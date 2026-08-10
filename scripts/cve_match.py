#!/usr/bin/env python3
"""Match local components to local CVE records with conservative version evaluation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


VERSION = re.compile(r"^v?(\d+(?:\.\d+){0,3})(?:[-+].*)?$")
CONSTRAINT = re.compile(r"^(>=|<=|>|<|==|=)?\s*(v?\d+(?:\.\d+){0,3}(?:[-+].*)?)$")


def token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_version(value: str) -> tuple[int, int, int, int] | None:
    match = VERSION.fullmatch(value.strip())
    if not match:
        return None
    parts = [int(item) for item in match.group(1).split(".")]
    return tuple((parts + [0, 0, 0, 0])[:4])  # type: ignore[return-value]


def version_matches(value: str, expression: str | None) -> bool | None:
    if not expression:
        return None
    parsed = parse_version(value)
    if parsed is None:
        return None
    for raw in expression.split(","):
        match = CONSTRAINT.fullmatch(raw.strip())
        if not match:
            return None
        operator = match.group(1) or "=="
        expected = parse_version(match.group(2))
        if expected is None:
            return None
        comparison = {
            "==": parsed == expected,
            "=": parsed == expected,
            ">=": parsed >= expected,
            "<=": parsed <= expected,
            ">": parsed > expected,
            "<": parsed < expected,
        }[operator]
        if not comparison:
            return False
    return True


def _records(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{name} must be an array of objects")
    return value


def load_inputs(inventory_path: Path, cves_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    cves = json.loads(cves_path.read_text(encoding="utf-8"))
    if isinstance(inventory, dict):
        components = inventory.get("components")
    else:
        components = inventory
    components = _records(components, "component inventory")
    cve_records = _records(cves, "CVE records")
    for index, component in enumerate(components):
        if not isinstance(component.get("name"), str) or not component["name"].strip():
            raise ValueError(f"components[{index}].name is required")
        if not isinstance(component.get("version"), str) or not component["version"].strip():
            raise ValueError(f"components[{index}].version is required")
    for index, cve in enumerate(cve_records):
        if not isinstance(cve.get("cve_id"), str) or not cve["cve_id"].strip():
            raise ValueError(f"cves[{index}].cve_id is required")
        products = cve.get("products")
        if not isinstance(products, list) or not products or not all(isinstance(item, str) for item in products):
            raise ValueError(f"cves[{index}].products must be a non-empty array")
    return components, cve_records


def match(components: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, Any]:
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cve in records:
        for product in cve["products"] + cve.get("aliases", []):
            normalized = token(str(product))
            if normalized:
                index[normalized].append(cve)
    candidates: list[dict[str, Any]] = []
    not_affected: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for component in components:
        names = [component["name"], *component.get("aliases", [])]
        matching_records: list[dict[str, Any]] = []
        for name in names:
            matching_records.extend(index.get(token(str(name)), []))
        for cve in matching_records:
            key = (component["name"], component["version"], cve["cve_id"])
            if key in seen:
                continue
            seen.add(key)
            affected_range = cve.get("affected_versions")
            version_result = version_matches(component["version"], affected_range)
            base = {
                "component": component,
                "cve_id": cve["cve_id"],
                "affected_versions": affected_range,
                "affected_feature": cve.get("affected_feature", "unspecified"),
                "references": cve.get("references", []),
                "target_version": component["version"],
                "feature_reachable": "unverified",
                "verified_against_target": False,
                "safe_reproduction": "verify version/configuration and affected feature before any lab-only PoC",
                "known_false_positives": cve.get(
                    "known_false_positives",
                    ["vendor backport", "feature disabled", "fingerprint alias collision"],
                ),
            }
            if version_result is False:
                not_affected.append({**base, "version_evaluation": "outside-recorded-range"})
                continue
            candidates.append(
                {
                    **base,
                    "match": "product-and-version" if version_result is True else "product-only",
                    "version_evaluation": "affected" if version_result is True else "unresolved",
                    "confidence": "high" if version_result is True else "low",
                    "verification_status": "unverified",
                }
            )
    def sort_key(item: dict[str, Any]) -> tuple[str, str, str]:
        return item["cve_id"], item["component"]["name"], item["target_version"]

    return {
        "schema_version": "1.0",
        "candidates": sorted(candidates, key=sort_key),
        "not_affected": sorted(not_affected, key=sort_key),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--cves", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        components, records = load_inputs(args.inventory, args.cves)
        result = match(components, records)
        atomic_write_text(args.output, json.dumps(result, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"CVE input error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(result['candidates'])} candidate(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
