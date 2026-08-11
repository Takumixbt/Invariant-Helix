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
SAFE_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _comment(value: Any, limit: int = 240) -> str:
    """Make untrusted finding text stay data inside a Solidity line comment."""

    text = str(value if value is not None else "")
    escaped: list[str] = []
    for char in text:
        codepoint = ord(char)
        if char == "\r":
            escaped.append(r"\r")
        elif char == "\n":
            escaped.append(r"\n")
        elif codepoint < 0x20 or codepoint == 0x7F:
            escaped.append(f"\\x{codepoint:02x}")
        else:
            escaped.append(char)
    return "".join(escaped)[:limit]


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
    if not isinstance(fork_url_env, str) or not SAFE_ENV.fullmatch(fork_url_env):
        raise ValueError("fork_url_env must be a valid environment variable name")
    fid = str(finding.get("finding_id") or "FINDING")
    title = _comment(finding.get("title") or fid)
    safe_fid = SAFE.sub("_", fid)[:48].strip("_") or "Finding"
    class_name = "PoC_" + safe_fid
    if class_name[0].isdigit():
        class_name = "PoC_" + class_name
    triggers = finding.get("minimal_trigger_sequence") or []
    if isinstance(triggers, list):
        trigger_lines = "\n".join(f"    // {i + 1}. {_comment(t)}" for i, t in enumerate(triggers))
    else:
        trigger_lines = f"    // {_comment(triggers)}"
    path = finding.get("reachable_path") or []
    path_comment = " -> ".join(_comment(p, 120) for p in path) if isinstance(path, list) else _comment(path)
    root = _comment(finding.get("root_cause") or "")
    claim = _comment(finding.get("security_claim") or "")
    severity = _comment(finding.get("severity") or "unknown", 80)
    components = finding.get("affected_components") or []
    comp = ", ".join(_comment(c, 120) for c in components) if isinstance(components, list) else _comment(components)

    return f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {{Test, console2}} from "forge-std/Test.sol";

/// @title {_comment(class_name, 80)}
/// @notice Auto-generated IH scaffold for {_comment(fid, 120)} — fill in and prove, do not treat as verified.
/// @dev Severity hint: {severity}
/// Title: {title}
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

        // Root cause (from finding): {root}
        // Claim: {claim}
        // Components: {comp}

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
