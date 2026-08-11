#!/usr/bin/env python3
"""Static analysis of Solidity sources into Invariant Helix observations and leads.

This is the sharp end of the contract branch. Rather than describing how to hunt, it
extracts the facts the lenses need and flags concrete high-signal patterns:

  facts    state variables, functions (visibility/mutability/modifiers), guards,
           external calls, storage delta writes
  leads    CEI violations (state write after an external call), unprotected
           state-changing entry points, unguarded initializers, unchecked call
           returns, division-before-multiplication, tx.origin auth, unbounded loops
           over dynamic arrays, and missing zero-address checks on address setters

Every lead is emitted as a ``hypothesized`` observation with a file:line locator -- a
starting point a lens must prove and a verifier must falsify, never a finding. This is a
lexical analyzer, not a compiler: it is deliberately aggressive (favouring recall) and
its output is explicitly labelled as unproven. Standard library only.
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
COMMENT = re.compile(r"//.*?$|/\*.*?\*/", re.S | re.M)
CONTRACT = re.compile(r"\b(contract|library|interface|abstract\s+contract)\s+(\w+)")
FUNCTION = re.compile(
    r"\bfunction\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*(?P<attrs>[^{;]*)",
    re.S,
)
CONSTRUCTOR = re.compile(r"\bconstructor\s*\((?P<params>[^)]*)\)\s*(?P<attrs>[^{;]*)", re.S)
VISIBILITY = re.compile(r"\b(external|public|internal|private)\b")
MUTABILITY = re.compile(r"\b(view|pure|payable)\b")
MODIFIER = re.compile(r"\b(only\w+|nonReentrant|initializer|reinitializer|whenNotPaused|whenPaused)\b")
STATE_VAR = re.compile(
    r"^\s*(?P<type>(?:mapping\s*\([^;]*?\)|address|uint\d*|int\d*|bool|bytes\d*|string|"
    r"[A-Z]\w*)(?:\s*\[\s*\])*)\s+(?P<vis>public|private|internal\s+)?\s*"
    r"(?P<mods>constant\s+|immutable\s+)?(?P<name>\w+)\s*(?:=[^;]*)?;",
    re.M,
)
GUARD = re.compile(r"\b(require|assert)\s*\(([^;]*?)\)\s*;", re.S)
IF_REVERT = re.compile(r"\bif\s*\(([^)]*)\)\s*(?:\{\s*)?revert\b")
EXTERNAL_CALL = re.compile(
    r"(\.call\s*\{|\.call\s*\(|\.delegatecall\s*\(|\.staticcall\s*\(|"
    r"\.transfer\s*\(|\.send\s*\(|\.safeTransfer\w*\s*\(|\.transferFrom\s*\(|"
    r"\.onERC721Received\s*\(|\.onERC1155Received\s*\()"
)
DELTA_WRITE = re.compile(r"(\w+(?:\[[^\]]*\])*)\s*(\+=|-=)\s*([^;]+);")
PLAIN_WRITE = re.compile(r"^\s*(\w+)(\[[^\]]*\])*\s*=\s*[^=][^;]*;", re.M)
SENDER_CHECK = re.compile(r"msg\.sender\s*[=!]=|==\s*msg\.sender|_checkOwner|_checkRole")
TX_ORIGIN = re.compile(r"\btx\.origin\b")
DIV_THEN_MUL = re.compile(r"/\s*[\w.\[\]()]+\s*\*")
LOOP_OVER_DYNAMIC = re.compile(r"for\s*\([^;]*;\s*\w+\s*<\s*(\w+)\.length\s*;")
ADDRESS_PARAM = re.compile(r"\baddress\s+(?:calldata\s+|memory\s+)?(\w+)")
ZERO_CHECK = re.compile(r"!=\s*address\s*\(\s*0\s*\)|address\s*\(\s*0\s*\)\s*!=")


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def strip_comments(source: str) -> str:
    """Blank out comments while preserving line numbers so locators stay accurate."""
    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return COMMENT.sub(blank, source)


def line_of(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def function_bodies(source: str) -> list[dict[str, Any]]:
    """Extract functions with their brace-matched bodies, attributes, and line numbers."""
    results: list[dict[str, Any]] = []
    candidates = [(m, m.group("name")) for m in FUNCTION.finditer(source)]
    candidates += [(m, "constructor") for m in CONSTRUCTOR.finditer(source)]
    for match, name in candidates:
        brace = source.find("{", match.end() - 1)
        semicolon = source.find(";", match.end() - 1)
        if brace == -1:
            continue  # no body anywhere after this declaration
        if semicolon != -1 and semicolon < brace:
            # Declaration terminated by ';' (interface / abstract / modifier-less stub).
            # Without this guard the search would latch onto the NEXT contract's brace
            # and attribute an unrelated body to this signature.
            continue
        depth, index = 0, brace
        while index < len(source):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        attrs = match.groupdict().get("attrs", "") or ""
        results.append({
            "name": name,
            "params": match.groupdict().get("params", "") or "",
            "visibility": (VISIBILITY.search(attrs).group(1) if VISIBILITY.search(attrs) else
                           ("public" if name == "constructor" else "internal")),
            "mutability": sorted({m.group(1) for m in MUTABILITY.finditer(attrs)}),
            "modifiers": sorted({m.group(1) for m in MODIFIER.finditer(attrs)}),
            "body": source[brace:index + 1],
            "body_offset": brace,
            "line": line_of(source, match.start()),
        })
    return results


def _lead(kind_id: str, label: str, locator: str, properties: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "id": slug(kind_id, "hypothesis"), "kind": "hypothesis", "label": label[:120],
        "status": "hypothesized", "sensitivity": "public",
        "confidence": {"level": "low", "reason": f"{reason}; lexical analysis, unproven"},
        "properties": properties, "locators": [locator], "evidence_refs": [f"source:{locator}"],
    }


def analyze_source(source: str, rel: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (fact observations, lead observations) for one Solidity file."""
    clean = strip_comments(source)
    facts: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []

    state_vars: dict[str, str] = {}
    for match in STATE_VAR.finditer(clean):
        # Skip declarations that are actually inside a function body (locals).
        name, vartype = match.group("name"), " ".join(match.group("type").split())
        if name in {"return", "returns", "memory", "storage", "calldata"}:
            continue
        if (match.group("mods") or "").strip():
            continue  # constant/immutable are not mutable state
        state_vars[name] = vartype
        line = line_of(clean, match.start())
        facts.append({
            "id": slug(f"{rel}-{name}", "state"), "kind": "state", "label": f"{vartype} {name}",
            "status": "observed", "sensitivity": "public",
            "confidence": {"level": "medium", "reason": "state variable declaration"},
            "properties": {"file": rel, "line": line, "type": vartype, "name": name},
            "locators": [f"{rel}:{line}"], "evidence_refs": [f"source:{rel}:{line}"],
        })

    for fn in function_bodies(clean):
        name, body, line = fn["name"], fn["body"], fn["line"]
        locator = f"{rel}:{line}"
        is_entry = fn["visibility"] in {"external", "public"}
        is_mutating = not ({"view", "pure"} & set(fn["mutability"]))
        guards = [" ".join(m.group(2).split())[:160] for m in GUARD.finditer(body)]
        guards += [" ".join(m.group(1).split())[:160] for m in IF_REVERT.finditer(body)]
        deltas = [f"{m.group(1)} {m.group(2)} {m.group(3).strip()[:60]}" for m in DELTA_WRITE.finditer(body)]
        writes = {m.group(1) for m in PLAIN_WRITE.finditer(body)} | {m.group(1).split("[")[0] for m in DELTA_WRITE.finditer(body)}
        touched_state = sorted(writes & set(state_vars))
        calls = [m.group(1).strip() for m in EXTERNAL_CALL.finditer(body)]

        if is_entry:
            facts.append({
                "id": slug(f"{rel}-{name}-{line}", "entrypoint"), "kind": "entrypoint",
                "label": f"{name}({fn['params'].strip()[:60]})", "status": "observed",
                "sensitivity": "public",
                "confidence": {"level": "high", "reason": "declared entry point"},
                "properties": {
                    "file": rel, "line": line, "visibility": fn["visibility"],
                    "mutability": fn["mutability"], "modifiers": fn["modifiers"],
                    "guards": guards[:12], "state_written": touched_state,
                    "delta_writes": deltas[:12], "external_calls": calls[:12],
                    "access_control": bool(fn["modifiers"]) or bool(SENDER_CHECK.search(body)),
                },
                "locators": [locator], "evidence_refs": [f"source:{locator}"],
            })

        # --- high-signal leads -------------------------------------------------
        # 1. CEI violation: a storage write that happens after an external call.
        for call in EXTERNAL_CALL.finditer(body):
            tail = body[call.end():]
            after = {m.group(1) for m in PLAIN_WRITE.finditer(tail)} | {
                m.group(1).split("[")[0] for m in DELTA_WRITE.finditer(tail)
            }
            late = sorted(after & set(state_vars))
            if late:
                leads.append(_lead(
                    f"{rel}-{name}-cei", f"CEI violation in {name}: state written after external call", locator,
                    {"file": rel, "line": line, "function": name, "call": call.group(1).strip(),
                     "state_written_after_call": late, "lens": "execution-trace",
                     "bug_class": "reentrancy"},
                    "external call precedes a storage write",
                ))
                break

        # 2. Unprotected state-changing entry point. Writes scoped to the caller's own
        # slot (mapping[msg.sender]) are the permissionless-by-design pattern -- a
        # deposit is not an access-control bug -- so only flag writes that reach shared
        # state. This keeps the signal-to-noise ratio usable on real protocols.
        if is_entry and is_mutating and touched_state and not fn["modifiers"] and not SENDER_CHECK.search(body):
            self_scoped = set(re.findall(r"(\w+)\s*\[\s*msg\.sender\s*\]", body))
            shared_state = [var for var in touched_state if var not in self_scoped]
            if shared_state and name != "constructor":
                leads.append(_lead(
                    f"{rel}-{name}-noauth", f"{name} writes shared state with no access control", locator,
                    {"file": rel, "line": line, "function": name, "state_written": shared_state,
                     "self_scoped_writes": sorted(self_scoped), "lens": "access-control",
                     "bug_class": "missing-access-control"},
                    "public/external mutating function writes non-caller-scoped state "
                    "without a modifier or msg.sender check",
                ))

        # 3. Initializer without an initializer guard.
        if is_entry and re.match(r"^(initialize|init|__\w+_init)$", name) and not (
            {"initializer", "reinitializer"} & set(fn["modifiers"])
        ) and "initialized" not in body:
            leads.append(_lead(
                f"{rel}-{name}-reinit", f"{name} is callable without an initializer guard", locator,
                {"file": rel, "line": line, "function": name, "lens": "access-control",
                 "bug_class": "unprotected-initializer"},
                "initializer-shaped function lacks initializer/reinitializer",
            ))

        # 4. Unchecked low-level call return value.
        for call in re.finditer(r"\.(call|delegatecall|staticcall|send)\s*[({]", body):
            window = body[max(0, call.start() - 120):call.end() + 160]
            if not re.search(r"\b(bool\s+\w+|\(\s*bool|require\s*\(|if\s*\(\s*!?\s*\w+\s*\))", window):
                leads.append(_lead(
                    f"{rel}-{name}-{call.start()}-unchecked",
                    f"unchecked {call.group(1)} return in {name}", locator,
                    {"file": rel, "line": line, "function": name, "lens": "execution-trace",
                     "bug_class": "unchecked-call-return"},
                    "low-level call result is not captured or required",
                ))
                break

        # 5. Division before multiplication (precision loss).
        if DIV_THEN_MUL.search(body):
            leads.append(_lead(
                f"{rel}-{name}-divmul", f"division before multiplication in {name}", locator,
                {"file": rel, "line": line, "function": name, "lens": "math-precision",
                 "bug_class": "precision-loss"},
                "a division result is multiplied, amplifying truncation",
            ))

        # 6. tx.origin used for authorization.
        if TX_ORIGIN.search(body):
            leads.append(_lead(
                f"{rel}-{name}-txorigin", f"tx.origin referenced in {name}", locator,
                {"file": rel, "line": line, "function": name, "lens": "access-control",
                 "bug_class": "tx-origin-auth"},
                "tx.origin is phishable and must not gate authority",
            ))

        # 7. Unbounded loop over a dynamic array (griefing / gas DoS).
        for loop in LOOP_OVER_DYNAMIC.finditer(body):
            if loop.group(1) in state_vars:
                leads.append(_lead(
                    f"{rel}-{name}-unbounded", f"unbounded loop over {loop.group(1)} in {name}", locator,
                    {"file": rel, "line": line, "function": name, "array": loop.group(1),
                     "lens": "boundary", "bug_class": "unbounded-loop"},
                    "loop bound is attacker-growable storage",
                ))
                break

        # 8. Address setter with no zero-address check.
        if is_entry and is_mutating and touched_state and not ZERO_CHECK.search(body):
            params = ADDRESS_PARAM.findall(fn["params"])
            if params and re.match(r"^(set|update|change)\w*", name, re.I):
                leads.append(_lead(
                    f"{rel}-{name}-zeroaddr", f"{name} sets an address without a zero check", locator,
                    {"file": rel, "line": line, "function": name, "params": params,
                     "lens": "boundary", "bug_class": "missing-zero-address-check"},
                    "address setter accepts address(0)",
                ))

        # 9. Unlimited ERC20 approve (type(uint256).max / 2**256-1 style).
        if is_entry and re.search(
            r"\.approve\s*\([^,]+,\s*(type\s*\(\s*uint256\s*\)\s*\.\s*max|~uint256\s*\(\s*0\s*\)|"
            r"0xfff{8,}|2\s*\*\*\s*256\s*-\s*1)",
            body,
            re.I,
        ):
            leads.append(_lead(
                f"{rel}-{name}-maxapprove", f"unlimited approve in {name}", locator,
                {"file": rel, "line": line, "function": name, "lens": "trust-gap",
                 "bug_class": "unlimited-approval"},
                "approve of max uint is a standing authority grant",
            ))

        # 10. First-depositor / empty-supply mint without virtual offset (share inflation class).
        if is_entry and is_mutating and re.search(r"totalSupply\s*\(\s*\)\s*==\s*0|totalSupply\s*==\s*0", body):
            if re.search(r"\b(_mint|mint)\s*\(", body) and not re.search(
                r"VIRTUAL|OFFSET|DEAD|DEAD_SHARES|1e3|1000\s*\*|MINIMUM_LIQUIDITY", body, re.I
            ):
                leads.append(_lead(
                    f"{rel}-{name}-firstdep", f"empty-supply path in {name} may allow share inflation",
                    locator,
                    {"file": rel, "line": line, "function": name, "lens": "share-exchange-rate",
                     "bug_class": "first-depositor-inflation"},
                    "mint when totalSupply==0 without an inflation offset is a classic vault bug class",
                ))

        # 11. ERC20 transfer/transferFrom return value ignored (non-standard tokens).
        for call in re.finditer(r"\.(transferFrom|transfer)\s*\(", body):
            window = body[max(0, call.start() - 80):call.end() + 120]
            if re.search(r"safeTransfer", window):
                continue
            if not re.search(r"\b(bool\s+\w+|require\s*\(|if\s*\(\s*!?\s*\w+)", window):
                leads.append(_lead(
                    f"{rel}-{name}-{call.start()}-xferret",
                    f"unchecked {call.group(1)} return in {name}", locator,
                    {"file": rel, "line": line, "function": name, "lens": "periphery-integration",
                     "bug_class": "unchecked-erc20-return"},
                    "non-standard ERC20s return false instead of reverting",
                ))
                break

        # 12. msg.value accepted with no amount binding (common fee-on-transfer / accounting miss).
        if is_entry and "msg.value" in body and is_mutating:
            if not re.search(r"msg\.value\s*==|==\s*msg\.value|require\s*\(\s*msg\.value", body):
                if re.search(r"\b(deposit|receive|payable)\b", name + body[:80], re.I) or "payable" in fn["mutability"]:
                    # Only flag when value is stored asymmetrically without equality check.
                    if re.search(r"(balances?|deposits?|amounts?)\s*(\[|\.|$)", body) and not re.search(
                        r"balances?\s*\[[^\]]+\]\s*\+=\s*msg\.value|msg\.value\s*;", body
                    ):
                        leads.append(_lead(
                            f"{rel}-{name}-msgvalue", f"{name} uses msg.value without an equality bind",
                            locator,
                            {"file": rel, "line": line, "function": name, "lens": "economic",
                             "bug_class": "msg-value-accounting"},
                            "value path without explicit amount==msg.value is a frequent accounting gap",
                        ))

    return facts, leads


