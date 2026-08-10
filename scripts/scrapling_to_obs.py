#!/usr/bin/env python3
"""Normalize Scrapling crawl export into Invariant Helix observations JSONL.

Consumes a JSON object with any of ``routes``, ``forms``, ``scripts``, ``endpoints``
(each a list of items with a ``url``/``path`` and optional ``method``/``params``) and
emits ``route``/``form``/``script``/``endpoint`` observation nodes for the graph.
Discovery only — nodes are ``observed`` facts; the graph, not this script, proves flaws.
Standard library only.
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
KIND_KEYS = {"routes": "route", "forms": "form", "scripts": "script", "endpoints": "endpoint"}


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def normalize(export: dict[str, Any], case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for key, kind in KIND_KEYS.items():
        for item in export.get(key, []) or []:
            if not isinstance(item, dict):
                continue
            locator = str(item.get("url") or item.get("path") or "").strip()
            if not locator:
                continue
            method = str(item.get("method", "GET")).upper()
            label = f"{method} {locator}" if kind in {"route", "endpoint"} else locator
            records.append({
                "id": slug(f"{method}-{locator}", kind), "case_id": case_id, "snapshot_id": snapshot_id,
                "kind": kind, "label": label[:120], "status": "observed", "sensitivity": "internal",
                "confidence": {"level": "medium", "reason": "scrapling discovery"},
                "properties": {"method": method, "params": item.get("params", [])},
                "locators": [locator], "evidence_refs": [f"crawl:{locator}"],
            })
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="Scrapling JSON export")
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        export = json.loads(args.export.read_text(encoding="utf-8"))
        if not isinstance(export, dict):
            raise ValueError("export must be a JSON object with routes/forms/scripts/endpoints")
        records = normalize(export, str(case.get("case_id")), str(case.get("snapshot_id")))
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"scrapling normalize error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(records)} observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
