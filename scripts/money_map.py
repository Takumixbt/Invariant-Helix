#!/usr/bin/env python3
"""Build a money-map model from Solidity analyzer observations (G3).

Accounting-first posture: most high-severity findings are a tracked total diverging
from reality. This module turns lexical delta-write facts into conservation-equation
*candidates* and unguarded-write gaps. Every row is an inference or hypothesis --
never a finding. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .inventory import load_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from inventory import load_scope
    from security_utils import atomic_write_text

DELTA = re.compile(r"^(\w+(?:\[[^\]]*\])*)\s*(\+=|-=)\s*(.+)$")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def build_money_map(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Derive assets, tracked totals, and conservation candidates from entrypoint facts."""
    assets: set[str] = set()
    equations: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []
    # var -> list of (function, op, expr, file, line)
    writes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    entrypoints: list[dict[str, Any]] = []

    for obs in observations:
        if not isinstance(obs, dict):
            continue
        props = obs.get("properties") if isinstance(obs.get("properties"), dict) else {}
        kind = obs.get("kind")
        if kind == "state":
            name = str(props.get("name") or "")
            if name:
                assets.add(name)
        if kind == "entrypoint":
            entrypoints.append(obs)
            fn = str(props.get("label") or obs.get("label") or "?")
            file_ = str(props.get("file") or "")
            line = props.get("line")
            for delta in props.get("delta_writes") or []:
                if not isinstance(delta, str):
                    continue
                match = DELTA.match(delta.strip())
                if not match:
                    continue
                var, op, expr = match.group(1), match.group(2), match.group(3).strip()
                base = var.split("[", 1)[0]
                assets.add(base)
                writes[base].append({
                    "function": fn, "op": op, "expr": expr[:120],
                    "file": file_, "line": line, "var": var,
                })

    # Pair +expr and -expr within the same function body as conservation candidates.
    for ep in entrypoints:
        props = ep.get("properties") if isinstance(ep.get("properties"), dict) else {}
        deltas = [d for d in (props.get("delta_writes") or []) if isinstance(d, str)]
        plus = []
        minus = []
        for delta in deltas:
            match = DELTA.match(delta.strip())
            if not match:
                continue
            var, op, expr = match.group(1), match.group(2), match.group(3).strip()
            base = var.split("[", 1)[0]
            item = {"var": base, "full": var, "expr": expr}
            if op == "+=":
                plus.append(item)
            elif op == "-=":
                minus.append(item)
        for p in plus:
            for m in minus:
                if p["expr"] == m["expr"] or p["expr"] in m["expr"] or m["expr"] in p["expr"]:
                    equations.append({
                        "kind": "conservation_candidate",
                        "equation": f"{p['var']} + {m['var']} ≈ const  (via {p['expr'][:60]})",
                        "function": props.get("label") or ep.get("label"),
                        "file": props.get("file"),
                        "line": props.get("line"),
                        "status": "inferred",
                        "lens": "invariant-state",
                        "note": "paired delta writes in one function; verify all write sites",
                    })

    # Unguarded shared-state write leads already in observations become money-map gaps.
    for obs in observations:
        if obs.get("kind") != "hypothesis":
            continue
        props = obs.get("properties") if isinstance(obs.get("properties"), dict) else {}
        bug = str(props.get("bug_class") or "")
        if bug in {
            "missing-access-control", "first-depositor-inflation", "msg-value-accounting",
            "precision-loss",
        }:
            gaps.append({
                "kind": "accounting_gap",
                "bug_class": bug,
                "label": obs.get("label"),
                "locators": obs.get("locators"),
                "lens": props.get("lens"),
                "status": "hypothesized",
            })

    return {
        "schema": "ih-money-map/v1",
        "assets": sorted(assets),
        "entrypoint_count": len(entrypoints),
        "write_sites": {k: v for k, v in sorted(writes.items())},
        "conservation_candidates": equations,
        "accounting_gaps": gaps,
        "status": "inferred",
        "note": "Money-map rows are model candidates, never findings. Prove on-chain.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", required=True, type=Path,
                        help="JSONL from ih-solidity-analyze")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--scope", type=Path, help="optional case manifest for case/snapshot ids")
    args = parser.parse_args(argv)
    try:
        observations = _load_jsonl(args.observations)
        model = build_money_map(observations)
        if args.scope:
            case = load_scope(args.scope)
            model["case_id"] = case.get("case_id")
            model["snapshot_id"] = case.get("snapshot_id")
        atomic_write_text(args.output, json.dumps(model, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"money-map error: {exc}", file=sys.stderr)
        return 2
    print(
        f"wrote {args.output}: {len(model['assets'])} asset(s), "
        f"{len(model['conservation_candidates'])} conservation candidate(s), "
        f"{len(model['accounting_gaps'])} accounting gap(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
