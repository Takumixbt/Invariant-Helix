#!/usr/bin/env python3
"""Ingest researcher finding writeups (HTML or markdown) into the knowledge base.

Public audit findings -- 0xsimao's index, Solodit exports, contest reports, a firm's
published PDFs converted to text -- are the highest-signal corpus available, because
each entry is a *confirmed* bug with a root cause a human wrote down. This turns a
directory or a saved page of them into knowledge-base entries that ``kb_match`` can
query, so hypothesis generation is grounded in what real auditors actually found.

Sites like 0xsimao.com are often unreachable from an audit host (egress policy), so
this reads from a LOCAL path you fetched yourself:

    # on a machine with network access
    wget -r -l2 -k -p https://0xsimao.com/findings -P ./simao
    ih-findings-ingest ./simao --source 0xsimao --output entries.json
    ih-kb-sync --source ./simao --index knowledge/cache/index.json

HTML is parsed with the standard library's HTMLParser -- no external dependency, and
scripts/styles are discarded rather than executed. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text

SLUG = re.compile(r"[^a-z0-9]+")
WHITESPACE = re.compile(r"\s+")
CWE = re.compile(r"CWE[-\s]?(\d{1,5})", re.IGNORECASE)
SEVERITY = re.compile(r"\b(critical|high|medium|low|informational|info|qa|gas)\b", re.IGNORECASE)
# Bug-class vocabulary seen across public audit findings, mapped to the IH lens that owns it.
BUG_CLASS_LENS = {
    "reentrancy": "execution-trace",
    "read-only reentrancy": "execution-trace",
    "access control": "access-control",
    "missing access control": "access-control",
    "unprotected initializer": "access-control",
    "privilege escalation": "access-control",
    "rounding": "math-precision",
    "precision loss": "math-precision",
    "division before multiplication": "math-precision",
    "overflow": "math-precision",
    "underflow": "math-precision",
    "decimals": "math-precision",
    "first depositor": "math-precision",
    "share inflation": "math-precision",
    "oracle manipulation": "economic",
    "price manipulation": "economic",
    "flash loan": "economic",
    "sandwich": "economic",
    "front-run": "race-condition",
    "frontrun": "race-condition",
    "mev": "economic",
    "liquidation": "economic",
    "slippage": "economic",
    "invariant": "invariant-state",
    "accounting": "invariant-state",
    "insolvency": "invariant-state",
    "state desync": "invariant-state",
    "dos": "boundary",
    "denial of service": "boundary",
    "unbounded loop": "boundary",
    "griefing": "boundary",
    "edge case": "boundary",
    "signature replay": "trust-gap",
    "replay": "trust-gap",
    "domain separator": "trust-gap",
    "stale price": "trust-gap",
    "trust": "trust-gap",
    "callback": "periphery-integration",
    "hook": "periphery-integration",
    "integration": "periphery-integration",
    "fee-on-transfer": "periphery-integration",
    "rebasing": "periphery-integration",
    "idor": "web-api",
    "ssrf": "web-api",
    "xss": "web-api",
    "injection": "web-api",
    "authorization": "auth-session",
    "authentication": "auth-session",
    "session": "auth-session",
}
STOPWORDS = frozenset(
    "the a an and or of to in on for with by from at is are was were be been this that as "
    "it its into via can could may will not no if then than when where which who how what "
    "we they you i finding issue report audit severity impact recommendation mitigation".split()
)


class TextExtractor(HTMLParser):
    """Collect visible text and headings; discard script/style/nav chrome."""

    SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.headings: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0
        self._heading: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading = ""
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value and value.startswith(("http://", "https://")):
                    self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"h1", "h2", "h3", "h4"} and self._heading is not None:
            text = WHITESPACE.sub(" ", self._heading).strip()
            if text:
                self.headings.append(text)
            self._heading = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)
        if self._heading is not None:
            self._heading += data

    @property
    def text(self) -> str:
        return WHITESPACE.sub(" ", " ".join(self.parts)).strip()


def slug(text: str) -> str:
    return SLUG.sub("-", text.lower()).strip("-")[:100] or "entry"


def classify(text: str) -> list[tuple[str, str]]:
    """Return [(bug_class, lens)] for every vocabulary term present in the writeup."""
    low = text.lower()
    hits = [(name, lens) for name, lens in BUG_CLASS_LENS.items() if name in low]
    # Prefer the most specific match when several overlap (e.g. "reentrancy" vs
    # "read-only reentrancy") by sorting longest-first and de-duplicating by lens.
    hits.sort(key=lambda item: -len(item[0]))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for name, lens in hits:
        if lens in seen:
            continue
        seen.add(lens)
        unique.append((name, lens))
    return unique


def keywords(text: str, limit: int = 40) -> list[str]:
    found: list[str] = []
    for token in re.findall(r"[a-z][a-z0-9\-]{2,}", text.lower()):
        if token in STOPWORDS or token in found:
            continue
        found.append(token)
        if len(found) >= limit:
            break
    return found


def parse_document(path: Path, source: str) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not raw.strip():
        return None
    if path.suffix.lower() in {".html", ".htm"}:
        parser = TextExtractor()
        try:
            parser.feed(raw)
        except Exception:  # noqa: BLE001 - malformed HTML must not abort a corpus run
            return None
        text = parser.text
        title = parser.headings[0] if parser.headings else path.stem
        links = parser.links[:8]
    else:
        text = WHITESPACE.sub(" ", re.sub(r"[#*`>]", " ", raw)).strip()
        heading = re.search(r"^#{1,3}\s+(.+)$", raw, re.M)
        title = heading.group(1).strip() if heading else path.stem
        links = re.findall(r"https?://[^\s)\]]+", raw)[:8]
    if len(text) < 80:
        return None  # index pages / nav stubs carry no finding content
    classes = classify(text)
    severity = SEVERITY.search(text)
    cwe = CWE.search(text)
    return {
        "id": f"{source}:{slug(title)}",
        "source": source,
        "entry_type": "researcher-finding",
        "title": WHITESPACE.sub(" ", title).strip()[:200],
        "vuln_class": classes[0][0] if classes else "unclassified",
        "all_classes": [name for name, _ in classes],
        "lenses": [lens for _, lens in classes],
        "severity": severity.group(1).lower() if severity else None,
        "cwe": f"CWE-{cwe.group(1)}" if cwe else None,
        "summary": text[:500],
        "root_cause": text[:500],
        "chains": [],
        "poc_refs": links,
        "keywords": keywords(text),
        "path": str(path),
    }


def ingest(root: Path, source: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".html", ".htm", ".md", ".txt"}:
            continue
        entry = parse_document(path, source)
        if entry and entry["id"] not in seen:
            seen.add(entry["id"])
            entries.append(entry)
    entries.sort(key=lambda item: item["id"])
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path, help="local directory of saved finding writeups")
    parser.add_argument("--source", default="researcher-findings", help="corpus label, e.g. 0xsimao")
    parser.add_argument("--output", required=True, type=Path, help="knowledge-base index JSON")
    args = parser.parse_args(argv)
    try:
        if not args.root.is_dir():
            raise ValueError(f"directory not found: {args.root}")
        entries = ingest(args.root, args.source)
        index = {
            "schema_version": "1.0",
            "generated_from": [args.source],
            "entry_count": len(entries),
            "entries": entries,
        }
        atomic_write_text(args.output, json.dumps(index, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"findings ingest error: {exc}", file=sys.stderr)
        return 2
    by_lens: dict[str, int] = {}
    for entry in entries:
        for lens in entry["lenses"] or ["unrouted"]:
            by_lens[lens] = by_lens.get(lens, 0) + 1
    for lens, count in sorted(by_lens.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:>3}  {lens}")
    print(f"\nwrote {args.output} ({len(entries)} finding(s) from {args.source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
