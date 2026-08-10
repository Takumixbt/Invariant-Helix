#!/usr/bin/env python3
"""Plan which attacker lenses to run against a target graph, and who verifies each.

This is the aggression engine's scheduler. It selects only the lenses justified by
node kinds actually present in the graph (Invariant Helix's "no fixed roster" rule),
binds each lens to an available capability, and assigns an owner plus an *independent*
verifier at plan time — so discoverer != verifier cannot be violated downstream. A
lens whose capability is unavailable, or that cannot be given an independent verifier,
is planned as blocked rather than silently attempted. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .check_capabilities import probe
    from .inventory import load_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from check_capabilities import probe
    from inventory import load_scope
    from security_utils import atomic_write_text


# lens id -> (domain, capability, trigger node kinds). A lens is a candidate when the
# graph contains any of its trigger kinds. Ported from pashov (contract) and
# bountyforge (web/recon) attacker profiles, kept chain-neutral.
LENSES: dict[str, dict[str, Any]] = {
    "access-control": {"domain": "contract", "capability": "source_analysis",
                       "triggers": ["contract", "program", "entrypoint", "authority", "role", "capability"]},
    "math-precision": {"domain": "contract", "capability": "source_analysis",
                       "triggers": ["state", "storage", "invariant", "contract"]},
    "economic": {"domain": "contract", "capability": "source_analysis",
                 "triggers": ["oracle", "external_dependency", "state", "account"]},
    "execution-trace": {"domain": "contract", "capability": "execution_trace",
                        "triggers": ["entrypoint", "instruction", "message", "contract"]},
    "invariant-state": {"domain": "contract", "capability": "source_analysis",
                        "triggers": ["state", "storage", "invariant"]},
    "periphery-integration": {"domain": "contract", "capability": "source_analysis",
                              "triggers": ["external_dependency", "module", "contract"]},
    "first-principles": {"domain": "contract", "capability": "source_analysis",
                         "triggers": ["contract", "program", "module", "entrypoint"]},
    "asymmetry": {"domain": "contract", "capability": "source_analysis",
                  "triggers": ["entrypoint", "state", "instruction"]},
    "boundary": {"domain": "contract", "capability": "source_analysis",
                 "triggers": ["state", "parameter", "storage"]},
    "numerical-gap": {"domain": "contract", "capability": "source_analysis",
                      "triggers": ["state", "oracle", "storage"]},
    "trust-gap": {"domain": "contract", "capability": "source_analysis",
                  "triggers": ["oracle", "external_dependency", "authority", "message"]},
    "flow-gap": {"domain": "contract", "capability": "source_analysis",
                 "triggers": ["state", "authority", "message", "account"]},
    # Accounting-first lenses: value modelling rather than code-pattern matching.
    "share-exchange-rate": {"domain": "contract", "capability": "source_analysis",
                            "triggers": ["state", "storage", "contract", "account"]},
    "temporal-cohort": {"domain": "contract", "capability": "source_analysis",
                        "triggers": ["state", "identity", "actor", "storage"]},
    "liquidation-solvency": {"domain": "contract", "capability": "source_analysis",
                             "triggers": ["oracle", "state", "account", "external_dependency"]},
    "cross-chain-state": {"domain": "contract", "capability": "source_analysis",
                          "triggers": ["message", "boundary", "external_dependency", "receipt"]},
    "zk-circuit": {"domain": "circuit", "capability": "source_analysis",
                   "triggers": ["circuit", "constraint", "witness", "module"]},
    "web-api": {"domain": "web", "capability": "http_crawl",
                "triggers": ["route", "endpoint", "parameter", "request"]},
    "auth-session": {"domain": "web", "capability": "request_replay",
                     "triggers": ["identity", "role", "tenant", "cookie", "token_redacted", "workflow"]},
    "recon-infra": {"domain": "infra", "capability": "surface_inventory",
                    "triggers": ["host", "service", "origin", "asset"]},
    "credential-leak": {"domain": "infra", "capability": "source_analysis",
                        "triggers": ["token_redacted", "cookie", "script", "component"]},
    "race-condition": {"domain": "web", "capability": "synchronized_requests",
                       "triggers": ["route", "endpoint", "entrypoint"]},
}
DEFAULT_ACTORS = ["auditor-a", "auditor-b", "auditor-c"]


def graph_kinds(graph: dict[str, Any]) -> set[str]:
    return {
        str(node.get("kind"))
        for node in graph.get("nodes", [])
        if isinstance(node, dict) and node.get("kind")
    }


def plan(
    graph: dict[str, Any],
    *,
    actors: list[str] | None = None,
    capability_report: dict[str, Any] | None = None,
    allowed_capabilities: list[str] | None = None,
) -> dict[str, Any]:
    actors = actors or DEFAULT_ACTORS
    report = capability_report or probe()
    kinds = graph_kinds(graph)
    case_id = str(graph.get("case_id", "unbound-case"))
    snapshot_id = str(graph.get("snapshot_id", "unbound-snapshot"))
    entries: list[dict[str, Any]] = []
    index = 0
    for lens, spec in LENSES.items():
        present = sorted(kinds & set(spec["triggers"]))
        if not present:
            continue  # not justified by the graph; do not spawn to fill a roster
        capability = spec["capability"]
        cap_ok = report.get(capability, {}).get("available", False)
        allow_ok = allowed_capabilities is None or capability in allowed_capabilities
        # Independent-verifier assignment: owner and verifier must be distinct actors.
        if len(actors) >= 2:
            owner = actors[index % len(actors)]
            verifier = actors[(index + 1) % len(actors)]
        else:
            owner = actors[0] if actors else "auditor-a"
            verifier = None
        blockers: list[str] = []
        if not cap_ok:
            candidates = ", ".join(report.get(capability, {}).get("candidate_tools", [])) or "an external harness"
            blockers.append(f"capability {capability} unavailable; install one of: {candidates}")
        if not allow_ok:
            blockers.append(f"capability {capability} not admitted by the case manifest")
        if verifier is None or verifier == owner:
            blockers.append("cannot assign an independent verifier: need at least two distinct actors")
        entries.append(
            {
                "lens": lens,
                "domain": spec["domain"],
                "capability": capability,
                "capability_available": cap_ok,
                "trigger_kinds_present": present,
                "owner": owner,
                "verifier": verifier,
                "status": "planned" if not blockers else "blocked",
                "blockers": blockers,
                "bundle_ref": f"bundle:{lens}",
            }
        )
        index += 1
    planned = [entry for entry in entries if entry["status"] == "planned"]
    blocked = [entry for entry in entries if entry["status"] == "blocked"]
    return {
        "schema_version": "1.0",
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "graph_node_kinds": sorted(kinds),
        "actors": actors,
        "planned_count": len(planned),
        "blocked_count": len(blocked),
        "lenses": entries,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--case-manifest", type=Path)
    parser.add_argument("--coverage", type=Path, help="reserved: coverage bundle for target prioritization")
    parser.add_argument("--actor", action="append", dest="actors", default=[],
                        help="an actor that can discover or verify (repeatable; >=2 for independence)")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        if not isinstance(graph, dict):
            raise ValueError("graph must be a JSON object")
        allowed = None
        if args.case_manifest:
            case = load_scope(args.case_manifest)
            allowed = case.get("allowed_capabilities")
            if isinstance(allowed, list):
                allowed = [str(item) for item in allowed]
        result = plan(graph, actors=args.actors or None, allowed_capabilities=allowed)
        if args.output:
            atomic_write_text(args.output, json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"lens dispatch error: {exc}", file=sys.stderr)
        return 2
    for entry in result["lenses"]:
        mark = "plan" if entry["status"] == "planned" else "BLOCK"
        note = "" if entry["status"] == "planned" else f"  <- {entry['blockers'][0]}"
        print(f"  [{mark}] {entry['lens']:<22} {entry['domain']:<9} own={entry['owner']} vfy={entry['verifier']}{note}")
    print(f"\n{result['planned_count']} planned, {result['blocked_count']} blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
