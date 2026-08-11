#!/usr/bin/env python3
"""Normalize real-world exploit / finding / CVE corpora into one queryable index.

The knowledge base grounds hypothesis generation (gate G5): instead of improvising,
Invariant Helix matches a target against history. This script parses heterogeneous
markdown (DeFi incident writeups, CVE-PoC records, researcher findings) into a single
normalized JSON index that ``kb_match`` queries.

Corpora are fetched on demand into a gitignored cache and are never vendored, so the
repository stays lean and license-clean. ``--no-fetch`` normalizes an existing
directory (used by tests and CI against a tiny committed fixture), while
``--findings-index`` merges the JSON emitted by the researcher-finding ingester.
Standard library only; ``git`` is invoked as a subprocess, never imported.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

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
KNOWN_SOURCE_REPOS = {
    "defi-incidents": "https://github.com/kismp123/DeFi-Security-Incident",
    "trickest-cve": "https://github.com/trickest/cve",
}
SOURCE_TYPES = {
    "defi-incidents": "defi-incident",
    "trickest-cve": "cve-poc-record",
    "incidents": "defi-incident",
    "cve": "cve-poc-record",
}
CWE = re.compile(r"CWE[-\s]?(\d{1,5})", re.IGNORECASE)
CVE_ID = re.compile(r"CVE-\d{4}-\d{3,7}", re.IGNORECASE)
LINK = re.compile(r"https?://[^\s)\]]+")
MONEY = re.compile(r"\$[\s]?\d[\d,]*(?:\.\d+)?\s?(?:k|m|b|million|billion|thousand)?", re.IGNORECASE)
SEVERITY = re.compile(r"\b(critical|high|medium|low|informational|info|qa|gas)\b", re.IGNORECASE)
DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
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


def normalize_severity(value: str | None) -> str | None:
    if not value:
        return None
    low = value.lower()
    if "critical" in low:
        return "critical"
    if "high" in low:
        return "high"
    if "medium" in low:
        return "medium"
    if "low" in low:
        return "low"
    if re.search(r"\binformational\b|\binfo\b", low):
        return "informational"
    if re.search(r"\bqa\b", low):
        return "qa"
    if re.search(r"\bgas\b", low):
        return "gas"
    return None


def git_revision(root: Path) -> str | None:
    """Return the checked-out corpus revision when the source is a git snapshot."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    revision = result.stdout.strip()
    return revision if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{7,64}", revision) else None


def source_url_for(root: Path, path: Path, source: str, revision: str | None) -> str | None:
    repo = KNOWN_SOURCE_REPOS.get(source)
    if not repo:
        return None
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError:
        relative = path.name
    ref = revision or "main"
    return f"{repo}/blob/{ref}/{quote(relative, safe='/')}"


def entry_type(source: str) -> str:
    return SOURCE_TYPES.get(source, "historical-record")


def normalize_file(path: Path, source: str, source_url: str | None = None, revision: str | None = None) -> dict[str, Any] | None:
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
    severity_match = SEVERITY.search(text)
    impact = first_section(parts, "impact", "consequence", "loss")
    attack_flow = first_section(parts, "attack flow", "exploit flow", "transaction flow", "steps")
    on_chain_source = first_section(parts, "on-chain source", "on chain source", "transaction source", "transaction hash")
    poc_detail = first_section(parts, "foundry poc", "proof of concept", "poc")
    remediation = first_section(parts, "remediation", "mitigation", "fix", "prevention")
    lessons = first_section(parts, "lessons", "lesson", "takeaway")
    if source_url is None and links:
        source_url = links[0]
    kind = entry_type(source)
    incident_date = DATE.search(path.stem)
    keyword_source = " ".join(
        [title, vuln_class, summary[:600], root_cause[:600], impact[:500], attack_flow[:500], poc_detail[:500], lessons[:500]]
    )
    references = [ref for ref in dict.fromkeys([source_url, *links]) if ref]
    entry = {
        "id": (cve_match.group(0).upper() if cve_match else f"{source}:{path.stem}"),
        "source": source,
        "entry_type": kind,
        "status": "historical-confirmed" if kind == "defi-incident" else "catalogued-record",
        "vuln_class": vuln_class,
        "cwe": f"CWE-{cwe.group(1)}" if cwe else None,
        "cve_id": cve_match.group(0).upper() if cve_match else None,
        "severity": normalize_severity(severity_match.group(1) if severity_match else None),
        "severity_label": severity_match.group(1).lower() if severity_match else None,
        "chains": detect_chains(text),
        "title": title.strip()[:200],
        "summary": " ".join(summary.split())[:500],
        "root_cause": " ".join(root_cause.split())[:500],
        "impact": " ".join(impact.split())[:1000],
        "attack_flow": " ".join(attack_flow.split())[:1500],
        "on_chain_source": " ".join(on_chain_source.split())[:1000],
        "poc_detail": " ".join(poc_detail.split())[:2000],
        "remediation": " ".join(remediation.split())[:1000],
        "lessons": " ".join(lessons.split())[:1000],
        "estimated_loss": money.group(0).strip() if money else None,
        "poc_refs": references[:12],
        "keywords": tokens(keyword_source)[:40],
        "path": str(path),
        "source_url": source_url,
        "incident_date": incident_date.group(1) if incident_date else None,
        "content_depth": "postmortem" if kind == "defi-incident" else "cve-record",
        "provenance": {
            "authority": "upstream-corpus",
            "source_url": source_url,
            "retrieval": "git-snapshot" if revision else "local-source",
            "revision": revision,
        },
    }
    return entry


