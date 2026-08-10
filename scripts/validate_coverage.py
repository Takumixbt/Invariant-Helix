#!/usr/bin/env python3
"""Validate coverage obligations and compute an auditable termination summary."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .evidence_manifest import load_manifest, validate_manifest_structure
    from .inventory import load_scope, validate_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from evidence_manifest import load_manifest, validate_manifest_structure
    from inventory import load_scope, validate_scope
    from security_utils import atomic_write_text


IMPACTS = {"critical", "high", "medium", "low", "informational"}
STATUSES = {"planned", "in_progress", "tested", "verified", "refuted", "blocked", "excluded", "uncovered", "stale"}
TERMINATIONS = {"complete", "complete_with_limitations", "inconclusive", "blocked", "aborted"}
CLOSED = {"tested", "verified", "refuted", "excluded"}
GAPS = {"planned", "in_progress", "blocked", "uncovered", "stale"}
REQUIRED_ITEM_FIELDS = {
    "coverage_id", "case_id", "snapshot_id", "target_refs", "impact_class", "owner",
    "hypothesis_families", "planned_observations", "negative_controls", "verifier_id", "status",
    "evidence_refs", "dependencies",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: Any, *, allow_empty: bool = False) -> bool:
    return isinstance(value, list) and (allow_empty or bool(value)) and all(_nonempty(item) for item in value)


def load_bundle(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("coverage bundle root must be an object")
    return value


def validate(
    bundle: dict[str, Any],
    *,
    case: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    for field in ("schema_version", "case_id", "snapshot_id", "termination_status", "items"):
        if field not in bundle:
            errors.append(f"coverage bundle missing {field}")
    termination = bundle.get("termination_status")
    if termination not in TERMINATIONS:
        errors.append("termination_status is invalid")
    items = bundle.get("items")
    if not isinstance(items, list) or not items or not all(isinstance(item, dict) for item in items):
        errors.append("items must be a non-empty array of objects")
        return errors, {}
    artifact_ids = {
        record.get("artifact_id")
        for record in (manifest or {}).get("artifacts", [])
        if isinstance(record, dict)
    }
    ids: set[str] = set()
    status_counts: Counter[str] = Counter()
    impact_counts: Counter[str] = Counter()
    gap_counts: Counter[str] = Counter()
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        missing = REQUIRED_ITEM_FIELDS - item.keys()
        if missing:
            errors.append(f"{prefix} missing: {', '.join(sorted(missing))}")
        coverage_id = item.get("coverage_id")
        if not _nonempty(coverage_id):
            errors.append(f"{prefix}.coverage_id is invalid")
        elif coverage_id in ids:
            errors.append(f"{prefix}.coverage_id is duplicated")
        ids.add(str(coverage_id))
        if item.get("case_id") != bundle.get("case_id") or item.get("snapshot_id") != bundle.get("snapshot_id"):
            errors.append(f"{prefix} does not match the bundle case/snapshot")
        impact = item.get("impact_class")
        status = item.get("status")
        if impact not in IMPACTS:
            errors.append(f"{prefix}.impact_class is invalid")
        if status not in STATUSES:
            errors.append(f"{prefix}.status is invalid")
        else:
            status_counts[str(status)] += 1
            if status in GAPS:
                gap_counts[str(impact)] += 1
        if impact in IMPACTS:
            impact_counts[str(impact)] += 1
        for field in ("target_refs", "hypothesis_families", "planned_observations", "negative_controls"):
            if not _strings(item.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty array of strings")
        for field in ("evidence_refs", "dependencies"):
            if not _strings(item.get(field), allow_empty=True):
                errors.append(f"{prefix}.{field} must be an array of strings")
        if not _nonempty(item.get("owner")) or not _nonempty(item.get("verifier_id")):
            errors.append(f"{prefix} requires owner and verifier_id")
        if item.get("owner") == item.get("verifier_id"):
            errors.append(f"{prefix} owner and verifier must differ")
        if status in {"tested", "verified", "refuted"} and not item.get("evidence_refs"):
            errors.append(f"{prefix} closed status requires evidence_refs")
        if status == "blocked" and not _nonempty(item.get("blocker")):
            errors.append(f"{prefix} blocked status requires blocker")
        if status == "excluded" and not _nonempty(item.get("exclusion_reason")):
            errors.append(f"{prefix} excluded status requires exclusion_reason")
        if manifest:
            unresolved = sorted(set(item.get("evidence_refs", [])) - artifact_ids)
            if unresolved:
                errors.append(f"{prefix} unresolved evidence_refs: {', '.join(unresolved)}")
    if termination == "complete" and any(item.get("status") not in CLOSED for item in items):
        errors.append("complete requires every coverage item to be closed")
    if termination == "complete_with_limitations":
        material_gaps = [
            item["coverage_id"]
            for item in items
            if item.get("status") in GAPS and item.get("impact_class") in {"critical", "high", "medium"}
        ]
        if material_gaps:
            errors.append(f"complete_with_limitations has material gaps: {', '.join(material_gaps)}")
    if termination in {"complete", "complete_with_limitations"} and status_counts.get("stale", 0):
        errors.append(f"{termination} cannot contain stale coverage")
    if case:
        if bundle.get("case_id") != case.get("case_id") or bundle.get("snapshot_id") != case.get("snapshot_id"):
            errors.append("coverage bundle does not match the case manifest")
    if manifest:
        if bundle.get("case_id") != manifest.get("case_id") or bundle.get("snapshot_id") != manifest.get("snapshot_id"):
            errors.append("coverage bundle does not match the evidence manifest")
    summary = {
        "schema_version": "1.0",
        "case_id": bundle.get("case_id"),
        "snapshot_id": bundle.get("snapshot_id"),
        "termination_status": termination,
        "total_items": len(items),
        "by_status": dict(sorted(status_counts.items())),
        "by_impact": dict(sorted(impact_counts.items())),
        "coverage_debt_by_impact": dict(sorted(gap_counts.items())),
    }
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("coverage", type=Path)
    parser.add_argument("--case-manifest", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output-summary", type=Path)
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.coverage)
        case = load_scope(args.case_manifest) if args.case_manifest else None
        manifest = load_manifest(args.manifest) if args.manifest else None
        preflight: list[str] = []
        if case:
            preflight.extend(f"case manifest: {error}" for error in validate_scope(case))
        if manifest:
            preflight.extend(validate_manifest_structure(manifest))
        errors, summary = validate(bundle, case=case, manifest=manifest)
        errors = preflight + errors
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        if args.output_summary:
            atomic_write_text(args.output_summary, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"coverage validation error: {exc}", file=sys.stderr)
        return 2
    print(f"validated {summary['total_items']} coverage item(s): {summary['termination_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
