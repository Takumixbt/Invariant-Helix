#!/usr/bin/env python3
"""Generate a Foundry fork/unit PoC scaffold from an IH finding JSON.

The scaffold is a G6 work product: it does not prove the bug. Fill in addresses,
calldata, and asserts; run with forge test. Standard library only.
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

SAFE = re.compile(r"[^A-Za-z0-9_]+")


def _load_finding(path: Path, finding_id: str | None) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "findings" in data:
        items = data["findings"]
    elif isinstance(data, dict) and "finding_id" in data:
        items = [data]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("expected a finding object, array, or {findings: [...]}")
    if not items:
        raise ValueError("no findings in input")
    if finding_id:
        for item in items:
            if isinstance(item, dict) and item.get("finding_id") == finding_id:
                return item
        raise ValueError(f"finding_id not found: {finding_id}")
    first = items[0]
    if not isinstance(first, dict):
        raise ValueError("finding must be an object")
    return first


def scaffold(finding: dict[str, Any], *, fork_url_env: str = "ETH_RPC_URL") -> str:
    fid = str(finding.get("finding_id") or "FINDING")
    title = str(finding.get("title") or fid)
    class_name = "PoC_" + SAFE.sub("_", fid)[:48].strip("_") or "PoC_Finding"
    if class_name[0].isdigit():
        class_name = "PoC_" + class_name
    triggers = finding.get("minimal_trigger_sequence") or []
    if isinstance(triggers, list):
        trigger_lines = "\n".join(f"    // {i + 1}. {t}" for i, t in enumerate(triggers))
    else:
        trigger_lines = f"    // {triggers}"
    path = finding.get("reachable_path") or []
    path_comment = " -> ".join(str(p) for p in path) if isinstance(path, list) else str(path)
    root = str(finding.get("root_cause") or "")[:200]
    claim = str(finding.get("security_claim") or "")[:200]
    severity = str(finding.get("severity") or "unknown")
    components = finding.get("affected_components") or []
    comp = ", ".join(str(c) for c in components) if isinstance(components, list) else str(components)

    return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {{Test, console2}} from "forge-std/Test.sol";

/// @title {class_name}
/// @notice Auto-generated IH scaffold for {fid} — fill in and prove, do not treat as verified.
/// @dev Severity hint: {severity}
/// Title: {title.replace('"', "'")}
contract {class_name} is Test {{
    // --- configure ---
    address internal constant VICTIM = address(0xBEEF);
    address internal constant ATTACKER = address(0xA11CE);
    // address internal target; // set to protocol entry

    function setUp() public {{
        // vm.createSelectFork(vm.envString("{fork_url_env}"));
        // deal(ATTACKER, 100 ether);
        // target = <deploy or attach>;
    }}

    /// @dev Reproduces: {path_comment.replace('"', "'")}
    function test_poc_{SAFE.sub('_', fid)[:40].strip('_') or 'finding'}() public {{
        vm.startPrank(ATTACKER);

        // Root cause (from finding): {root.replace('"', "'")}
        // Claim: {claim.replace('"', "'")}
        // Components: {comp.replace('"', "'")}

        // Minimal trigger sequence from the finding:
{trigger_lines if trigger_lines.strip() else "    // (none listed — reconstruct from reachable_path)"}

        // TODO: execute the call sequence
        // TODO: assert the invariant break (balances, shares, roles, etc.)
        // assertTrue(false, "PoC not yet implemented");

        vm.stopPrank();
    }}

    function test_negative_control_should_not_break() public {{
        // Strongest negative control from falsification_result.disproof_criteria
        // Leave failing until you know the control path is clean.
    }}
}}
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings", type=Path, help="finding JSON (object or findings array)")
    parser.add_argument("--finding-id", help="pick one finding when input has many")
    parser.add_argument("--output", type=Path, help="default: test/PoC_<id>.t.sol")
    parser.add_argument("--fork-env", default="ETH_RPC_URL")
    args = parser.parse_args(argv)
    try:
        finding = _load_finding(args.findings, args.finding_id)
        body = scaffold(finding, fork_url_env=args.fork_env)
        fid = SAFE.sub("_", str(finding.get("finding_id") or "FINDING"))[:48]
        out = args.output or Path("test") / f"PoC_{fid}.t.sol"
        atomic_write_text(out, body)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"poc error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {out}")
    print("Fill addresses/asserts, then: forge test --match-contract PoC_ -vvv")
    print("Scaffold is not proof. Hash the file into the evidence manifest when used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
