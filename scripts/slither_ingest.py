#!/usr/bin/env python3
"""Ingest Slither JSON or SARIF into Invariant Helix hypothesized leads.

Deterministic static findings become G5 starting points. They never set status to
verified. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:
    from security_utils import atomic_write_text

SLUG = re.compile(r"[^a-z0-9]+")

# detector id / rule id substring -> (lens, bug_class)
ROUTING: list[tuple[str, str, str]] = [
    ("reentrancy", "execution-trace", "reentrancy"),
    ("arbitrary-send", "access-control", "arbitrary-send"),
    ("controlled-delegatecall", "access-control", "controlled-delegatecall"),
    ("tx-origin", "access-control", "tx-origin-auth"),
    ("unchecked-transfer", "periphery-integration", "unchecked-erc20-return"),
    ("unchecked-lowlevel", "execution-trace", "unchecked-call-return"),
    ("divide-before-multiply", "math-precision", "precision-loss"),
    ("divide-before", "math-precision", "precision-loss"),
    ("locked-ether", "economic", "locked-funds"),
    ("suicidal", "access-control", "selfdestruct"),
    ("uninitialized-state", "invariant-state", "uninitialized-state"),
    ("uninitialized-storage", "invariant-state", "uninitialized-storage"),
    ("uninitialized-local", "boundary", "uninitialized-local"),
    ("shadowing", "trust-gap", "shadowing"),
    ("timestamp", "temporal-cohort", "timestamp-dependence"),
    ("weak-prng", "trust-gap", "weak-prng"),
    ("msg-value-loop", "economic", "msg-value-accounting"),
    ("erc20-interface", "periphery-integration", "erc20-interface"),
    ("incorrect-equality", "boundary", "incorrect-equality"),
    ("tautology", "first-principles", "tautology"),
    ("boolean-cst", "first-principles", "boolean-constant"),
    ("name-reused", "trust-gap", "name-reuse"),
    ("rtlo", "trust-gap", "rtlo"),
    ("assembly", "execution-trace", "inline-assembly"),
    ("low-level-calls", "execution-trace", "low-level-call"),
    ("naming-convention", "first-principles", "style"),  # usually informational
]


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def route(detector: str) -> tuple[str, str]:
    key = detector.lower().replace("_", "-")
    for needle, lens, bug in ROUTING:
        if needle in key:
            return lens, bug
    return "first-principles", "static-detector"


def _lead(
    *,
    case_id: str,
    snapshot_id: str,
    detector: str,
    message: str,
    file: str,
    line: int | None,
    severity: str,
) -> dict[str, Any]:
    lens, bug = route(detector)
    locator = f"{file}:{line}" if line else file
    return {
        "id": slug(f"{detector}-{file}-{line}-{message[:40]}", "hypothesis"),
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "kind": "hypothesis",
        "label": f"[slither:{detector}] {message[:100]}",
        "status": "hypothesized",
        "sensitivity": "public",
        "confidence": {
            "level": "medium" if severity.lower() in {"high", "critical", "error"} else "low",
            "reason": f"slither detector {detector}; unproven on this target",
        },
        "properties": {
            "source": "slither",
            "detector": detector,
            "file": file,
            "line": line,
            "severity_hint": severity,
            "lens": lens,
            "bug_class": bug,
            "message": message[:400],
        },
        "locators": [locator],
        "evidence_refs": [f"slither:{detector}:{locator}"],
    }


def from_slither_json(data: Any, case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    """Parse `slither . --json out.json` (results.detectors list)."""
    leads: list[dict[str, Any]] = []
    detectors = []
    if isinstance(data, dict):
        results = data.get("results") or data
        if isinstance(results, dict):
            detectors = results.get("detectors") or []
        elif isinstance(results, list):
            detectors = results
    if not isinstance(detectors, list):
        return leads
    for det in detectors:
        if not isinstance(det, dict):
            continue
        check = str(det.get("check") or det.get("id") or "unknown")
        message = str(det.get("description") or det.get("markdown") or check)
        severity = str(det.get("impact") or det.get("confidence") or "Medium")
        file, line = "", None
        for elem in det.get("elements") or []:
            if not isinstance(elem, dict):
                continue
            src = elem.get("source_mapping") or {}
            if isinstance(src, dict):
                file = str(src.get("filename_relative") or src.get("filename_short") or file)
                lines = src.get("lines") or []
                if isinstance(lines, list) and lines:
                    try:
                        line = int(lines[0])
                    except (TypeError, ValueError):
                        pass
            if file:
                break
        leads.append(_lead(
            case_id=case_id, snapshot_id=snapshot_id, detector=check,
            message=message.replace("\n", " ").strip(), file=file or "unknown",
            line=line, severity=severity,
        ))
    return leads


def from_sarif(data: Any, case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    """Parse SARIF 2.1.0 (slither --sarif)."""
    leads: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        return leads
    for run in data.get("runs") or []:
        if not isinstance(run, dict):
            continue
        rules = {}
        for rule in ((run.get("tool") or {}).get("driver") or {}).get("rules") or []:
            if isinstance(rule, dict) and rule.get("id"):
                rules[str(rule["id"])] = rule
        for result in run.get("results") or []:
            if not isinstance(result, dict):
                continue
            rule_id = str(result.get("ruleId") or "unknown")
            msg_obj = result.get("message") or {}
            message = str(msg_obj.get("text") if isinstance(msg_obj, dict) else msg_obj or rule_id)
            severity = str(result.get("level") or "warning")
            file, line = "unknown", None
            for loc in result.get("locations") or []:
                if not isinstance(loc, dict):
                    continue
                pl = (loc.get("physicalLocation") or {})
                art = (pl.get("artifactLocation") or {})
                reg = (pl.get("region") or {})
                file = str(art.get("uri") or file)
                if reg.get("startLine") is not None:
                    try:
                        line = int(reg["startLine"])
                    except (TypeError, ValueError):
                        pass
                break
            leads.append(_lead(
                case_id=case_id, snapshot_id=snapshot_id, detector=rule_id,
                message=message.replace("\n", " ").strip(), file=file, line=line,
                severity=severity,
            ))
    return leads


def ingest(path: Path, case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and data.get("version") and "runs" in data:
        return from_sarif(data, case_id, snapshot_id)
    if isinstance(data, dict) and ("$schema" in data or "runs" in data):
        return from_sarif(data, case_id, snapshot_id)
    return from_slither_json(data, case_id, snapshot_id)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="slither JSON or SARIF file")
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--output", required=True, type=Path, help="observations JSONL")
    parser.add_argument("--append", type=Path, help="existing JSONL to append to")
    args = parser.parse_args(argv)
    try:
        leads = ingest(args.input, args.case_id, args.snapshot_id)
        lines = [json.dumps(r, sort_keys=True) for r in leads]
        if args.append and args.append.is_file():
            existing = args.append.read_text(encoding="utf-8").rstrip()
            body = (existing + "\n" if existing else "") + "\n".join(lines) + ("\n" if lines else "")
            atomic_write_text(args.output, body)
        else:
            atomic_write_text(args.output, "\n".join(lines) + ("\n" if lines else ""))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"slither ingest error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output}: {len(leads)} slither lead(s) (hypothesized only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
