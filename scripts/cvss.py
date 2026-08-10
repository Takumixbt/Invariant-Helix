#!/usr/bin/env python3
"""Build, validate, and score CVSS 3.1 base vectors for finding release.

Pure standard library. Implements the CVSS 3.1 base-score specification exactly,
including the specified roundup, so a finding's declared severity band can be
checked against its vector by ``validate_findings``.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

METRICS: dict[str, dict[str, float]] = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "UI": {"N": 0.85, "R": 0.62},
    "C": {"H": 0.56, "L": 0.22, "N": 0.0},
    "I": {"H": 0.56, "L": 0.22, "N": 0.0},
    "A": {"H": 0.56, "L": 0.22, "N": 0.0},
}
# Privileges Required is scope-dependent.
PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.5}
SCOPE = {"U", "C"}
ORDER = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")


def roundup(value: float) -> float:
    """CVSS 3.1 specified roundup: round up to the nearest 0.1 with integer math."""
    integer = round(value * 100000)
    if integer % 10000 == 0:
        return integer / 100000.0
    return (math.floor(integer / 10000) + 1) / 10.0


def severity_band(score: float) -> str:
    if score <= 0.0:
        return "None"
    if score < 4.0:
        return "Low"
    if score < 7.0:
        return "Medium"
    if score < 9.0:
        return "High"
    return "Critical"


# Map a CVSS severity band to the Invariant Helix finding severity enum.
BAND_TO_SEVERITY = {
    "None": "informational",
    "Low": "low",
    "Medium": "medium",
    "High": "high",
    "Critical": "critical",
}


def parse_vector(vector: str) -> dict[str, str]:
    if not isinstance(vector, str) or not vector.strip():
        raise ValueError("vector must be a non-empty string")
    parts = vector.strip().split("/")
    if not parts or parts[0] != "CVSS:3.1":
        raise ValueError("vector must start with the CVSS:3.1 prefix")
    metrics: dict[str, str] = {}
    for part in parts[1:]:
        if ":" not in part:
            raise ValueError(f"malformed metric segment: {part!r}")
        key, _, value = part.partition(":")
        if key in metrics:
            raise ValueError(f"duplicate metric: {key}")
        metrics[key] = value
    required = set(ORDER)
    present = set(metrics)
    if present != required:
        missing = ", ".join(sorted(required - present)) or "none"
        extra = ", ".join(sorted(present - required)) or "none"
        raise ValueError(f"base vector must define exactly {ORDER}; missing: {missing}; unexpected: {extra}")
    if metrics["S"] not in SCOPE:
        raise ValueError("S must be U or C")
    for key in ("AV", "AC", "UI", "C", "I", "A"):
        if metrics[key] not in METRICS[key]:
            raise ValueError(f"{key} value {metrics[key]!r} is invalid")
    pr_table = PR_CHANGED if metrics["S"] == "C" else PR_UNCHANGED
    if metrics["PR"] not in pr_table:
        raise ValueError(f"PR value {metrics['PR']!r} is invalid")
    return metrics


def base_score(vector: str) -> dict[str, Any]:
    metrics = parse_vector(vector)
    scope_changed = metrics["S"] == "C"
    pr_table = PR_CHANGED if scope_changed else PR_UNCHANGED
    iss = 1 - (
        (1 - METRICS["C"][metrics["C"]])
        * (1 - METRICS["I"][metrics["I"]])
        * (1 - METRICS["A"][metrics["A"]])
    )
    if scope_changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    else:
        impact = 6.42 * iss
    exploitability = (
        8.22
        * METRICS["AV"][metrics["AV"]]
        * METRICS["AC"][metrics["AC"]]
        * pr_table[metrics["PR"]]
        * METRICS["UI"][metrics["UI"]]
    )
    if impact <= 0:
        score = 0.0
    elif scope_changed:
        score = roundup(min(1.08 * (impact + exploitability), 10))
    else:
        score = roundup(min(impact + exploitability, 10))
    band = severity_band(score)
    canonical = "CVSS:3.1/" + "/".join(f"{key}:{metrics[key]}" for key in ORDER)
    return {
        "vector": canonical,
        "base_score": score,
        "severity_band": band,
        "ih_severity": BAND_TO_SEVERITY[band],
        "metrics": metrics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vector", help="a CVSS 3.1 base vector string")
    parser.add_argument("--json", action="store_true", help="emit the full scoring object as JSON")
    args = parser.parse_args(argv)
    try:
        result = base_score(args.vector)
    except (ValueError, TypeError) as exc:
        print(f"cvss error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"{result['base_score']:.1f} {result['severity_band']} ({result['ih_severity']})")
        print(result["vector"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
