#!/usr/bin/env python3
"""One-command local audit orchestration for Solidity trees (Windows-native friendly).

Runs the fail-closed pipeline that actually produces work products for lenses:

  1. validate / synthesize a case manifest
  2. capability probe (missing tools -> coverage debt, never silent pass)
  3. solidity analyze -> facts + leads
  4. money map from those observations
  5. normalize leads into a graph, lens dispatch with pre-seeded leads
  6. build hashed-ready lens bundles

This does **not** invent findings or mark anything verified. It prepares the case so
an agent swarm (or a human) runs under G5-G8 with located leads. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .build_lens_bundle import build as build_bundles
    from .check_capabilities import blocked_coverage_items, probe
    from .lens_dispatch import plan as dispatch_plan
    from .money_map import build_money_map
    from .normalize_observations import normalize
    from .security_utils import atomic_write_text
    from .slither_ingest import ingest as ingest_slither
    from .solidity_analyze import analyze_tree
except ImportError:  # direct script execution
    from build_lens_bundle import build as build_bundles
    from check_capabilities import blocked_coverage_items, probe
    from lens_dispatch import plan as dispatch_plan
    from money_map import build_money_map
    from normalize_observations import normalize
    from security_utils import atomic_write_text
    from slither_ingest import ingest as ingest_slither
    from solidity_analyze import analyze_tree


def _default_case(root: Path, case_id: str, snapshot_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "authorization": {
            "granted_by": "local-operator",
            "granted_at": now,
            "expires_at": "2099-01-01T00:00:00Z",
            "scope_statement": f"Local development audit of {root.resolve()}",
            "rules_of_engagement": "local-static-and-fork-only; no production interaction",
        },
        "targets": [{"kind": "repository", "locator": str(root.resolve()), "label": root.name}],
        "exclusions": [],
        "identities": [{"id": "auditor-a", "role": "discoverer"},
                       {"id": "auditor-b", "role": "verifier"}],
        "allowed_capabilities": [
            "source_analysis", "chain_simulation", "execution_trace", "property_fuzzing",
            "evidence_manifest",
        ],
        "impact_limits": {"production": False, "real_funds": False, "notes": "local-dev-scope"},
        "stop_conditions": ["authorization expiry", "unexpected state change"],
        "data_handling": "local only",
        "emergency_contact": "local-operator",
    }


def _try_slither(root: Path, out: Path, case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    """Run slither if on PATH; return hypothesized leads or [] if unavailable/failed."""
    if not shutil.which("slither"):
        return []
    json_path = out / "slither.json"
    try:
        proc = subprocess.run(
            ["slither", str(root), "--json", str(json_path)],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if not json_path.is_file():
        # slither may write even with non-zero exit (findings found)
        return []
    try:
        leads = ingest_slither(json_path, case_id, snapshot_id)
        atomic_write_text(
            out / "slither-leads.jsonl",
            "".join(json.dumps(r, sort_keys=True) + "\n" for r in leads),
        )
        if proc.returncode not in (0, 255, 1):  # 1/255 often mean findings
            pass
        return leads
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return []


def run_audit(
    root: Path,
    out: Path,
    *,
    case_path: Path | None = None,
    actors: list[str] | None = None,
    local_dev: bool = False,
    run_slither: bool = True,
) -> int:
    root = root.resolve()
    if not root.is_dir():
        print(f"audit error: root not found: {root}", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)

    if case_path:
        case = json.loads(case_path.read_text(encoding="utf-8"))
    else:
        if not local_dev:
            print(
                "audit error: pass --case MANIFEST.json, or --local-dev-scope to synthesize "
                "a non-production local case (explicit, never silent)",
                file=sys.stderr,
            )
            return 2
        case = _default_case(root, f"local-{root.name}", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        print("WARNING: --local-dev-scope synthesized a case. No URL/repo implies production auth.")

    case_id = str(case.get("case_id", "unbound-case"))
    snapshot_id = str(case.get("snapshot_id", "unbound-snapshot"))
    case_out = out / "case.json"
    atomic_write_text(case_out, json.dumps(case, indent=2, sort_keys=True) + "\n")

    caps = probe()
    atomic_write_text(out / "capabilities.json", json.dumps(caps, indent=2, sort_keys=True) + "\n")
    blocked = blocked_coverage_items(
        caps, case_id=case_id, snapshot_id=snapshot_id, language="solidity",
    )
    if blocked:
        atomic_write_text(out / "blocked-coverage.json", json.dumps(blocked, indent=2) + "\n")

    facts, leads = analyze_tree(root, case_id, snapshot_id)
    slither_leads: list[dict[str, Any]] = []
    if run_slither:
        slither_leads = _try_slither(root, out, case_id, snapshot_id)
        leads = leads + slither_leads
    observations = facts + leads
    obs_path = out / "observations.jsonl"
    atomic_write_text(obs_path, "".join(json.dumps(r, sort_keys=True) + "\n" for r in observations))

    money = build_money_map(observations)
    money["case_id"], money["snapshot_id"] = case_id, snapshot_id
    atomic_write_text(out / "money-map.json", json.dumps(money, indent=2, sort_keys=True) + "\n")

    # Graph from observations JSONL (normalize reads a path, not in-memory rows).
    graph = normalize(obs_path)
    if isinstance(graph, dict):
        graph.setdefault("case_id", case_id)
        graph.setdefault("snapshot_id", snapshot_id)
    atomic_write_text(out / "graph.json", json.dumps(graph, indent=2, sort_keys=True) + "\n")

    actors = actors or ["auditor-a", "auditor-b"]
    plan = dispatch_plan(graph, actors=actors, capability_report=caps, seed_leads=leads)
    atomic_write_text(out / "dispatch.json", json.dumps(plan, indent=2, sort_keys=True) + "\n")

    lens_dir = Path(__file__).resolve().parents[1] / "references" / "lenses"
    bundles = build_bundles(plan, lens_dir)
    bundle_dir = out / "bundles"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    for name, content in bundles:
        atomic_write_text(bundle_dir / name, content)

    summary = {
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "root": str(root),
        "facts": len(facts),
        "leads": len(leads),
        "slither_leads": len(slither_leads),
        "lenses_planned": sum(1 for e in plan.get("lenses", []) if e.get("status") == "planned"),
        "lenses_blocked": sum(1 for e in plan.get("lenses", []) if e.get("status") == "blocked"),
        "conservation_candidates": len(money.get("conservation_candidates", [])),
        "accounting_gaps": len(money.get("accounting_gaps", [])),
        "blocked_capabilities": len(blocked),
        "next": [
            f"ih-evidence {bundle_dir} --case-id {case_id} --snapshot-id {snapshot_id} "
            f"--producer lens-bundler --output {out / 'bundle-manifest.json'}",
            "Run lens agents on bundles/; discoverer != verifier",
            "ih-validate-findings + ih-evaluate-case --release when evidence is ready",
        ],
    }
    atomic_write_text(out / "summary.json", json.dumps(summary, indent=2, sort_keys=True) + "\n")

    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"\naudit workdir: {out}")
    print("No findings were verified. Leads are hypothesized only.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="source tree (Foundry/Hardhat contracts root or repo)")
    parser.add_argument("--out", type=Path, default=Path(".ih-audit"), help="output directory")
    parser.add_argument("--case", type=Path, help="case manifest JSON")
    parser.add_argument(
        "--local-dev-scope",
        action="store_true",
        help="explicitly synthesize a local non-production case (required if --case omitted)",
    )
    parser.add_argument("--actor", action="append", dest="actors", default=None)
    parser.add_argument("--no-slither", action="store_true", help="skip slither even if installed")
    args = parser.parse_args(argv)
    try:
        return run_audit(
            args.root,
            args.out,
            case_path=args.case,
            actors=args.actors,
            local_dev=args.local_dev_scope,
            run_slither=not args.no_slither,
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"audit error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
