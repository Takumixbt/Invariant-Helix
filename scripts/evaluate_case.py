#!/usr/bin/env python3
"""Run the case, graph, evidence, finding, and coverage gates as one evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .evidence_manifest import load_manifest, validate_manifest_structure, verify
    from .graph_merge import load_graph, validate_graph
    from .inventory import load_scope, validate_scope
    from .security_utils import atomic_write_text
    from .validate_coverage import load_bundle, validate as validate_coverage
    from .validate_findings import load_findings, validate as validate_findings
except ImportError:  # direct script execution
    from evidence_manifest import load_manifest, validate_manifest_structure, verify
    from graph_merge import load_graph, validate_graph
    from inventory import load_scope, validate_scope
    from security_utils import atomic_write_text
    from validate_coverage import load_bundle, validate as validate_coverage
    from validate_findings import load_findings, validate as validate_findings


def evaluate(
    *,
    case: dict[str, Any],
    graph: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage: dict[str, Any],
    manifest: dict[str, Any],
    release: bool,
) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    errors.extend(f"case: {error}" for error in validate_scope(case))
    errors.extend(validate_manifest_structure(manifest))
    errors.extend(validate_graph(graph))
    finding_errors = validate_findings(findings, release, manifest=manifest, case=case)
    errors.extend(finding_errors)
    coverage_errors, coverage_summary = validate_coverage(coverage, case=case, manifest=manifest)
    errors.extend(coverage_errors)
    expected = (case.get("case_id"), case.get("snapshot_id"))
    for name, artifact in (("graph", graph), ("coverage", coverage), ("manifest", manifest)):
        if (artifact.get("case_id"), artifact.get("snapshot_id")) != expected:
            errors.append(f"{name} does not match the case/snapshot")
    if release and graph.get("merge_conflicts"):
        errors.append("release graph contains unresolved merge conflicts")
    node_ids = {node.get("id") for node in graph.get("nodes", []) if isinstance(node, dict)}
    artifact_ids = {
        record.get("artifact_id")
        for record in manifest.get("artifacts", [])
        if isinstance(record, dict)
    }
    for kind in ("nodes", "edges"):
        for record in graph.get(kind, []):
            unresolved_evidence = sorted(set(record.get("evidence_refs", [])) - artifact_ids)
            if unresolved_evidence:
                errors.append(
                    f"graph {record.get('id')} has unresolved evidence_refs: "
                    f"{', '.join(unresolved_evidence)}"
                )
    coverage_by_id = {
        item.get("coverage_id"): item
        for item in coverage.get("items", [])
        if isinstance(item, dict)
    }
    for item in coverage_by_id.values():
        if item.get("status") in {"tested", "verified", "refuted"}:
            unresolved = sorted(set(item.get("target_refs", [])) - node_ids)
            if unresolved:
                errors.append(
                    f"coverage {item.get('coverage_id')} has unresolved closed target_refs: "
                    f"{', '.join(unresolved)}"
                )
    for finding in findings:
        finding_id = finding.get("finding_id")
        refs = finding.get("coverage_refs", [])
        unresolved = sorted(set(refs) - coverage_by_id.keys())
        if unresolved:
            errors.append(f"finding {finding_id} has unresolved coverage_refs: {', '.join(unresolved)}")
        if finding.get("status") in {"verified", "downgraded", "released"} and not any(
            coverage_by_id.get(ref, {}).get("status") in {"verified", "tested"} for ref in refs
        ):
            errors.append(f"finding {finding_id} has no verified/tested coverage item")
    summary = {
        "schema_version": "1.0",
        "case_id": case.get("case_id"),
        "snapshot_id": case.get("snapshot_id"),
        "release_mode": release,
        "graph": {"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))},
        "findings": len(findings),
        "evidence_artifacts": len(manifest.get("artifacts", [])),
        "coverage": coverage_summary,
        "result": "pass" if not errors else "fail",
    }
    return errors, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-manifest", required=True, type=Path)
    parser.add_argument("--graph", required=True, type=Path)
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.case_manifest)
        graph = load_graph(args.graph)
        findings = load_findings(args.findings)
        coverage = load_bundle(args.coverage)
        manifest = load_manifest(args.manifest)
        integrity_errors = verify(args.manifest, args.evidence_root)
        errors, summary = evaluate(
            case=case,
            graph=graph,
            findings=findings,
            coverage=coverage,
            manifest=manifest,
            release=args.release,
        )
        errors = integrity_errors + errors
        summary["result"] = "pass" if not errors else "fail"
        if args.output:
            atomic_write_text(args.output, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"case evaluation error: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(
        f"evaluated case {summary['case_id']} ({summary['findings']} findings, "
        f"{summary['coverage']['total_items']} coverage items): pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