def analyze_tree(root: Path, case_id: str, snapshot_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    skip = {"test", "tests", "lib", "node_modules", "out", "mock", "mocks", "interfaces", ".git"}
    facts: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.sol")):
        parts = path.relative_to(root).parts[:-1]
        if any(part.lower() in skip for part in parts):
            continue
        rel = str(path.relative_to(root))
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        file_facts, file_leads = analyze_source(source, rel)
        facts.extend(file_facts)
        leads.extend(file_leads)
    for record in facts + leads:
        record["case_id"], record["snapshot_id"] = case_id, snapshot_id
    return facts, leads


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="observations JSONL (facts + leads)")
    parser.add_argument("--leads-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        if not args.root.is_dir():
            raise ValueError(f"source root not found: {args.root}")
        facts, leads = analyze_tree(args.root, str(case.get("case_id")), str(case.get("snapshot_id")))
        records = leads if args.leads_only else facts + leads
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, re.error) as exc:
        print(f"solidity analysis error: {exc}", file=sys.stderr)
        return 2
    by_class: dict[str, int] = {}
    for lead in leads:
        key = str(lead["properties"].get("bug_class", "other"))
        by_class[key] = by_class.get(key, 0) + 1
    for name, count in sorted(by_class.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:>3}  {name}")
    print(f"\nwrote {args.output}: {len(facts)} fact(s), {len(leads)} lead(s) -- all unproven hypotheses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