def normalize_dir(root: Path, source: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    revision = git_revision(root)
    for path in sorted(root.rglob("*.md")):
        if path.name.lower() in {"readme.md", "contributing.md", "license.md", "code_of_conduct.md", "security.md"}:
            continue
        entry = normalize_file(path, source, source_url_for(root, path, source, revision), revision)
        if entry:
            entries.append(entry)
    return entries


def fetch(name: str, url: str, cache: Path) -> Path:
    destination = cache / name
    cache.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not (destination / ".git").exists():
            raise ValueError(f"cache path exists but is not a git repository: {destination}")
        subprocess.run(["git", "-C", str(destination), "pull", "--ff-only"], check=True, capture_output=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1", url, str(destination)], check=True, capture_output=True)
    return destination


def normalize_index_file(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """Load a source-aware index emitted by findings_ingest without trusting its count."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("entries"), list):
        raise ValueError(f"findings index must be an object with an entries list: {path}")
    names = [str(name) for name in raw.get("generated_from", []) if str(name).strip()]
    entries: list[dict[str, Any]] = []
    for value in raw["entries"]:
        if not isinstance(value, dict) or not value.get("id"):
            continue
        entry = dict(value)
        source = str(entry.get("source") or (names[0] if names else path.stem))
        entry["source"] = source
        entry.setdefault("entry_type", "researcher-finding")
        entry.setdefault("status", "published-finding")
        entry.setdefault("vuln_class", "unclassified")
        entry.setdefault("chains", [])
        entry.setdefault("poc_refs", [])
        entry.setdefault("keywords", [])
        entry.setdefault("provenance", {
            "authority": "local-derived-index",
            "source_url": entry.get("source_url"),
            "retrieval": "derived-index",
        })
        keywords = entry["keywords"] if isinstance(entry["keywords"], list) else []
        poc_refs = entry["poc_refs"] if isinstance(entry["poc_refs"], list) else []
        entry["keywords"] = [str(token) for token in keywords if str(token).strip()]
        entry["poc_refs"] = [str(ref) for ref in poc_refs if str(ref).strip()]
        entries.append(entry)
        if source not in names:
            names.append(source)
    return (names or [path.stem], entries)


def build_index(
    sources: list[tuple[str, Path]],
    finding_indexes: list[Path] | None = None,
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    source_names: list[str] = []
    for name, path in sources:
        source_names.append(name)
        entries.extend(normalize_dir(path, name))
    for path in finding_indexes or []:
        names, indexed_entries = normalize_index_file(path)
        source_names.extend(names)
        entries.extend(indexed_entries)
    entries.sort(key=lambda item: (item["source"], item["id"]))
    summary: dict[str, dict[str, Any]] = {}
    for entry in entries:
        source = str(entry.get("source", "unknown"))
        bucket = summary.setdefault(source, {"entry_count": 0, "entry_types": []})
        bucket["entry_count"] += 1
        kind = entry.get("entry_type")
        if kind and kind not in bucket["entry_types"]:
            bucket["entry_types"].append(kind)
    for bucket in summary.values():
        bucket["entry_types"].sort()
    return {
        "schema_version": "1.0",
        "generated_from": sorted(set(source_names)),
        "entry_count": len(entries),
        "source_summary": summary,
        "entries": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, action="append", default=[],
                        help="a local corpus directory to normalize (repeatable)")
    parser.add_argument("--fetch", action="store_true", help="git-clone the known corpora into the cache first")
    parser.add_argument("--fetch-source", choices=sorted(KNOWN_SOURCES), action="append", default=[],
                        help="with --fetch, refresh only this known corpus (repeatable; default: all)")
    parser.add_argument("--no-fetch", dest="fetch", action="store_false")
    parser.add_argument("--cache", type=Path, default=Path("knowledge/cache"))
    parser.add_argument("--index", type=Path, default=Path("knowledge/cache/index.json"))
    parser.add_argument("--findings-index", type=Path, action="append", default=[],
                        help="a JSON index emitted by ih-findings-ingest (repeatable)")
    parser.set_defaults(fetch=False)
    args = parser.parse_args(argv)
    try:
        sources: list[tuple[str, Path]] = []
        if args.fetch:
            fetch_names = args.fetch_source or list(KNOWN_SOURCES)
            for name in fetch_names:
                url = KNOWN_SOURCES[name]
                if url:
                    sources.append((name, fetch(name, url, args.cache)))
        for source in args.source:
            if not source.is_dir():
                raise ValueError(f"source directory not found: {source}")
            sources.append((source.name, source))
        for findings_index in args.findings_index:
            if not findings_index.is_file():
                raise ValueError(f"findings index not found: {findings_index}")
        if not sources and not args.findings_index:
            raise ValueError("no sources: pass --source DIR, --findings-index FILE, and/or --fetch")
        index = build_index(sources, args.findings_index)
        atomic_write_text(args.index, json.dumps(index, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"kb sync error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.index} ({index['entry_count']} entries from {', '.join(index['generated_from'])})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
