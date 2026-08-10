#!/usr/bin/env python3
"""Validate a case manifest and produce a deterministic, type-aware inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text, canonical_http_url
except ImportError:  # direct script execution
    from security_utils import atomic_write_text, canonical_http_url


TARGET_TYPES = {"web-origin", "repository", "contract", "program", "rpc"}
TARGET_KINDS = {"web", "chain", "combined", "infrastructure"}
ENVIRONMENTS = {"local", "fork", "testnet", "production-program"}
CAPABILITIES = {
    "surface_inventory",
    "http_crawl",
    "browser_workflow",
    "proxy_observation",
    "request_replay",
    "input_mutation",
    "synchronized_requests",
    "oob_observation",
    "source_analysis",
    "chain_simulation",
    "execution_trace",
    "property_fuzzing",
    "evidence_manifest",
}
REQUIRED_CASE_FIELDS = (
    "case_id",
    "operator",
    "authorization_reference",
    "authorization_expires_at",
    "snapshot_id",
    "target_kind",
    "targets",
    "rules_of_engagement",
    "allowed_capabilities",
    "redaction_policy",
)
REQUIRED_RULE_FIELDS = (
    "active_testing",
    "max_requests",
    "max_concurrency",
    "test_identities",
    "oob_allowed",
    "real_funds_allowed",
    "impact_limit",
    "prohibited_effects",
    "stop_conditions",
    "emergency_contact",
    "data_retention",
)


def load_scope(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"scope must be JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("scope root must be an object")
    return value


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not _nonempty_string(value):
        return False
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def normalize_target(target: dict[str, Any] | str) -> str:
    """Normalize a target without changing chain-native identifiers."""

    if isinstance(target, str):
        value = target.strip()
        if "://" not in value:
            value = f"https://{value}"
        return canonical_http_url(value)
    target_type = str(target.get("type", ""))
    value = str(target.get("value", "")).strip()
    if target_type in {"web-origin", "rpc"}:
        return canonical_http_url(value)
    if target_type == "repository" and value.lower().startswith(("http://", "https://")):
        return canonical_http_url(value)
    if target_type in {"repository", "contract", "program"}:
        return value
    raise ValueError(f"unsupported target type: {target_type or '<empty>'}")


def target_identity(target: dict[str, Any], normalized: str) -> str:
    identity = {
        "type": target["type"],
        "chain": str(target.get("chain", "")),
        "network": str(target.get("network", "")),
        "environment": target["environment"],
        "value": normalized,
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return f"target:{hashlib.sha256(payload).hexdigest()[:20]}"


def _validate_rules(rules: Any, errors: list[str]) -> None:
    if not isinstance(rules, dict):
        errors.append("rules_of_engagement must be an object")
        return
    for field in REQUIRED_RULE_FIELDS:
        if field not in rules:
            errors.append(f"rules_of_engagement missing {field}")
    for field in ("active_testing", "oob_allowed", "real_funds_allowed"):
        if field in rules and not isinstance(rules[field], bool):
            errors.append(f"rules_of_engagement.{field} must be boolean")
    for field in ("max_requests", "max_concurrency"):
        value = rules.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"rules_of_engagement.{field} must be a positive integer")
    for field in ("test_identities", "prohibited_effects", "stop_conditions"):
        value = rules.get(field)
        if not isinstance(value, list) or not all(_nonempty_string(item) for item in value):
            errors.append(f"rules_of_engagement.{field} must be an array of non-empty strings")
    for field in ("impact_limit", "emergency_contact", "data_retention"):
        if not _nonempty_string(rules.get(field)):
            errors.append(f"rules_of_engagement.{field} must be a non-empty string")
    if rules.get("active_testing") is True and not rules.get("test_identities"):
        errors.append("active testing requires at least one test identity")
    if rules.get("real_funds_allowed") is True:
        fund_limit = rules.get("max_test_funds")
        if not isinstance(fund_limit, dict) or not _nonempty_string(fund_limit.get("asset")):
            errors.append("real_funds_allowed=true requires max_test_funds.asset and amount")
        elif not isinstance(fund_limit.get("amount"), (int, float)) or fund_limit["amount"] <= 0:
            errors.append("max_test_funds.amount must be positive")


def validate_scope(scope: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_CASE_FIELDS:
        if field not in scope:
            errors.append(f"missing required field: {field}")
    for field in ("case_id", "operator", "authorization_reference", "snapshot_id", "redaction_policy"):
        if field in scope and not _nonempty_string(scope[field]):
            errors.append(f"{field} must be a non-empty string")
    if "authorization_expires_at" in scope and not _valid_timestamp(scope["authorization_expires_at"]):
        errors.append("authorization_expires_at must be an ISO-8601 timestamp")
    if scope.get("target_kind") not in TARGET_KINDS:
        errors.append(f"target_kind must be one of: {', '.join(sorted(TARGET_KINDS))}")

    capabilities = scope.get("allowed_capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("allowed_capabilities must be a non-empty array")
    elif not all(isinstance(item, str) and item in CAPABILITIES for item in capabilities):
        errors.append("allowed_capabilities contains an unknown capability")
    elif len(set(capabilities)) != len(capabilities):
        errors.append("allowed_capabilities contains duplicates")

    _validate_rules(scope.get("rules_of_engagement"), errors)
    rules = scope.get("rules_of_engagement") if isinstance(scope.get("rules_of_engagement"), dict) else {}
    if rules.get("oob_allowed") is True and isinstance(capabilities, list) and "oob_observation" not in capabilities:
        errors.append("oob_allowed=true requires the oob_observation capability")

    targets = scope.get("targets")
    if not isinstance(targets, list) or not targets:
        errors.append("targets must be a non-empty array")
        return errors
    seen: set[tuple[str, str, str, str, str]] = set()
    in_scope_count = 0
    for index, target in enumerate(targets):
        prefix = f"targets[{index}]"
        if not isinstance(target, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("type", "value", "in_scope", "environment"):
            if field not in target:
                errors.append(f"{prefix} missing {field}")
        target_type = target.get("type")
        if target_type not in TARGET_TYPES:
            errors.append(f"{prefix}.type is unsupported")
        if not _nonempty_string(target.get("value")):
            errors.append(f"{prefix}.value must be a non-empty string")
        if not isinstance(target.get("in_scope"), bool):
            errors.append(f"{prefix}.in_scope must be boolean")
        elif target["in_scope"]:
            in_scope_count += 1
        if target.get("environment") not in ENVIRONMENTS:
            errors.append(f"{prefix}.environment is unsupported")
        if target_type in {"contract", "program", "rpc"}:
            for field in ("chain", "network"):
                if not _nonempty_string(target.get(field)):
                    errors.append(f"{prefix}.{field} is required for {target_type}")
        if target_type in TARGET_TYPES and _nonempty_string(target.get("value")):
            try:
                normalized = normalize_target(target)
            except ValueError as exc:
                errors.append(f"{prefix}.value is invalid: {exc}")
                continue
            key = (
                str(target_type),
                str(target.get("chain", "")),
                str(target.get("network", "")),
                str(target.get("environment", "")),
                normalized,
            )
            if key in seen:
                errors.append(f"duplicate target after type-aware normalization: {normalized}")
            seen.add(key)
    if in_scope_count == 0:
        errors.append("at least one target must set in_scope=true")
    return errors


def build_inventory(scope: dict[str, Any]) -> dict[str, Any]:
    targets: list[dict[str, Any]] = []
    for target in scope["targets"]:
        item = dict(target)
        normalized = normalize_target(item)
        item["normalized_value"] = normalized
        item["target_id"] = target_identity(item, normalized)
        targets.append(item)
    targets.sort(key=lambda item: item["target_id"])
    return {
        "schema_version": "1.0",
        "case_id": scope["case_id"],
        "operator": scope["operator"],
        "authorization_reference": scope["authorization_reference"],
        "authorization_expires_at": scope["authorization_expires_at"],
        "snapshot_id": scope["snapshot_id"],
        "target_kind": scope["target_kind"],
        "rules_of_engagement": scope["rules_of_engagement"],
        "allowed_capabilities": sorted(scope["allowed_capabilities"]),
        "redaction_policy": scope["redaction_policy"],
        "targets": targets,
        "coverage_items": [
            {
                "id": f"coverage:{item['target_id'].split(':', 1)[1]}",
                "case_id": scope["case_id"],
                "snapshot_id": scope["snapshot_id"],
                "target_refs": [item["target_id"]],
                "status": "planned" if item["in_scope"] else "excluded",
                "owner": "discovery",
                "exclusion_reason": item.get("exclusion_reason") if not item["in_scope"] else None,
            }
            for item in targets
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        scope = load_scope(args.scope)
        errors = validate_scope(scope)
        if errors:
            for error in errors:
                print(f"scope error: {error}", file=sys.stderr)
            return 2
        inventory = build_inventory(scope)
        atomic_write_text(args.output, json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"inventory error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
