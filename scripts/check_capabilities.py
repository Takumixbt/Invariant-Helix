#!/usr/bin/env python3
"""Probe the local machine for audit tooling and map it to Invariant Helix capabilities.

Turns the prose in ``references/method/requirements.md`` into an enforced gate: it
reports which of the 13 capability names are backed by an installed tool and emits
well-formed blocked coverage items for the rest, so a missing tool becomes coverage
debt instead of a silent gap. Standard library only; no tool is executed, only
located on ``PATH``.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import shutil
import sys
import sysconfig
from pathlib import Path
from typing import Any

try:
    from .inventory import load_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from inventory import load_scope
    from security_utils import atomic_write_text


# Each capability is satisfied when it is bundled with Invariant Helix, or when any
# one of its candidate external tools is present on PATH.
CAPABILITIES: dict[str, dict[str, Any]] = {
    "surface_inventory": {"bundled": False, "tools": ["nmap", "amass", "httpx", "gobuster", "scrapling"]},
    "http_crawl": {"bundled": False, "tools": ["scrapling", "ffuf", "gobuster", "httpx"]},
    "browser_workflow": {"bundled": False, "tools": ["chromium", "chromium-browser", "playwright", "scrapling"]},
    "proxy_observation": {"bundled": False, "tools": ["burpsuite", "mitmdump", "zap"]},
    "request_replay": {"bundled": False, "tools": ["curl", "httpx", "wget"]},
    "input_mutation": {"bundled": False, "tools": ["ffuf", "wfuzz", "sqlmap"]},
    "synchronized_requests": {"bundled": True, "tools": []},  # scripts/race_runner.py
    "oob_observation": {"bundled": False, "tools": ["interactsh-client", "burpsuite"]},
    "source_analysis": {"bundled": True, "tools": ["slither", "semgrep", "cargo", "solc"]},
    "chain_simulation": {"bundled": False, "tools": ["anvil", "forge", "solana-test-validator", "npx"]},
    "execution_trace": {"bundled": False, "tools": ["cast", "forge", "anvil"]},
    "property_fuzzing": {"bundled": False, "tools": ["echidna", "medusa", "halmos", "forge", "certoraRun"]},
    "evidence_manifest": {"bundled": True, "tools": []},  # scripts/evidence_manifest.py
}


def _is_python_httpx_entrypoint(path: str) -> bool:
    """Reject Python HTTPX when a capability needs ProjectDiscovery httpx.

    Both tools install an executable named ``httpx`` on Windows.  The Python
    client can issue one request, but it does not emit the ``httpx -json``
    reconnaissance format consumed by the recon adapter.  Treating a filename
    match as sufficient would silently create false coverage.
    """

    try:
        executable = Path(path).resolve()
        scripts_dir = Path(sysconfig.get_path("scripts")).resolve()
        if executable.parent != scripts_dir:
            return False
        distribution = importlib.metadata.distribution("httpx")
    except (OSError, TypeError, importlib.metadata.PackageNotFoundError):
        return False
    return any(
        entry.name == "httpx"
        and str(entry.value).lower().startswith("httpx:")
        for entry in distribution.entry_points
        if entry.group == "console_scripts"
    )


def _tool_path(tool: str, *, needs_recon_httpx: bool = False) -> str | None:
    path = shutil.which(tool)
    if not path:
        return None
    if needs_recon_httpx and tool == "httpx" and _is_python_httpx_entrypoint(path):
        return None
    return path


def probe(capabilities: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    capabilities = capabilities or CAPABILITIES
    report: dict[str, Any] = {}
    for name, spec in capabilities.items():
        present = [
            tool for tool in spec["tools"]
            if _tool_path(tool, needs_recon_httpx=name in {"surface_inventory", "http_crawl"})
        ]
        bundled = bool(spec["bundled"])
        report[name] = {
            "available": bundled or bool(present),
            "bundled": bundled,
            "installed_tools": present,
            "candidate_tools": list(spec["tools"]),
        }
    return report


def peer_tools(language: str | None = None, role: str | None = None) -> list[dict[str, Any]]:
    """Peer audit tools that can supply a capability Invariant Helix lacks.

    Distilled from the Web3 Security Tools Hub. A peer tool generates hypotheses; it never
    adjudicates (see `independence_rule` in the registry).
    """
    registry_path = Path(__file__).resolve().parents[1] / "adapters/audit/peer-tools.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tools = [tool for tool in registry.get("tools", []) if isinstance(tool, dict)]
    if language:
        tools = [t for t in tools if language in t.get("languages", []) or "multi" in t.get("languages", [])]
    if role:
        tools = [t for t in tools if role in t.get("roles", [])]
    return tools


def blocked_coverage_items(
    report: dict[str, Any],
    *,
    case_id: str,
    snapshot_id: str,
    requested: list[str] | None = None,
    owner: str = "capability-planner",
    verifier: str = "independent-capability-verifier",
    language: str | None = None,
) -> list[dict[str, Any]]:
    """Produce a blocked coverage item for every requested-but-unavailable capability.

    Each item names the exact next requirement: the local tools that would supply the
    capability, plus peer skills for the target language when one applies.
    """
    wanted = set(requested) if requested else set(report)
    role_for = {"property_fuzzing": "fuzzer", "source_analysis": "auditor"}
    items: list[dict[str, Any]] = []
    for name in sorted(wanted):
        detail = report.get(name)
        if detail is None or detail["available"]:
            continue
        candidates = ", ".join(detail["candidate_tools"]) or "an external harness"
        peers = peer_tools(language, role_for.get(name)) if language else []
        if peers:
            candidates += "; peer skills: " + ", ".join(t["name"] for t in peers[:3])
        items.append(
            {
                "coverage_id": f"coverage:capability-{name.replace('_', '-')}",
                "case_id": case_id,
                "snapshot_id": snapshot_id,
                "target_refs": [f"scope:capability:{name}"],
                "impact_class": "medium",
                "owner": owner,
                "hypothesis_families": [f"paths requiring {name}"],
                "planned_observations": [f"exercise {name} once a backing tool is installed"],
                "negative_controls": ["confirm the capability is genuinely absent, not merely misconfigured"],
                "verifier_id": verifier,
                "status": "blocked",
                "evidence_refs": [],
                "dependencies": [],
                "blocker": f"no tool on PATH supplies {name}; install one of: {candidates}",
            }
        )
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-manifest", type=Path, help="bind emitted coverage to this case/snapshot")
    parser.add_argument("--emit-blocked-coverage", type=Path, help="write blocked coverage items here")
    parser.add_argument("--language", help="target language, to name peer skills for blocked capabilities")
    parser.add_argument("--json", action="store_true", help="print the full capability report as JSON")
    args = parser.parse_args(argv)
    try:
        report = probe()
        case_id = "unbound-case"
        snapshot_id = "unbound-snapshot"
        requested: list[str] | None = None
        if args.case_manifest:
            case = load_scope(args.case_manifest)
            case_id = str(case.get("case_id", case_id))
            snapshot_id = str(case.get("snapshot_id", snapshot_id))
            allowed = case.get("allowed_capabilities")
            if isinstance(allowed, list) and allowed:
                requested = [str(item) for item in allowed]
        items = blocked_coverage_items(
            report, case_id=case_id, snapshot_id=snapshot_id, requested=requested,
            language=args.language,
        )
        if args.emit_blocked_coverage:
            payload = {
                "schema_version": "1.0",
                "case_id": case_id,
                "snapshot_id": snapshot_id,
                "blocked_coverage_items": items,
            }
            atomic_write_text(args.emit_blocked_coverage, json.dumps(payload, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"capability check error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name in sorted(report):
            detail = report[name]
            mark = "ok  " if detail["available"] else "MISS"
            backing = "bundled" if detail["bundled"] else (", ".join(detail["installed_tools"]) or "-")
            print(f"  [{mark}] {name:<22} {backing}")
        blocked = [name for name in sorted(report) if not report[name]["available"]]
        print(f"\n{len(report) - len(blocked)}/{len(report)} capabilities available; blocked: {', '.join(blocked) or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
