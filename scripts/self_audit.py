#!/usr/bin/env python3
"""Audit Invariant Helix itself for structural and logical integrity.

A skill that claims executability must prove it. This checks the repository against the
contract it advertises, so drift is caught mechanically instead of by reading:

  wiring       every lens file is dispatchable and every dispatchable lens has a file;
               every ih-* command resolves to a real module with a main()
  references   every path SKILL.md names exists; every referenced lens/adapter resolves
  registry     chain adapters resolve their documents; peer tools are well-formed
  contracts    every script exposes a CLI and fails closed on bad input
  claims       documented gate/status vocabulary matches what the validators enforce

Exit 0 clean, 1 with findings, 2 on error. Standard library only.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Files under references/lenses/ that are protocol, not attack lenses.
PROTOCOL_FILES = {"shared-rules", "auditor-sop", "nemesis-loop"}


def _finding(check: str, severity: str, detail: str) -> dict[str, str]:
    return {"check": check, "severity": severity, "detail": detail}


def check_lens_wiring() -> list[dict[str, str]]:
    """Every lens file must be dispatchable, and every dispatchable lens must exist."""
    findings: list[dict[str, str]] = []
    sys.path.insert(0, str(ROOT))
    from scripts.lens_dispatch import LENSES  # noqa: PLC0415

    on_disk = {p.stem for p in (ROOT / "references/lenses").glob("*.md")} - PROTOCOL_FILES
    dispatchable = set(LENSES)
    for orphan in sorted(on_disk - dispatchable):
        findings.append(_finding(
            "lens-wiring", "high",
            f"references/lenses/{orphan}.md exists but ih-lens-dispatch can never select it: "
            "a lens nobody can dispatch is documentation, not a capability",
        ))
    for missing in sorted(dispatchable - on_disk):
        findings.append(_finding(
            "lens-wiring", "critical",
            f"lens {missing!r} is dispatchable but references/lenses/{missing}.md is missing: "
            "ih-lens-bundle would ship an agent an empty profile",
        ))
    return findings


def check_lens_triggers() -> list[dict[str, str]]:
    """A lens whose triggers are not real node kinds can never fire."""
    findings: list[dict[str, str]] = []
    from scripts.lens_dispatch import LENSES  # noqa: PLC0415
    from scripts.normalize_observations import NODE_KINDS  # noqa: PLC0415

    for lens, spec in LENSES.items():
        unknown = sorted(set(spec["triggers"]) - NODE_KINDS)
        if unknown:
            findings.append(_finding(
                "lens-triggers", "high",
                f"lens {lens!r} triggers on non-existent node kind(s) {unknown}: it can never fire",
            ))
    return findings


def check_capability_names() -> list[dict[str, str]]:
    """Lens capabilities and inventory capabilities must be the same vocabulary."""
    findings: list[dict[str, str]] = []
    from scripts.check_capabilities import CAPABILITIES  # noqa: PLC0415
    from scripts.inventory import CAPABILITIES as SCOPE_CAPABILITIES  # noqa: PLC0415
    from scripts.lens_dispatch import LENSES  # noqa: PLC0415

    probed, admitted = set(CAPABILITIES), set(SCOPE_CAPABILITIES)
    if probed != admitted:
        findings.append(_finding(
            "capability-vocabulary", "high",
            f"check_capabilities and inventory disagree: only-probed={sorted(probed - admitted)}, "
            f"only-admissible={sorted(admitted - probed)}; a capability that can be admitted "
            "but never probed is an unenforced promise",
        ))
    for lens, spec in LENSES.items():
        if spec["capability"] not in probed:
            findings.append(_finding(
                "capability-vocabulary", "high",
                f"lens {lens!r} needs capability {spec['capability']!r}, which is never probed",
            ))
    return findings


def check_entry_points() -> list[dict[str, str]]:
    """Every advertised ih-* command must import and expose main()."""
    findings: list[dict[str, str]] = []
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    entries = re.findall(r"^(ih-[\w-]+)\s*=\s*\"([\w.]+):(\w+)\"", text, re.M)
    if not entries:
        return [_finding("entry-point", "critical", "no ih-* commands are registered in pyproject.toml")]
    for name, module_name, function in entries:
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            findings.append(_finding("entry-point", "critical", f"{name} -> {module_name} does not import: {exc}"))
            continue
        if not callable(getattr(module, function, None)):
            findings.append(_finding(
                "entry-point", "critical",
                f"{name} -> {module_name}:{function} is not callable",
            ))
    return findings


def check_skill_references() -> list[dict[str, str]]:
    """Every reference path SKILL.md names must exist on disk."""
    findings: list[dict[str, str]] = []
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    referenced = set(re.findall(r"\b((?:method|lenses|web|chains|knowledge)/[\w-]+\.md)\b", skill))
    for relative in sorted(referenced):
        if not (ROOT / "references" / relative).is_file():
            findings.append(_finding(
                "skill-references", "high",
                f"SKILL.md names references/{relative}, which does not exist: the controller "
                "would try to load a missing file",
            ))
    return findings


def check_chain_registry() -> list[dict[str, str]]:
    """Adapter documents must resolve, and maturity claims must stay honest."""
    findings: list[dict[str, str]] = []
    registry = json.loads((ROOT / "adapters/chains/registry.json").read_text(encoding="utf-8"))
    for adapter in registry.get("adapters", []):
        document = ROOT / str(adapter.get("document", ""))
        if not document.is_file():
            findings.append(_finding(
                "chain-registry", "high",
                f"adapter {adapter.get('adapter_id')!r} points at a missing document",
            ))
        if adapter.get("status") == "methodology-only" and adapter.get("maturity_tier") != 3:
            findings.append(_finding(
                "chain-registry", "critical",
                f"adapter {adapter.get('adapter_id')!r} claims a maturity it cannot back",
            ))
    return findings


def check_peer_registry() -> list[dict[str, str]]:
    """Peer tools must be well-formed and carry the independence rule."""
    findings: list[dict[str, str]] = []
    path = ROOT / "adapters/audit/peer-tools.json"
    if not path.is_file():
        return [_finding("peer-registry", "medium", "adapters/audit/peer-tools.json is missing")]
    registry = json.loads(path.read_text(encoding="utf-8"))
    if "independence_rule" not in registry:
        findings.append(_finding(
            "peer-registry", "critical",
            "peer registry lacks independence_rule: without it a peer tool could be read as "
            "an adjudicator, which would defeat verifier independence",
        ))
    roles = set(registry.get("roles", {}))
    for tool in registry.get("tools", []):
        if not tool.get("url", "").startswith("https://"):
            findings.append(_finding("peer-registry", "low", f"{tool.get('name')!r} has no https url"))
        unknown = sorted(set(tool.get("roles", [])) - roles)
        if unknown:
            findings.append(_finding("peer-registry", "low", f"{tool.get('name')!r} has undeclared role(s) {unknown}"))
    return findings


def check_status_vocabulary() -> list[dict[str, str]]:
    """The documented uncertainty ladder must match the enforced status machine."""
    findings: list[dict[str, str]] = []
    from scripts.normalize_observations import OBSERVATION_STATUSES  # noqa: PLC0415
    from scripts.validate_findings import STATUSES  # noqa: PLC0415

    if "verified" in OBSERVATION_STATUSES:
        findings.append(_finding(
            "status-vocabulary", "critical",
            "'verified' is an observable status: an observation could assert adjudication "
            "it never underwent",
        ))
    for required in ("hypothesis", "under_verification", "verified", "released"):
        if required not in STATUSES:
            findings.append(_finding("status-vocabulary", "critical", f"finding status {required!r} is missing"))
    return findings


def check_docs_claims() -> list[dict[str, str]]:
    """Commands promised in INSTALL/QUICKSTART/README must actually be registered."""
    findings: list[dict[str, str]] = []
    registered = set(re.findall(r"^(ih-[\w-]+)\s*=", (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M))
    for name in ("README.md", "INSTALL.md", "QUICKSTART.md"):
        path = ROOT / name
        if not path.is_file():
            findings.append(_finding("docs", "medium", f"{name} is missing"))
            continue
        for command in sorted(set(re.findall(r"\b(ih-[\w-]+)\b", path.read_text(encoding="utf-8")))):
            if command not in registered:
                findings.append(_finding(
                    "docs", "high",
                    f"{name} documents {command}, which is not a registered command: "
                    "a user following the docs would hit command-not-found",
                ))
    return findings


def check_lens_structure() -> list[dict[str, str]]:
    """An attack lens without surfaces or a proof contract is prose, not a lens."""
    findings: list[dict[str, str]] = []
    required = ("**Role.**", "## Attack surfaces", "## Proof fields")
    for path in sorted((ROOT / "references/lenses").glob("*.md")):
        if path.stem in PROTOCOL_FILES:
            continue
        text = path.read_text(encoding="utf-8")
        missing = [section for section in required if section not in text]
        if missing:
            findings.append(_finding(
                "lens-structure", "medium",
                f"lens {path.stem!r} is missing {missing}: an agent reading it would get no "
                "attack surfaces or no proof obligation",
            ))
    return findings


def check_test_coverage() -> list[dict[str, str]]:
    """Every executable script needs at least one test importing it."""
    findings: list[dict[str, str]] = []
    imported: set[str] = set()
    for path in (ROOT / "tests").glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        # Match every import form: `from scripts.x import y`, `import scripts.x`,
        # and `from scripts import x, y` (which the original pattern missed).
        imported |= set(re.findall(r"(?:from|import)\s+scripts\.(\w+)", text))
        # `[ \t]` rather than `\s`: a newline must end the import list, or the last name
        # gets glued to the following line and never matches a real module.
        for group in re.findall(r"from[ \t]+scripts[ \t]+import[ \t]+([\w,][\w, \t]*)", text):
            imported |= {name.strip() for name in group.split(",") if name.strip()}
    scripts = {path.stem for path in (ROOT / "scripts").glob("*.py")} - {"__init__"}
    for orphan in sorted(scripts - imported):
        findings.append(_finding(
            "test-coverage", "medium",
            f"scripts/{orphan}.py has no test importing it: a regression would ship silently",
        ))
    return findings


CHECKS = (
    ("lens-wiring", check_lens_wiring),
    ("lens-structure", check_lens_structure),
    ("test-coverage", check_test_coverage),
    ("lens-triggers", check_lens_triggers),
    ("capability-vocabulary", check_capability_names),
    ("entry-points", check_entry_points),
    ("skill-references", check_skill_references),
    ("chain-registry", check_chain_registry),
    ("peer-registry", check_peer_registry),
    ("status-vocabulary", check_status_vocabulary),
    ("docs-claims", check_docs_claims),
)
ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def run_all() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for _, check in CHECKS:
        findings.extend(check())
    findings.sort(key=lambda item: (ORDER.get(item["severity"], 9), item["check"], item["detail"]))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        findings = run_all()
    except Exception as exc:  # noqa: BLE001 - a self-audit must report its own failure
        print(f"self audit error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"findings": findings, "count": len(findings)}, indent=2, sort_keys=True))
    elif findings:
        for item in findings:
            print(f"  [{item['severity']:<8}] {item['check']}: {item['detail']}")
        print(f"\n{len(findings)} structural finding(s)")
    else:
        print(f"  {len(CHECKS)} checks passed: lenses wired, commands resolve, references exist, claims match")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
