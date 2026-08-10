#!/usr/bin/env python3
"""Drive the iterative audit loop: alternating passes, deltas, reopening, convergence.

This makes the nemesis feedback loop executable instead of aspirational. Each pass
alternates a first-principles branch with a state/invariant branch; every pass emits a
delta (new facts, new hypotheses, refutations, reopened items) and the loop terminates
on a *reasoned* condition -- convergence, budget exhaustion, or a blocking gap -- never
on a fixed count alone.

Two rules are enforced structurally, because they are what stop a loop from becoming an
echo chamber:

  * a branch receives the previous branch's EVIDENCE and QUESTIONS, never its verdict;
  * convergence (no new material) reduces uncertainty only when coverage is complete --
    otherwise the loop terminates ``inconclusive`` with its debt intact.

The loop plans and accounts for work; it does not itself adjudicate. Standard library
only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


# The alternating branch protocol. Each pass runs one side, then hands evidence across.
BRANCHES = ("first-principles", "invariant-state")
MATERIAL = {"critical", "high"}


def _ids(records: list[dict[str, Any]], key: str) -> set[str]:
    return {str(r[key]) for r in records if isinstance(r, dict) and r.get(key)}


def pass_delta(
    previous: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    """Compute what a pass actually added, relative to the state before it."""
    prev_nodes = _ids(previous.get("nodes", []), "id")
    prev_hypotheses = _ids(previous.get("hypotheses", []), "id")
    prev_refuted = _ids(previous.get("refuted", []), "id")
    now_nodes = _ids(current.get("nodes", []), "id")
    now_hypotheses = _ids(current.get("hypotheses", []), "id")
    now_refuted = _ids(current.get("refuted", []), "id")
    return {
        "new_facts": sorted(now_nodes - prev_nodes),
        "new_hypotheses": sorted(now_hypotheses - prev_hypotheses),
        "new_refutations": sorted(now_refuted - prev_refuted),
    }


def reopened_by_delta(
    coverage_items: list[dict[str, Any]],
    delta: dict[str, Any],
) -> list[str]:
    """A cleared item is reopened when the delta touches something it depends on.

    This is the rule that prevents a loop from 'finishing' while its own later passes
    invalidate its earlier conclusions.
    """
    touched = set(delta.get("new_facts", [])) | set(delta.get("new_refutations", []))
    if not touched:
        return []
    reopened: list[str] = []
    for item in coverage_items:
        if not isinstance(item, dict):
            continue
        if item.get("status") not in {"tested", "verified", "refuted"}:
            continue
        dependencies = set(item.get("dependencies", []) or []) | set(item.get("target_refs", []) or [])
        if dependencies & touched:
            reopened.append(str(item.get("coverage_id")))
    return sorted(reopened)


def evaluate_termination(
    passes: list[dict[str, Any]],
    coverage_items: list[dict[str, Any]],
    *,
    max_passes: int,
    quiet_passes_required: int = 2,
) -> dict[str, Any]:
    """Decide whether the loop may stop, and say honestly what stopping means."""
    gaps = [
        item for item in coverage_items
        if isinstance(item, dict)
        and item.get("status") in {"planned", "in_progress", "blocked", "uncovered", "stale"}
    ]
    material_gaps = [item for item in gaps if item.get("impact_class") in MATERIAL]
    exercised = [
        item for item in coverage_items
        if isinstance(item, dict) and item.get("status") in {"tested", "verified", "refuted"}
    ]
    # A pass is "quiet" when it produced no new material of any kind.
    quiet_tail = 0
    for record in reversed(passes):
        delta = record.get("delta", {})
        if any(delta.get(key) for key in ("new_facts", "new_hypotheses", "new_refutations")):
            break
        quiet_tail += 1
    converged = quiet_tail >= quiet_passes_required
    budget_spent = len(passes) >= max_passes

    if converged and not gaps and exercised:
        status, reason = "complete", "converged with no open coverage gaps"
    elif converged and not material_gaps and exercised:
        status, reason = (
            "complete_with_limitations",
            f"converged; {len(gaps)} non-material gap(s) remain as coverage debt",
        )
    elif converged:
        status, reason = (
            "inconclusive",
            f"passes went quiet but {len(material_gaps)} material gap(s) remain: "
            "silence is not coverage",
        )
    elif budget_spent:
        status, reason = (
            "inconclusive",
            f"pass budget ({max_passes}) exhausted while still producing new material",
        )
    else:
        status, reason = "continue", "the last pass still produced new material"
    return {
        "termination_status": status,
        "reason": reason,
        "converged": converged,
        "quiet_passes": quiet_tail,
        "passes_run": len(passes),
        "open_gaps": len(gaps),
        "material_gaps": sorted(str(item.get("coverage_id")) for item in material_gaps),
        "exercised_items": len(exercised),
    }


def run(
    state: dict[str, Any],
    coverage_items: list[dict[str, Any]],
    *,
    max_passes: int = 6,
) -> dict[str, Any]:
    """Replay the recorded passes, computing deltas, reopenings, and termination.

    ``state`` carries ``passes``: each an object with ``nodes``/``hypotheses``/
    ``refuted`` produced up to and including that pass. The loop is a planner and
    accountant over branch output -- the branches themselves are run by the controller.
    """
    recorded = state.get("passes", [])
    if not isinstance(recorded, list):
        raise ValueError("state.passes must be an array")
    history: list[dict[str, Any]] = []
    previous: dict[str, Any] = {"nodes": [], "hypotheses": [], "refuted": []}
    for index, current in enumerate(recorded):
        if not isinstance(current, dict):
            raise ValueError(f"state.passes[{index}] must be an object")
        delta = pass_delta(previous, current)
        reopened = reopened_by_delta(coverage_items, delta)
        history.append({
            "pass": index + 1,
            "branch": BRANCHES[index % len(BRANCHES)],
            "delta": delta,
            "reopened": reopened,
            # The next branch receives evidence and questions, never a verdict.
            "handoff": {
                "evidence": delta["new_facts"],
                "questions": delta["new_hypotheses"],
                "verdicts_withheld": True,
            },
        })
        previous = current
    termination = evaluate_termination(history, coverage_items, max_passes=max_passes)
    return {
        "schema_version": "1.0",
        "case_id": state.get("case_id"),
        "snapshot_id": state.get("snapshot_id"),
        "passes": history,
        "termination": termination,
        "next_branch": BRANCHES[len(history) % len(BRANCHES)] if termination["termination_status"] == "continue" else None,
        "reopened_total": sorted({item for record in history for item in record["reopened"]}),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("state", type=Path, help="loop state JSON with a passes array")
    parser.add_argument("--coverage", type=Path, help="coverage bundle used for gap accounting")
    parser.add_argument("--max-passes", type=int, default=6)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        state = json.loads(args.state.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise ValueError("loop state must be a JSON object")
        items: list[dict[str, Any]] = []
        if args.coverage:
            bundle = json.loads(args.coverage.read_text(encoding="utf-8"))
            items = bundle.get("items", []) if isinstance(bundle, dict) else []
        result = run(state, items, max_passes=args.max_passes)
        if args.output:
            atomic_write_text(args.output, json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"audit loop error: {exc}", file=sys.stderr)
        return 2
    for record in result["passes"]:
        delta = record["delta"]
        counts = (
            f"+{len(delta['new_facts'])} facts, +{len(delta['new_hypotheses'])} hypotheses, "
            f"+{len(delta['new_refutations'])} refutations"
        )
        reopened = f", reopened {len(record['reopened'])}" if record["reopened"] else ""
        print(f"  pass {record['pass']} [{record['branch']}]: {counts}{reopened}")
    termination = result["termination"]
    print(f"\n{termination['termination_status']}: {termination['reason']}")
    if termination["material_gaps"]:
        print(f"material gaps: {', '.join(termination['material_gaps'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
