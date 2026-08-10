#!/usr/bin/env python3
"""Convert observation JSONL into a redacted, referentially valid graph projection."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text, redact
except ImportError:  # direct script execution
    from security_utils import atomic_write_text, redact


NODE_KINDS = {
    "case", "snapshot", "scope", "asset", "origin", "host", "service", "route",
    "endpoint", "parameter", "request", "response", "browser_action", "workflow",
    "websocket", "script", "cookie", "token_redacted", "actor", "identity", "role",
    "tenant", "boundary", "component", "program", "contract", "module", "entrypoint",
    "instruction", "state", "storage", "resource", "object", "account", "authority",
    "capability", "message", "oracle", "external_dependency", "event", "receipt",
    "invariant", "hypothesis", "test", "execution", "evidence", "finding",
    "coverage_item", "pattern", "cve",
    # zero-knowledge circuits: a missing constraint is the bug, so signals and
    # constraints are first-class graph nodes.
    "circuit", "constraint", "signal", "witness",
}
RELATIONS = {
    "contains", "hosts", "serves", "redirects_to", "links_to", "loads", "calls", "sends",
    "receives", "emits", "reads", "writes", "guards", "requires", "authenticates",
    "authorizes", "impersonates", "belongs_to", "crosses", "trusts", "delegates", "owns",
    "controls", "upgrades", "depends_on", "prices", "observes", "mutates", "reconciles",
    "derived_from", "mirrors", "replays_as", "races_with", "reaches", "violates", "tests",
    "supports", "refutes", "duplicates", "supersedes",
}
OBSERVATION_STATUSES = {"observed", "inferred", "hypothesized", "refuted", "stale"}
SENSITIVITIES = {"public", "internal", "secret-redacted", "restricted"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
SAFE_ID = re.compile(r"^[a-z][a-z0-9_.:-]{2,127}$")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any, field: str, line_number: int, *, required: bool = False) -> list[str]:
    if not isinstance(value, list) or not all(_nonempty_string(item) for item in value):
        raise ValueError(f"line {line_number}: {field} must be an array of non-empty strings")
    if required and not value:
        raise ValueError(f"line {line_number}: {field} must not be empty")
    return [str(item) for item in value]


def stable_id(case_id: str, snapshot_id: str, kind: str, label: str, identity: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "case_id": case_id,
            "snapshot_id": snapshot_id,
            "kind": kind,
            "label": label,
            "identity": identity,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"{kind}:{hashlib.sha256(payload).hexdigest()[:24]}"


def _confidence(value: Any, line_number: int) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"line {line_number}: confidence must be an object")
    level = value.get("level")
    reason = value.get("reason")
    if level not in CONFIDENCE_LEVELS or not _nonempty_string(reason):
        raise ValueError(f"line {line_number}: confidence requires a valid level and reason")
    return {"level": str(level), "reason": str(redact(reason))}


def normalize_line(item: dict[str, Any], line_number: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    case_id = item.get("case_id")
    snapshot_id = item.get("snapshot_id")
    kind = item.get("kind")
    label = item.get("label")
    status = item.get("status", "observed")
    sensitivity = item.get("sensitivity", "internal")
    if not _nonempty_string(case_id) or not _nonempty_string(snapshot_id):
        raise ValueError(f"line {line_number}: case_id and snapshot_id are required")
    if kind not in NODE_KINDS:
        raise ValueError(f"line {line_number}: unsupported node kind")
    if not _nonempty_string(label):
        raise ValueError(f"line {line_number}: label must be a non-empty string")
    if status not in OBSERVATION_STATUSES:
        raise ValueError(f"line {line_number}: status is not valid for an observation branch")
    if sensitivity not in SENSITIVITIES:
        raise ValueError(f"line {line_number}: sensitivity is invalid")
    properties = item.get("properties", {})
    identity = item.get("identity", {})
    if not isinstance(properties, dict) or not isinstance(identity, dict):
        raise ValueError(f"line {line_number}: properties and identity must be objects")
    evidence_refs = _string_list(item.get("evidence_refs", []), "evidence_refs", line_number)
    locators = _string_list(item.get("locators", []), "locators", line_number)
    if not evidence_refs and not locators:
        raise ValueError(f"line {line_number}: a locator or evidence reference is required")
    explicit_id = item.get("id")
    if explicit_id is not None and (not isinstance(explicit_id, str) or not SAFE_ID.fullmatch(explicit_id)):
        raise ValueError(f"line {line_number}: id must be a safe case-local identifier")
    node_id = explicit_id or stable_id(str(case_id), str(snapshot_id), str(kind), str(label), identity)
    node = {
        "id": node_id,
        "kind": kind,
        "label": redact(str(label)),
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "status": status,
        "confidence": _confidence(
            item.get("confidence", {"level": "medium", "reason": "captured observation"}),
            line_number,
        ),
        "locators": redact(locators),
        "evidence_refs": evidence_refs,
        "properties": redact(properties),
        "sensitivity": sensitivity,
    }
    edges: list[dict[str, Any]] = []
    raw_edges = item.get("edges", [])
    if not isinstance(raw_edges, list):
        raise ValueError(f"line {line_number}: edges must be an array")
    for index, edge in enumerate(raw_edges):
        if not isinstance(edge, dict):
            raise ValueError(f"line {line_number}: edges[{index}] must be an object")
        relation = edge.get("relation")
        target = edge.get("to")
        edge_status = edge.get("status", status)
        if relation not in RELATIONS or not _nonempty_string(target):
            raise ValueError(f"line {line_number}: edges[{index}] has an invalid relation or target")
        if edge_status not in OBSERVATION_STATUSES:
            raise ValueError(f"line {line_number}: edges[{index}].status is invalid")
        edge_evidence = _string_list(
            edge.get("evidence_refs", evidence_refs),
            f"edges[{index}].evidence_refs",
            line_number,
        )
        locator = edge.get("locator")
        if locator is not None and not _nonempty_string(locator):
            raise ValueError(f"line {line_number}: edges[{index}].locator must be a string")
        if not edge_evidence and locator is None:
            raise ValueError(f"line {line_number}: edges[{index}] requires evidence or a locator")
        identity_payload = json.dumps(
            {
                "case_id": case_id,
                "snapshot_id": snapshot_id,
                "from": node_id,
                "relation": relation,
                "to": target,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        edges.append(
            {
                "id": f"edge:{hashlib.sha256(identity_payload).hexdigest()[:24]}",
                "from": node_id,
                "relation": relation,
                "to": target,
                "status": edge_status,
                "confidence": _confidence(edge.get("confidence", node["confidence"]), line_number),
                "evidence_refs": edge_evidence,
                "locator": redact(locator) if locator is not None else None,
                "valid_for": snapshot_id,
            }
        )
    return node, edges


def _union(existing: list[str], incoming: list[str]) -> list[str]:
    return sorted(set(existing) | set(incoming))


def _merge_node(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    ignored = {"evidence_refs", "locators"}
    if {key: value for key, value in existing.items() if key not in ignored} != {
        key: value for key, value in incoming.items() if key not in ignored
    }:
        raise ValueError(f"conflicting observations share node id {existing['id']}")
    merged = dict(existing)
    merged["evidence_refs"] = _union(existing["evidence_refs"], incoming["evidence_refs"])
    merged["locators"] = _union(existing["locators"], incoming["locators"])
    return merged


def _merge_edge(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    if {key: value for key, value in existing.items() if key != "evidence_refs"} != {
        key: value for key, value in incoming.items() if key != "evidence_refs"
    }:
        raise ValueError(f"conflicting observations share edge id {existing['id']}")
    merged = dict(existing)
    merged["evidence_refs"] = _union(existing["evidence_refs"], incoming["evidence_refs"])
    return merged


def normalize(path: Path) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, dict[str, Any]] = {}
    case_id: str | None = None
    snapshot_id: str | None = None
    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            item = json.loads(raw)
            if not isinstance(item, dict):
                raise ValueError(f"line {line_number}: root must be an object")
            node, new_edges = normalize_line(item, line_number)
            if case_id is None:
                case_id, snapshot_id = node["case_id"], node["snapshot_id"]
            elif (node["case_id"], node["snapshot_id"]) != (case_id, snapshot_id):
                raise ValueError(f"line {line_number}: mixed case or snapshot")
            nodes[node["id"]] = _merge_node(nodes[node["id"]], node) if node["id"] in nodes else node
            for edge in new_edges:
                edges[edge["id"]] = (
                    _merge_edge(edges[edge["id"]], edge) if edge["id"] in edges else edge
                )
    if not nodes:
        raise ValueError("observation input contains no records")
    dangling = sorted({edge["to"] for edge in edges.values()} - nodes.keys())
    if dangling:
        raise ValueError(f"dangling edge target(s): {', '.join(dangling)}")
    return {
        "schema_version": "1.0",
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "nodes": sorted(nodes.values(), key=lambda item: item["id"]),
        "edges": sorted(edges.values(), key=lambda item: item["id"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        graph = normalize(args.input)
        atomic_write_text(args.output, json.dumps(graph, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"normalization error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
