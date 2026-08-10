#!/usr/bin/env python3
"""Merge case-bound graphs without losing evidence or hiding conflicts."""

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


NODE_FIELDS = {
    "id", "kind", "label", "case_id", "snapshot_id", "status", "confidence", "locators",
    "evidence_refs", "properties", "sensitivity",
}
EDGE_FIELDS = {
    "id", "from", "relation", "to", "status", "confidence", "evidence_refs", "locator", "valid_for",
}


def load_graph(path: Path) -> dict[str, Any]:
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: graph must be JSON: {exc}") from exc
    if not isinstance(graph, dict):
        raise ValueError(f"{path}: graph root must be an object")
    return graph


def validate_graph(graph: dict[str, Any], source: str = "graph") -> list[str]:
    errors: list[str] = []
    case_id = graph.get("case_id")
    snapshot_id = graph.get("snapshot_id")
    if not isinstance(case_id, str) or not case_id:
        errors.append(f"{source}: case_id is required")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        errors.append(f"{source}: snapshot_id is required")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not all(isinstance(item, dict) for item in nodes):
        errors.append(f"{source}: nodes must be an array of objects")
        return errors
    if not isinstance(edges, list) or not all(isinstance(item, dict) for item in edges):
        errors.append(f"{source}: edges must be an array of objects")
        return errors
    node_ids: set[str] = set()
    for index, node in enumerate(nodes):
        prefix = f"{source}: nodes[{index}]"
        missing = NODE_FIELDS - node.keys()
        if missing:
            errors.append(f"{prefix} missing: {', '.join(sorted(missing))}")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"{prefix}.id is invalid")
        elif node_id in node_ids:
            errors.append(f"{prefix}.id is duplicated")
        node_ids.add(str(node_id))
        if node.get("case_id") != case_id or node.get("snapshot_id") != snapshot_id:
            errors.append(f"{prefix} does not match graph case/snapshot")
    edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        prefix = f"{source}: edges[{index}]"
        missing = EDGE_FIELDS - edge.keys()
        if missing:
            errors.append(f"{prefix} missing: {', '.join(sorted(missing))}")
        edge_id = edge.get("id")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(f"{prefix}.id is invalid")
        elif edge_id in edge_ids:
            errors.append(f"{prefix}.id is duplicated")
        edge_ids.add(str(edge_id))
        if edge.get("from") not in node_ids or edge.get("to") not in node_ids:
            errors.append(f"{prefix} has a dangling endpoint")
        if edge.get("valid_for") != snapshot_id:
            errors.append(f"{prefix}.valid_for does not match the graph snapshot")
    return errors


def _semantic(record: dict[str, Any], ignored: set[str]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key not in ignored}


def _union(left: list[str], right: list[str]) -> list[str]:
    return sorted(set(left) | set(right))


def _merge_compatible(existing: dict[str, Any], incoming: dict[str, Any], kind: str) -> dict[str, Any] | None:
    ignored = {"evidence_refs", "locators"} if kind == "node" else {"evidence_refs"}
    if _semantic(existing, ignored) != _semantic(incoming, ignored):
        return None
    merged = dict(existing)
    merged["evidence_refs"] = _union(existing.get("evidence_refs", []), incoming.get("evidence_refs", []))
    if kind == "node":
        merged["locators"] = _union(existing.get("locators", []), incoming.get("locators", []))
    return merged


def merge(paths: list[Path]) -> dict[str, Any]:
    if not paths:
        raise ValueError("at least one graph input is required")
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    sources: dict[tuple[str, str], str] = {}
    conflict_variants: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    case_id: str | None = None
    snapshot_id: str | None = None
    for path in paths:
        graph = load_graph(path)
        errors = validate_graph(graph, path.as_posix())
        if errors:
            raise ValueError("; ".join(errors))
        current = (graph["case_id"], graph["snapshot_id"])
        if case_id is None:
            case_id, snapshot_id = current
        elif current != (case_id, snapshot_id):
            raise ValueError(f"{path}: mixed case or snapshot is not mergeable")
        for kind, records, destination in (
            ("node", graph["nodes"], nodes),
            ("edge", graph["edges"], edges),
        ):
            for record in records:
                record_id = record["id"]
                key = (kind, record_id)
                if record_id not in destination:
                    destination[record_id] = record
                    sources[key] = path.as_posix()
                    continue
                merged = _merge_compatible(destination[record_id], record, kind)
                if merged is not None:
                    destination[record_id] = merged
                    continue
                fingerprint = json.dumps(record, sort_keys=True, separators=(",", ":"))
                variants = conflict_variants.setdefault(key, {})
                variants.setdefault(
                    fingerprint,
                    {"source": path.as_posix(), "record": record},
                )
    conflicts = []
    for (kind, record_id), variants in sorted(conflict_variants.items()):
        conflicts.append(
            {
                "type": kind,
                "id": record_id,
                "canonical_source": sources[(kind, record_id)],
                "alternatives": sorted(variants.values(), key=lambda item: item["source"]),
            }
        )
    result = {
        "schema_version": "1.0",
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(edges.values(), key=lambda item: item["id"]),
        "merge_conflicts": conflicts,
        "source_graphs": [path.as_posix() for path in paths],
    }
    errors = validate_graph(result, "merged graph")
    if errors:
        raise ValueError("; ".join(errors))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = merge(args.inputs)
        atomic_write_text(args.output, json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"graph merge error: {exc}", file=sys.stderr)
        return 2
    print(
        f"wrote {args.output} ({len(result['nodes'])} nodes, {len(result['edges'])} edges, "
        f"{len(result['merge_conflicts'])} conflicts)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
