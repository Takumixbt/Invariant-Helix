#!/usr/bin/env python3
"""Validate finding bundles, evidence integrity, status transitions, and release gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .cvss import base_score
    from .evidence_manifest import load_manifest, validate_manifest_structure, verify
    from .inventory import load_scope, validate_scope
except ImportError:  # direct script execution
    from cvss import base_score
    from evidence_manifest import load_manifest, validate_manifest_structure, verify
    from inventory import load_scope, validate_scope


REQUIRED = (
    "finding_id", "case_id", "snapshot_id", "title", "severity", "confidence", "status",
    "status_history", "proof_level", "discoverer_id", "verifier_id", "root_cause",
    "security_claim", "violated_invariant_or_trust_assumption", "affected_components",
    "preconditions", "reachable_path", "minimal_trigger_sequence", "observable_consequence",
    "impact", "scope_and_version", "verification_method", "falsification_result",
    "fix_guidance", "evidence_refs", "coverage_refs", "coverage_impact", "dedup_key",
)
STRING_FIELDS = {
    "finding_id", "case_id", "snapshot_id", "title", "discoverer_id", "verifier_id",
    "root_cause", "security_claim", "violated_invariant_or_trust_assumption",
    "observable_consequence", "impact", "scope_and_version", "verification_method",
    "fix_guidance", "coverage_impact", "dedup_key",
}
LIST_FIELDS = {
    "affected_components", "preconditions", "reachable_path", "minimal_trigger_sequence",
    "evidence_refs", "coverage_refs",
}
SEVERITIES = {"critical", "high", "medium", "low", "informational"}
MATERIAL = {"critical", "high", "medium"}
STATUSES = {
    "hypothesis", "under_verification", "verified", "refuted", "downgraded", "duplicate",
    "inconclusive", "released",
}
RELEASABLE = {"verified", "downgraded"}
PROOF_LEVELS = {"P0", "P1", "P2", "P3", "P4"}
VERDICTS = {"TRUE_POSITIVE", "FALSE_POSITIVE", "DOWNGRADED", "DUPLICATE", "INCONCLUSIVE"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
TRANSITIONS = {
    "hypothesis": {"under_verification", "refuted", "duplicate", "inconclusive"},
    "under_verification": {"verified", "downgraded", "refuted", "duplicate", "inconclusive"},
    "verified": {"released"},
    "downgraded": {"released"},
    "refuted": set(),
    "duplicate": set(),
    "inconclusive": {"under_verification"},
    "released": set(),
}


def load_findings(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("findings")
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError("input must be an array or an object with a findings array")
    return value


def nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() != "unknown"
    return value not in (None, [], {})


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _validate_confidence(value: Any, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} confidence must be an object")
        return
    if value.get("level") not in CONFIDENCE_LEVELS or not nonempty(value.get("reason")):
        errors.append(f"{prefix} confidence requires a valid level and reason")


def _validate_history(value: Any, current: str, prefix: str, errors: list[str]) -> None:
    if not isinstance(value, list) or not value:
        errors.append(f"{prefix} status_history must be a non-empty array")
        return
    statuses: list[str] = []
    for index, entry in enumerate(value):
        item_prefix = f"{prefix} status_history[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{item_prefix} must be an object")
            continue
        status = entry.get("status")
        if status not in STATUSES:
            errors.append(f"{item_prefix}.status is invalid")
        else:
            statuses.append(status)
        if not nonempty(entry.get("actor_id")):
            errors.append(f"{item_prefix}.actor_id is required")
        if not _string_list(entry.get("evidence_refs")):
            errors.append(f"{item_prefix}.evidence_refs must be non-empty")
    if statuses and statuses[0] != "hypothesis":
        errors.append(f"{prefix} status_history must begin with hypothesis")
    for previous, following in zip(statuses, statuses[1:]):
        if following not in TRANSITIONS.get(previous, set()):
            errors.append(f"{prefix} illegal status transition: {previous} -> {following}")
    if statuses and statuses[-1] != current:
        errors.append(f"{prefix} status_history does not end at status={current}")


def _validate_falsification(value: Any, finding: dict[str, Any], prefix: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{prefix} falsification_result must be an object")
        return
    attempted = value.get("attempted")
    if not isinstance(attempted, bool):
        errors.append(f"{prefix} falsification attempted must be boolean")
    if attempted and value.get("verdict") not in VERDICTS:
        errors.append(f"{prefix} falsification verdict is invalid")
    if not nonempty(value.get("verifier_id")) or value.get("verifier_id") != finding.get("verifier_id"):
        errors.append(f"{prefix} falsification verifier does not match verifier_id")
    if not _string_list(value.get("disproof_criteria")):
        errors.append(f"{prefix} falsification requires disproof_criteria")
    evidence_refs = value.get("evidence_refs")
    if attempted and not _string_list(evidence_refs):
        errors.append(f"{prefix} completed falsification requires evidence_refs")
    elif not attempted and not isinstance(evidence_refs, list):
        errors.append(f"{prefix} planned falsification evidence_refs must be an array")
    if attempted and not isinstance(value.get("independent_reproduction"), bool):
        errors.append(f"{prefix} independent_reproduction must be boolean")
    status = str(finding.get("status", "")).lower()
    expected = {"verified": "TRUE_POSITIVE", "downgraded": "DOWNGRADED"}.get(status)
    if status == "released" and isinstance(finding.get("status_history"), list):
        history_statuses = [
            entry.get("status") for entry in finding["status_history"] if isinstance(entry, dict)
        ]
        prior = history_statuses[-2] if len(history_statuses) >= 2 else None
        expected = {"verified": "TRUE_POSITIVE", "downgraded": "DOWNGRADED"}.get(prior)
    if status in {"verified", "downgraded", "released", "refuted", "duplicate", "inconclusive"} and attempted is not True:
        errors.append(f"{prefix} terminal status requires a completed falsification attempt")
    if expected and value.get("verdict") != expected:
        errors.append(f"{prefix} status={status} requires falsification verdict {expected}")


def _validate_cvss(value: Any, finding: dict[str, Any], prefix: str, errors: list[str]) -> None:
    """Optional CVSS 3.1 field: a vector string or an object carrying one. Its band
    must agree with the finding severity so the two cannot silently diverge."""
    vector = value.get("vector") if isinstance(value, dict) else value
    if not isinstance(vector, str) or not vector.strip():
        errors.append(f"{prefix} cvss must be a vector string or an object with a 'vector'")
        return
    try:
        scored = base_score(vector)
    except (ValueError, TypeError) as exc:
        errors.append(f"{prefix} cvss vector is invalid: {exc}")
        return
    severity = str(finding.get("severity", "")).lower()
    if severity in SEVERITIES and scored["ih_severity"] != severity:
        errors.append(
            f"{prefix} cvss band {scored['severity_band']} maps to {scored['ih_severity']} "
            f"but severity is {severity}"
        )


def _validate_extensions(
    finding: dict[str, Any],
    prefix: str,
    errors: list[str],
    *,
    content_digests: set[str],
    manifest_present: bool,
    releasable_ids: set[str],
) -> None:
    """Validate the lens/knowledge-base/convergence/kill-chain extension fields."""
    if "cvss" in finding:
        _validate_cvss(finding["cvss"], finding, prefix, errors)
    lens = finding.get("lens")
    if lens is not None and not (isinstance(lens, str) and lens.strip()):
        errors.append(f"{prefix} lens must be a non-empty string")
    bundle_digest = finding.get("bundle_digest")
    if lens:
        # A lens finding must cite the hashed bundle its agent actually read.
        if not (isinstance(bundle_digest, str) and bundle_digest.strip()):
            errors.append(f"{prefix} lens finding requires a bundle_digest")
        elif manifest_present and bundle_digest not in content_digests:
            errors.append(f"{prefix} bundle_digest does not resolve to a manifest artifact")
    convergence = finding.get("convergence")
    if convergence is not None:
        if not isinstance(convergence, dict):
            errors.append(f"{prefix} convergence must be an object")
        elif str(convergence.get("implies_status", "")).lower() in {"verified", "released", "downgraded"}:
            errors.append(f"{prefix} convergence must not imply a verified/released status")
    kb_refs = finding.get("kb_refs")
    if kb_refs is not None and not _string_list(kb_refs):
        errors.append(f"{prefix} kb_refs must be a non-empty array of strings")
    chain_of = finding.get("chain_of")
    if chain_of is not None:
        if not _string_list(chain_of):
            errors.append(f"{prefix} chain_of must be a non-empty array of finding ids")
        else:
            unresolved = [ref for ref in chain_of if ref not in releasable_ids]
            if unresolved:
                errors.append(f"{prefix} chain_of parents are not releasable: {', '.join(sorted(unresolved))}")


def _evidence_refs(finding: dict[str, Any]) -> set[str]:
    refs = set(finding.get("evidence_refs", [])) if isinstance(finding.get("evidence_refs"), list) else set()
    falsification = finding.get("falsification_result")
    if isinstance(falsification, dict) and isinstance(falsification.get("evidence_refs"), list):
        refs.update(falsification["evidence_refs"])
    history = finding.get("status_history")
    if isinstance(history, list):
        for entry in history:
            if isinstance(entry, dict) and isinstance(entry.get("evidence_refs"), list):
                refs.update(entry["evidence_refs"])
    return {str(item) for item in refs}


def validate(
    items: list[dict[str, Any]],
    release: bool,
    *,
    manifest: dict[str, Any] | None = None,
    case: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    dedup_keys: set[str] = set()
    artifact_ids = {
        record.get("artifact_id")
        for record in (manifest or {}).get("artifacts", [])
        if isinstance(record, dict)
    }
    content_digests = {
        record.get("content_digest")
        for record in (manifest or {}).get("artifacts", [])
        if isinstance(record, dict)
    }
    # A kill-chain parent must itself be a releasable finding in this bundle.
    releasable_ids = {
        str(item.get("finding_id"))
        for item in items
        if isinstance(item, dict)
        and str(item.get("status", "")).lower() in (RELEASABLE | {"released"})
    }
    for index, finding in enumerate(items):
        prefix = f"finding[{index}]"
        missing = [field for field in REQUIRED if not nonempty(finding.get(field))]
        if missing:
            errors.append(f"{prefix} missing: {', '.join(missing)}")
        for field in STRING_FIELDS:
            if field in finding and not isinstance(finding[field], str):
                errors.append(f"{prefix} {field} must be a string")
        for field in LIST_FIELDS:
            if field in finding and not _string_list(finding[field]):
                errors.append(f"{prefix} {field} must be a non-empty array of strings")
        finding_id = finding.get("finding_id")
        if isinstance(finding_id, str) and finding_id in ids:
            errors.append(f"{prefix} duplicate finding_id: {finding_id}")
        ids.add(str(finding_id))
        dedup_key = finding.get("dedup_key")
        if isinstance(dedup_key, str) and dedup_key in dedup_keys:
            errors.append(f"{prefix} duplicate dedup_key: {dedup_key}")
        dedup_keys.add(str(dedup_key))
        severity = str(finding.get("severity", "")).lower()
        status = str(finding.get("status", "")).lower()
        proof_level = finding.get("proof_level")
        if severity not in SEVERITIES:
            errors.append(f"{prefix} invalid severity")
        if status not in STATUSES:
            errors.append(f"{prefix} invalid status")
        if proof_level not in PROOF_LEVELS:
            errors.append(f"{prefix} invalid proof_level")
        _validate_confidence(finding.get("confidence"), prefix, errors)
        _validate_history(finding.get("status_history"), status, prefix, errors)
        _validate_falsification(finding.get("falsification_result"), finding, prefix, errors)
        _validate_extensions(
            finding,
            prefix,
            errors,
            content_digests={str(digest) for digest in content_digests if digest},
            manifest_present=manifest is not None,
            releasable_ids=releasable_ids,
        )
        if proof_level == "P4" and finding.get("falsification_result", {}).get("independent_reproduction") is not True:
            errors.append(f"{prefix} P4 requires independent reproduction")
        if finding.get("discoverer_id") == finding.get("verifier_id"):
            errors.append(f"{prefix} discoverer and verifier must be different")
        if release:
            if status not in RELEASABLE:
                errors.append(f"{prefix} is not releasable: status={status}")
            if severity in MATERIAL and proof_level not in {"P3", "P4"}:
                exception = finding.get("runtime_proof_exception")
                valid_exception = (
                    proof_level == "P2"
                    and isinstance(exception, dict)
                    and all(nonempty(exception.get(field)) for field in ("reason", "limitation", "adjudicator_id"))
                )
                if not valid_exception:
                    errors.append(f"{prefix} material release requires P3/P4 or an adjudicated P2 exception")
            if severity not in MATERIAL and proof_level not in {"P2", "P3", "P4"}:
                errors.append(f"{prefix} release requires at least P2")
        if case:
            if finding.get("case_id") != case.get("case_id"):
                errors.append(f"{prefix} case_id does not match the case manifest")
            if finding.get("snapshot_id") != case.get("snapshot_id"):
                errors.append(f"{prefix} snapshot_id does not match the case manifest")
        if manifest:
            if finding.get("case_id") != manifest.get("case_id"):
                errors.append(f"{prefix} case_id does not match the evidence manifest")
            if finding.get("snapshot_id") != manifest.get("snapshot_id"):
                errors.append(f"{prefix} snapshot_id does not match the evidence manifest")
            unresolved = sorted(_evidence_refs(finding) - artifact_ids)
            if unresolved:
                errors.append(f"{prefix} unresolved evidence_refs: {', '.join(unresolved)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings", type=Path)
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--case-manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        items = load_findings(args.findings)
        if args.release and not all((args.manifest, args.evidence_root, args.case_manifest)):
            raise ValueError("--release requires --manifest, --evidence-root, and --case-manifest")
        manifest = load_manifest(args.manifest) if args.manifest else None
        case = load_scope(args.case_manifest) if args.case_manifest else None
        preflight: list[str] = []
        if manifest:
            preflight.extend(validate_manifest_structure(manifest))
        if args.manifest and args.evidence_root:
            preflight.extend(verify(args.manifest, args.evidence_root))
        if case:
            preflight.extend(f"case manifest: {error}" for error in validate_scope(case))
        errors = preflight + validate(items, args.release, manifest=manifest, case=case)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"finding validation error: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"validated {len(items)} finding(s){' for release' if args.release else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
