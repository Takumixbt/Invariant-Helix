#!/usr/bin/env python3
"""X-ray enumeration: detect the chain family, measure the codebase, extract entry
points, and emit Invariant Helix observations JSONL.

Feeds gate G2/G3: pipe the output through ``normalize_observations`` to build the
case/snapshot-scoped graph. Chain family and entry-point patterns come from
``adapters/chains/registry.json`` so the same code works across every family, not just
EVM. Standard library only.
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


# family -> (node kind for a source unit, source extensions, entry-pattern language key)
FAMILY_PROFILE = {
    "evm": ("contract", (".sol", ".vy"), "solidity"),
    "solana": ("program", (".rs",), "rust"),
    "cosmwasm": ("contract", (".rs",), "rust"),
    "move": ("module", (".move",), "move"),
    "starknet": ("contract", (".cairo",), "cairo"),
}
CONFIG_HINTS = {
    "foundry.toml": "evm", "hardhat.config.js": "evm", "hardhat.config.ts": "evm",
    "remappings.txt": "evm", "anchor.toml": "solana", "move.toml": "move",
    "scarb.toml": "starknet",
}
SLUG = re.compile(r"[^a-z0-9]+")


def posix_to_python(pattern: str) -> str:
    """Translate the POSIX-ERE classes used in the registry to Python re equivalents."""
    return (
        pattern.replace("[:alnum:]", "A-Za-z0-9")
        .replace("[:alpha:]", "A-Za-z")
        .replace("[:digit:]", "0-9")
        .replace("[:space:]", r"\s")
        .replace("[:upper:]", "A-Z")
        .replace("[:lower:]", "a-z")
    )


def slug(text: str, prefix: str) -> str:
    body = SLUG.sub("-", text.lower()).strip("-")[:100] or "x"
    ident = f"{prefix}:{body}"
    return ident[:128]


def detect_family(root: Path, registry: dict[str, Any]) -> str:
    families = {a["chain_family"] for a in registry.get("adapters", []) if isinstance(a, dict)}
    scores: dict[str, int] = {family: 0 for family in families}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name in CONFIG_HINTS and CONFIG_HINTS[name] in scores:
            scores[CONFIG_HINTS[name]] += 5
        suffix = path.suffix.lower()
        for family, (_, exts, _) in FAMILY_PROFILE.items():
            if suffix in exts and family in scores:
                scores[family] += 1
        # Cargo.toml with anchor/solana markers biases toward solana over cosmwasm.
        if name == "cargo.toml":
            try:
                text = path.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                text = ""
            if "anchor" in text or "solana" in text:
                scores["solana"] = scores.get("solana", 0) + 3
            if "cosmwasm" in text or "cw-storage" in text:
                scores["cosmwasm"] = scores.get("cosmwasm", 0) + 3
    best = max(scores.items(), key=lambda kv: kv[1]) if scores else ("generic-rpc", 0)
    return best[0] if best[1] > 0 else "generic-rpc"


def entry_patterns(registry: dict[str, Any], family: str, language: str) -> list[re.Pattern[str]]:
    for adapter in registry.get("adapters", []):
        if isinstance(adapter, dict) and adapter.get("chain_family") == family:
            raw = (adapter.get("entry_point_patterns") or {}).get(language, [])
            return [re.compile(posix_to_python(pattern)) for pattern in raw]
    return []


def source_files(root: Path, exts: tuple[str, ...]) -> list[Path]:
    skip = {"test", "tests", "lib", "node_modules", "target", "out", ".git", "mock", "mocks", "interfaces"}
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in exts:
            continue
        if any(part.lower() in skip for part in path.relative_to(root).parts[:-1]):
            continue
        files.append(path)
    return files


def nsloc(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip() and not line.strip().startswith(("//", "#", "*")))


def enumerate_codebase(root: Path, registry: dict[str, Any], case_id: str, snapshot_id: str) -> list[dict[str, Any]]:
    family = detect_family(root, registry)
    unit_kind, exts, language = FAMILY_PROFILE.get(family, ("component", (".txt",), ""))
    patterns = entry_patterns(registry, family, language)
    files = source_files(root, exts)
    total_nsloc = 0
    records: list[dict[str, Any]] = []
    component_id = slug(root.name or "codebase", "component")
    unit_edges: list[dict[str, Any]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        total_nsloc += nsloc(text)
        rel = str(path.relative_to(root))
        unit_id = slug(rel, unit_kind)
        entry_edges: list[dict[str, Any]] = []
        seen: set[str] = set()
        for number, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                label = line.strip()[:120]
                entry_id = slug(f"{rel}-{number}-{label}", "entrypoint")
                if entry_id in seen:
                    continue
                seen.add(entry_id)
                records.append({
                    "id": entry_id, "case_id": case_id, "snapshot_id": snapshot_id,
                    "kind": "entrypoint", "label": label, "status": "observed",
                    "sensitivity": "public",
                    "confidence": {"level": "high", "reason": "entry-point pattern match"},
                    "properties": {"file": rel, "line": number, "chain_family": family},
                    "locators": [f"{rel}:{number}"], "evidence_refs": [f"source:{rel}:{number}"],
                })
                entry_edges.append({"relation": "contains", "to": entry_id, "status": "observed",
                                    "locator": f"{rel}:{number}",
                                    "evidence_refs": [f"source:{rel}:{number}"]})
        records.append({
            "id": unit_id, "case_id": case_id, "snapshot_id": snapshot_id,
            "kind": unit_kind, "label": path.name, "status": "observed", "sensitivity": "public",
            "confidence": {"level": "high", "reason": "source file enumerated"},
            "properties": {"path": rel, "chain_family": family, "entry_points": len(entry_edges)},
            "locators": [rel], "evidence_refs": [f"source:{rel}"], "edges": entry_edges,
        })
        unit_edges.append({"relation": "contains", "to": unit_id, "status": "observed",
                           "locator": rel, "evidence_refs": [f"source:{rel}"]})
    component = {
        "id": component_id, "case_id": case_id, "snapshot_id": snapshot_id,
        "kind": "component", "label": root.name or "codebase", "status": "observed",
        "sensitivity": "public",
        "confidence": {"level": "high", "reason": "x-ray enumeration"},
        "properties": {"chain_family": family, "source_files": len(files), "nsloc": total_nsloc},
        "locators": ["scope:root"], "evidence_refs": [f"source:{root.name or 'root'}"],
        "edges": unit_edges,
    }
    return [component, *records]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, type=Path, help="case manifest for case/snapshot ids")
    parser.add_argument("--root", required=True, type=Path, help="source tree to enumerate")
    parser.add_argument("--registry", type=Path, default=Path("adapters/chains/registry.json"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        if not args.root.is_dir():
            raise ValueError(f"source root not found: {args.root}")
        records = enumerate_codebase(
            args.root, registry, str(case.get("case_id")), str(case.get("snapshot_id"))
        )
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, re.error) as exc:
        print(f"xray enumeration error: {exc}", file=sys.stderr)
        return 2
    family = records[0]["properties"]["chain_family"] if records else "unknown"
    print(f"wrote {args.output} ({len(records)} observations, chain_family={family})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
