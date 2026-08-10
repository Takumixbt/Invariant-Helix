#!/usr/bin/env python3
"""Validate the chain adapter registry, maturity claims, and document links."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED = {
    "adapter_id", "chain_family", "status", "maturity_tier", "document", "detection_markers",
    "enumeration_strategy", "authority_model", "state_model", "trace_strategy",
    "simulation_strategy", "property_strategy", "reproduction_format", "known_gaps",
}


def validate_registry(value: Any, *, project_root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict) or value.get("schema_version") != "1.0":
        return ["registry must be a schema_version=1.0 object"]
    adapters = value.get("adapters")
    if not isinstance(adapters, list) or not adapters or not all(isinstance(item, dict) for item in adapters):
        return ["adapters must be a non-empty array of objects"]
    ids: set[str] = set()
    families: set[str] = set()
    for index, adapter in enumerate(adapters):
        prefix = f"adapters[{index}]"
        missing = REQUIRED - adapter.keys()
        if missing:
            errors.append(f"{prefix} missing: {', '.join(sorted(missing))}")
        adapter_id = adapter.get("adapter_id")
        family = adapter.get("chain_family")
        if not isinstance(adapter_id, str) or not adapter_id:
            errors.append(f"{prefix}.adapter_id is invalid")
        elif adapter_id in ids:
            errors.append(f"{prefix}.adapter_id is duplicated")
        ids.add(str(adapter_id))
        if not isinstance(family, str) or not family:
            errors.append(f"{prefix}.chain_family is invalid")
        elif family in families:
            errors.append(f"{prefix}.chain_family is duplicated")
        families.add(str(family))
        if adapter.get("status") not in {"methodology-only", "executable"}:
            errors.append(f"{prefix}.status is invalid")
        tier = adapter.get("maturity_tier")
        if not isinstance(tier, int) or isinstance(tier, bool) or tier not in {1, 2, 3}:
            errors.append(f"{prefix}.maturity_tier is invalid")
        if adapter.get("status") == "methodology-only" and tier != 3:
            errors.append(f"{prefix} methodology-only adapters must remain Tier 3")
        for field in REQUIRED - {"adapter_id", "chain_family", "status", "maturity_tier", "document", "detection_markers", "known_gaps"}:
            if not isinstance(adapter.get(field), str) or not adapter[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("detection_markers", "known_gaps"):
            value_list = adapter.get(field)
            if not isinstance(value_list, list) or not value_list or not all(isinstance(item, str) and item.strip() for item in value_list):
                errors.append(f"{prefix}.{field} must be a non-empty string array")
        document = adapter.get("document")
        if not isinstance(document, str) or Path(document).is_absolute() or not (project_root / str(document)).is_file():
            errors.append(f"{prefix}.document does not resolve inside the project")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    args = parser.parse_args(argv)
    try:
        value = json.loads(args.registry.read_text(encoding="utf-8"))
        project_root = args.registry.resolve().parents[2]
        errors = validate_registry(value, project_root=project_root)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"adapter validation error: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(value['adapters'])} chain adapter(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
