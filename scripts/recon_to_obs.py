#!/usr/bin/env python3
"""Normalize recon CLI output into Invariant Helix observations JSONL.

Consumes a JSON object with any of ``hosts``, ``services``, ``origins``, ``routes``
(from nmap/amass/httpx/gobuster, adapted to this shape) and emits ``host``/``service``/
``origin``/``route`` observation nodes. Discovery only; scope is enforced upstream by the
case manifest allowlist. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .inventory import load_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from inventory import load_scope
    from security_utils import atomic_write_text

SLUG = re.compile(r"[^a-z0-9]+")
KIND_KEYS = {"hosts": "host", "services": "service", "origins": "origin", "routes": "route"}


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def normalize(export: dict[str, Any], case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key, kind in KIND_KEYS.items():
        for item in export.get(key, []) or []:
            value = item if isinstance(item, str) else (item.get("value") or item.get("url") or item.get("host"))
            if not value:
                continue
            value = str(value).strip()
            properties = item if isinstance(item, dict) else {}
            records.append({
                "id": slug(value, kind), "case_id": case_id, "snapshot_id": snapshot_id,
                "kind": kind, "label": value[:120], "status": "observed", "sensitivity": "public",
                "confidence": {"level": "medium", "reason": "recon discovery"},
                "properties": {k: v for k, v in properties.items() if k not in {"value", "url", "host"}},
                "locators": [value], "evidence_refs": [f"recon:{value}"],
            })
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="recon JSON export")
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        export = json.loads(args.export.read_text(encoding="utf-8"))
        if not isinstance(export, dict):
            raise ValueError("export must be a JSON object with hosts/services/origins/routes")
        records = normalize(export, str(case.get("case_id")), str(case.get("snapshot_id")))
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"recon normalize error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(records)} observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
