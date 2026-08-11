#!/usr/bin/env python3
"""Merge lens outputs and promote leads — without ever setting a verified status.

Dedup + convergence for multi-lens output. Deliberately corrected so agreement
for Invariant Helix's anti-confirmation rule. Multi-lens agreement raises *priority*
and *confidence*; it NEVER sets a finding's status. Promoted leads enter at
``hypothesis`` and must still pass gate G8 falsification with an independent verifier.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


TERMINAL_OR_VERIFIED = {"verified", "released", "downgraded"}


def load_findings(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("findings")
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("input must be an array or an object with a findings array")
    return value


def converge(findings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Group by dedup_key, record convergence, raise confidence — never status."""
    errors: list[str] = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, finding in enumerate(findings):
        key = finding.get("dedup_key")
        if not isinstance(key, str) or not key.strip():
            errors.append(f"finding[{index}] missing dedup_key; cannot converge")
            continue
        groups[key].append(finding)

    merged: list[dict[str, Any]] = []
    for key in sorted(groups):
        members = groups[key]
        lenses = sorted({str(m.get("lens")) for m in members if m.get("lens")})
        # Preserve materially different mechanisms as supporting evidence.
        mechanisms = sorted({str(m.get("root_cause", "")).strip() for m in members if m.get("root_cause")})
        primary = dict(members[0])
        agreement = len(lenses)
        primary["convergence"] = {
            "lenses": lenses,
            "agreement": agreement,
            "distinct_mechanisms": mechanisms,
            "shared_premise": len(mechanisms) <= 1 and agreement > 1,
            "note": "convergence sets priority/confidence only; status stays a hypothesis until G8",
        }
        # Lead promotion: multi-lens agreement OR a completed reachable path raises priority.
        promoted = agreement >= 2
        primary["priority"] = "elevated" if promoted else "normal"
        if promoted and isinstance(primary.get("confidence"), dict):
            # raise confidence one notch, capped at high; convergence with a shared premise
            # is not independent, so it may not reach high on its own.
            level = str(primary["confidence"].get("level", "low"))
            independent = not primary["convergence"]["shared_premise"]
            bump = {"low": "medium", "medium": "high" if independent else "medium", "high": "high"}
            primary["confidence"] = {
                "level": bump.get(level, level),
                "reason": f"{primary['confidence'].get('reason', '')}; converged across {agreement} lenses "
                          f"({'independent' if independent else 'shared-premise'})".strip("; "),
            }
        # Hard guard: convergence must never imply verification.
        if str(primary.get("status", "hypothesis")).lower() in TERMINAL_OR_VERIFIED:
            errors.append(
                f"dedup_key {key!r}: convergence output must remain a hypothesis, found status="
                f"{primary.get('status')}"
            )
        else:
            primary["status"] = "hypothesis"
        merged.append(primary)
    merged.sort(key=lambda item: (item.get("priority") != "elevated", str(item.get("dedup_key"))))
    return merged, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        findings = load_findings(args.findings)
        merged, errors = converge(findings)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        payload = {"findings": merged}
        if args.output:
            atomic_write_text(args.output, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"convergence error: {exc}", file=sys.stderr)
        return 2
    elevated = sum(1 for item in merged if item.get("priority") == "elevated")
    print(f"converged {len(findings)} finding(s) into {len(merged)} group(s); {elevated} elevated (still hypotheses)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
