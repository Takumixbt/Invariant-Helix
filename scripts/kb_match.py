#!/usr/bin/env python3
"""Ground hypothesis generation by matching a target graph against the knowledge base.

Given a case/snapshot-scoped graph and the normalized index produced by ``kb_sync``,
this returns ranked historical patterns per surface. Each match is emitted as an
``inferred`` observation carrying its source reference, and as a G5 hypothesis family.

Discipline is preserved: a match is a *lead*, never a finding. The gate still decides
whether the pattern is reachable and impactful on this target. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


STOPWORDS = frozenset(
    "the a an and or of to in on for with by from at is are node edge case snapshot public "
    "internal observed inferred label kind value".split()
)


def graph_tokens(graph: dict[str, Any]) -> list[str]:
    """Extract a token bag from node kinds, labels, and shallow property strings."""
    bag: list[str] = []
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        bag.append(str(node.get("kind", "")))
        bag.append(str(node.get("label", "")))
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, value in properties.items():
                bag.append(str(key))
                if isinstance(value, (str, int, float)):
                    bag.append(str(value))
    for edge in graph.get("edges", []):
        if isinstance(edge, dict):
            bag.append(str(edge.get("relation", "")))
            bag.append(str(edge.get("locator", "")))
    tokens: list[str] = []
    for chunk in bag:
        for token in re.findall(r"[a-z0-9][a-z0-9\-]{2,}", chunk.lower()):
            if token not in STOPWORDS and not token.isdigit():
                tokens.append(token)
    return tokens


def score_entry(entry: dict[str, Any], target: set[str], chain: str | None) -> float:
    keywords = set(entry.get("keywords", []))
    if not keywords:
        return 0.0
    overlap = keywords & target
    score = float(len(overlap))
    # A vuln_class token appearing in the target is a stronger signal.
    for word in str(entry.get("vuln_class", "")).split():
        if word in target:
            score += 1.5
    if chain and chain.lower() in {c.lower() for c in entry.get("chains", [])}:
        score += 1.0
    # Normalize slightly by entry breadth so a huge keyword list cannot dominate.
    return round(score / (1 + len(keywords) / 40.0), 3)


def match(
    graph: dict[str, Any],
    index: dict[str, Any],
    *,
    chain: str | None = None,
    top: int = 10,
    min_score: float = 1.0,
) -> list[dict[str, Any]]:
    target = set(graph_tokens(graph))
    scored: list[dict[str, Any]] = []
    for entry in index.get("entries", []):
        if not isinstance(entry, dict):
            continue
        value = score_entry(entry, target, chain)
        if value < min_score:
            continue
        overlap = sorted(set(entry.get("keywords", [])) & target)
        scored.append(
            {
                "kb_id": entry.get("id"),
                "source": entry.get("source"),
                "entry_type": entry.get("entry_type"),
                "vuln_class": entry.get("vuln_class"),
                "lenses": entry.get("lenses", []),
                "cwe": entry.get("cwe"),
                "severity": entry.get("severity"),
                "score": value,
                "matched_keywords": overlap,
                "title": entry.get("title"),
                "source_url": entry.get("source_url"),
                "report_url": entry.get("report_url"),
                "provenance": entry.get("provenance"),
                "poc_refs": entry.get("poc_refs", []),
                "lead_only": True,
            }
        )
    scored.sort(key=lambda item: (-item["score"], str(item["kb_id"])))
    return scored[:top]


def as_observations(matches: list[dict[str, Any]], case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    """Render matches as inferred observations for the graph. Never 'observed'."""
    observations: list[dict[str, Any]] = []
    for rank, item in enumerate(matches):
        observations.append(
            {
                "id": f"pattern:{re.sub(r'[^a-z0-9]+', '-', str(item['kb_id']).lower()).strip('-')[:96]}",
                "case_id": case_id,
                "snapshot_id": snapshot_id,
                "kind": "pattern",
                "label": str(item.get("title") or item.get("kb_id"))[:120],
                "status": "inferred",
                "sensitivity": "public",
                "confidence": {"level": "low", "reason": "knowledge-base keyword match; lead only, not a finding"},
                "properties": {
                    "vuln_class": item.get("vuln_class"),
                    "lenses": item.get("lenses", []),
                    "cwe": item.get("cwe"),
                    "severity": item.get("severity"),
                    "source_url": item.get("source_url"),
                    "entry_type": item.get("entry_type"),
                    "score": item.get("score"),
                    "rank": rank,
                },
                "locators": [f"kb:{item.get('source')}:{item.get('kb_id')}"],
                "evidence_refs": [item.get("source_url")] if item.get("source_url") else (
                    [ref for ref in item.get("poc_refs", [])[:1]] or ["kb:reference-pending"]
                ),
            }
        )
    return observations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--chain", help="chain family hint to boost same-family history")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--min-score", type=float, default=1.0)
    parser.add_argument("--emit-observations", type=Path, help="write inferred observations JSONL here")
    args = parser.parse_args(argv)
    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        index = json.loads(args.index.read_text(encoding="utf-8"))
        if not isinstance(graph, dict) or not isinstance(index, dict):
            raise ValueError("graph and index must both be JSON objects")
        matches = match(graph, index, chain=args.chain, top=args.top, min_score=args.min_score)
        if args.emit_observations:
            observations = as_observations(
                matches, str(graph.get("case_id", "unbound-case")), str(graph.get("snapshot_id", "unbound-snapshot"))
            )
            atomic_write_text(
                args.emit_observations,
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in observations),
            )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"kb match error: {exc}", file=sys.stderr)
        return 2
    for item in matches:
        keys = ", ".join(item["matched_keywords"][:6])
        print(f"  {item['score']:>5}  {item['vuln_class']:<24} {item['kb_id']}  [{keys}]")
    print(f"\n{len(matches)} lead(s); every match is a hypothesis, not a finding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
