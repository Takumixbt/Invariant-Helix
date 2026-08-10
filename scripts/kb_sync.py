#!/usr/bin/env python3
"""Normalize real-world exploit / finding / CVE corpora into one queryable index.

The knowledge base grounds hypothesis generation (gate G5): instead of improvising,
Invariant Helix matches a target against history. This script parses heterogeneous
markdown (DeFi incident writeups, CVE-PoC records, researcher findings) into a single
normalized JSON index that ``kb_match`` queries.

Corpora are fetched on demand into a gitignored cache and are never vendored, so the
repository stays lean and license-clean. ``--no-fetch`` normalizes an existing
directory (used by tests and CI against a tiny committed fixture). Standard library
only; ``git`` is invoked as a subprocess, never imported.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


# Public corpora. Cloned into the gitignored cache only when --fetch is requested.
KNOWN_SOURCES = {
    "defi-incidents": "https://github.com/kismp123/DeFi-Security-Incident.git",
    "trickest-cve": "https://github.com/trickest/cve.git",
    # 0xsimao findings are fetched on the operator's machine (egress-restricted here)
    # and pointed at with --source; there is no clone URL for the static site.
}
CWE = re.compile(r"CWE[-\s]?(\d{1,5})", re.IGNORECASE)
CVE_ID = re.compile(r"CVE-\d{4}-\d{3,7}", re.IGNORECASE)
LINK = re.compile(r"https?://[^\s)\]]+")
MONEY = re.compile(r"\$[\s]?\d[\d,]*(?:\.\d+)?\s?(?:k|m|b|million|billion|thousand)?", re.IGNORECASE)
CHAINS = (
    "ethereum", "evm", "solana", "aptos", "sui", "move", "cosmwasm", "cosmos", "near",
    "starknet", "cairo", "polkadot", "substrate", "ton", "tron", "cardano", "arbitrum",
    "optimism", "polygon", "bsc", "base", "avalanche",
)
STOPWORDS = frozenset(
    "the a an and or of to in on for with by from at is are was were be been being this that "
    "as it its into via can could may will vuln vulnerability attack exploit contract protocol "
    "code function value user users when where which who how what".split()
)


def sections(text: str) -> dict[str, str]:
    """Split markdown into {lowercased-heading: body} plus a synthetic 'preamble'."""
    result: dict[str, list[str]] = {"preamble": []}
    current = "preamble"
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.*)$", line)
        if heading:
            current = heading.group(1).strip().lower()
            result.setdefault(current, [])
        else:
            result.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in result.items()}


def first_section(parts: dict[str, str], *names: str) -> str:
    for name in names:
        for heading, body in parts.items():
            if name in heading and body:
                return body
    return ""


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", text.lower())
    seen: list[str] = []
    for token in raw:
        if token in STOPWORDS or token.isdigit():
            continue
        if token not in seen:
            seen.append(token)
    return seen


def infer_vuln_class(path: Path, text: str) -> str:
    # Filename convention YYYY-MM-DD_<Protocol>_<VulnType>.md, or a vulns/<class>.md file.
    stem = path.stem
    parts = stem.split("_")
    if len(parts) >= 3 and re.match(r"\d{4}-\d{2}-\d{2}", parts[0]):
        return parts[-1].replace("-", " ").strip().lower()
    if "vuln" in {p.name.lower() for p in path.parents}:
        return stem.replace("-", " ").strip().lower()
    labelled = re.search(r"(?im)^\s*(?:vuln(?:erability)?\s*(?:type|class|category)?)\s*[:\-]\s*(.+)$", text)
    if labelled:
        return labelled.group(1).strip().lower()
    return "unclassified"


def detect_chains(text: str) -> list[str]:
    low = text.lower()
    return [chain for chain in CHAINS if chain in low]


def normalize_file(path: Path, source: str) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not text.strip():
        return None
    parts = sections(text)
    cve_match = CVE_ID.search(text) or CVE_ID.search(path.stem)
    title = first_section(parts, "title") or path.stem.replace("_", " ").replace("-", " ")
    summary = first_section(parts, "summary", "overview", "description") or parts.get("preamble", "")
    root_cause = first_section(parts, "root cause", "vulnerability", "cause", "analysis")
    cwe = CWE.search(text)
    links = LINK.findall(text)
    money = MONEY.search(text)
    vuln_class = infer_vuln_class(path, text)
    keyword_source = " ".join([title, vuln_class, summary[:600], root_cause[:600]])
    entry = {
        "id": (cve_match.group(0).upper() if cve_match else f"{source}:{path.stem}"),
        "source": source,
        "vuln_class": vuln_class,
        "cwe": f"CWE-{cwe.group(1)}" if cwe else None,
        "cve_id": cve_match.group(0).upper() if cve_match else None,
        "chains": detect_chains(text),
        "title": title.strip()[:200],
        "summary": " ".join(summary.split())[:500],
        "root_cause": " ".join(root_cause.split())[:500],
        "estimated_loss": money.group(0).strip() if money else None,
        "poc_refs": links[:8],
        "keywords": tokens(keyword_source)[:40],
        "path": str(path),
    }
    return entry


def normalize_dir(root: Path, source: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        if path.name.lower() in {"readme.md", "contributing.md", "license.md", "code_of_conduct.md", "security.md"}:
            continue
        entry = normalize_file(path, source)
        if entry:
            entries.append(entry)
    return entries


def fetch(name: str, url: str, cache: Path) -> Path:
    destination = cache / name
    cache.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        subprocess.run(["git", "-C", str(destination), "pull", "--ff-only"], check=False, capture_output=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1", url, str(destination)], check=True, capture_output=True)
    return destination


def build_index(sources: list[tuple[str, Path]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for name, path in sources:
        entries.extend(normalize_dir(path, name))
    entries.sort(key=lambda item: (item["source"], item["id"]))
    return {
        "schema_version": "1.0",
        "generated_from": sorted({name for name, _ in sources}),
        "entry_count": len(entries),
        "entries": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", default=[],
                        help="a local corpus directory to normalize (repeatable)")
    parser.add_argument("--fetch", action="store_true", help="git-clone the known corpora into the cache first")
    parser.add_argument("--no-fetch", dest="fetch", action="store_false")
    parser.add_argument("--cache", type=Path, default=Path("knowledge/cache"))
    parser.add_argument("--index", type=Path, default=Path("knowledge/cache/index.json"))
    parser.set_defaults(fetch=False)
    args = parser.parse_args(argv)
    try:
        sources: list[tuple[str, Path]] = []
        if args.fetch:
            for name, url in KNOWN_SOURCES.items():
                if url:
                    sources.append((name, fetch(name, url, args.cache)))
        for source in args.source:
            if not source.is_dir():
                raise ValueError(f"source directory not found: {source}")
            sources.append((source.name, source))
        if not sources:
            raise ValueError("no sources: pass --source DIR and/or --fetch")
        index = build_index(sources)
        atomic_write_text(args.index, json.dumps(index, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"kb sync error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.index} ({index['entry_count']} entries from {', '.join(index['generated_from'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
