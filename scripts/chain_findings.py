#!/usr/bin/env python3
"""Propose kill chains from findings that already passed their gates.

Composes releasable findings whose affected components are connected in the graph into
A->B chain candidates. It NEVER invents an edge: a chain is proposed only when a graph
edge already links the two findings' components. Output is a planning aid; each proposed
chain still becomes a finding whose ``chain_of`` parents must be releasable. Standard
library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


RELEASABLE = {"verified", "downgraded", "released"}


def load_findings(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("findings")
    if not isinstance(value, list):
        raise ValueError("findings must be an array or an object with a findings array")
    return [item for item in value if isinstance(item, dict)]


def adjacency(graph: dict[str, Any]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        a, b = edge.get("from"), edge.get("to")
        if isinstance(a, str) and isinstance(b, str):
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
    return adj


def _connected(a_components: set[str], b_components: set[str], adj: dict[str, set[str]]) -> bool:
    if a_components & b_components:
        return True  # share a node
    for node in a_components:
        if adj.get(node, set()) & b_components:
            return True  # a graph edge already links them
    return False


def build_chains(findings: list[dict[str, Any]], graph: dict[str, Any]) -> list[dict[str, Any]]:
    adj = adjacency(graph)
    releasable = [f for f in findings if str(f.get("status", "")).lower() in RELEASABLE]
    chains: list[dict[str, Any]] = []
    for a, b in combinations(releasable, 2):
        a_components = set(a.get("affected_components", []))
        b_components = set(b.get("affected_components", []))
        if not a_components or not b_components:
            continue
        if _connected(a_components, b_components, adj):
            members = sorted([str(a.get("finding_id")), str(b.get("finding_id"))])
            chains.append({
                "chain_id": "chain:" + "+".join(members),
                "members": members,
                "shared_or_linked_components": sorted(
                    (a_components & b_components)
                    or {n for n in a_components if adj.get(n, set()) & b_components}
                ),
                "note": "chain_of parents must each be releasable; no edge was invented",
            })
    chains.sort(key=lambda item: item["chain_id"])
    return chains


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings", type=Path)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        findings = load_findings(args.findings)
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        chains = build_chains(findings, graph)
        if args.output:
            atomic_write_text(args.output, json.dumps({"chains": chains}, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"chain builder error: {exc}", file=sys.stderr)
        return 2
    for chain in chains:
        print(f"  {chain['chain_id']}  via {', '.join(chain['shared_or_linked_components'])}")
    print(f"\n{len(chains)} chain candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
