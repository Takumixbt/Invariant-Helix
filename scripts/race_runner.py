#!/usr/bin/env python3
"""Run a bounded request set only after case-bound safety controls pass."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .evidence_manifest import load_manifest, verify
    from .inventory import load_scope, validate_scope
    from .security_utils import (
        atomic_write_text,
        is_local_host,
        parse_http_target,
        redact,
        redact_url,
        url_allowed,
    )
except ImportError:  # direct script execution
    from evidence_manifest import load_manifest, verify
    from inventory import load_scope, validate_scope
    from security_utils import (
        atomic_write_text,
        is_local_host,
        parse_http_target,
        redact,
        redact_url,
        url_allowed,
    )


MAX_CONCURRENCY = 32
MAX_BODY_CAPTURE = 4096
MAX_REQUEST_BODY = 1024 * 1024
METHOD = re.compile(r"^[A-Z]{3,12}$")
BLOCKED_REQUEST_HEADERS = {
    "forwarded",
    "host",
    "x-forwarded-host",
    "x-original-url",
    "x-rewrite-url",
}
SERVER_ID_HEADERS = {
    "cf-ray",
    "request-id",
    "traceparent",
    "x-amzn-requestid",
    "x-correlation-id",
    "x-request-id",
    "x-trace-id",
}


def is_local(host: str | None) -> bool:
    return bool(host) and is_local_host(str(host))


def allowed(url: str, prefixes: list[str]) -> bool:
    return url_allowed(url, prefixes)


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _control_passed(value: Any, name: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return [f"{name} must be an object"]
    if value.get("status") != "passed":
        errors.append(f"{name}.status must be passed")
    if not _nonempty(value.get("evidence_ref")):
        errors.append(f"{name}.evidence_ref is required")
    if not _nonempty(value.get("summary")):
        errors.append(f"{name}.summary is required")
    return errors


def _case_web_allowlist(case: dict[str, Any]) -> list[str]:
    return [
        str(target["value"])
        for target in case.get("targets", [])
        if isinstance(target, dict)
        and target.get("in_scope") is True
        and target.get("type") in {"web-origin", "rpc"}
    ]


def validate_execution_spec(
    spec: dict[str, Any],
    *,
    case: dict[str, Any] | None,
    execute: bool,
    allow_external: bool,
    authorized: bool,
    artifact_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    for field in (
        "case_id", "snapshot_id", "actor_context", "url", "target_allowlist", "concurrency",
        "barrier_policy", "sequential_control", "negative_control", "impact_limit",
        "reconciliation_plan",
    ):
        if field not in spec:
            errors.append(f"spec missing {field}")
    try:
        parsed = parse_http_target(str(spec.get("url", "")))
    except ValueError as exc:
        parsed = None
        errors.append(str(exc))
    allowlist = spec.get("target_allowlist")
    try:
        if parsed and not url_allowed(str(spec.get("url")), allowlist):
            errors.append("url does not match target_allowlist")
        elif parsed:
            # Parse every entry even when the first entry matches.
            for entry in allowlist:
                parse_http_target(entry, allow_query=False)
    except (TypeError, ValueError) as exc:
        errors.append(str(exc))
    count = spec.get("concurrency")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= MAX_CONCURRENCY:
        errors.append(f"concurrency must be an integer between 1 and {MAX_CONCURRENCY}")
    timeout = spec.get("timeout_seconds", 10)
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout):
        errors.append("timeout_seconds must be finite")
    elif not 0.1 <= float(timeout) <= 30:
        errors.append("timeout_seconds must be between 0.1 and 30")
    method = str(spec.get("method", "GET")).upper()
    if not METHOD.fullmatch(method):
        errors.append("method is invalid")
    headers = spec.get("headers", {})
    if not isinstance(headers, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in headers.items()):
        errors.append("headers must be an object of strings")
    elif {key.lower() for key in headers} & BLOCKED_REQUEST_HEADERS:
        errors.append("routing override headers are not allowed by the bundled race runner")
    body = spec.get("body", "")
    try:
        encoded = json.dumps(body).encode() if isinstance(body, (dict, list)) else str(body).encode()
        if len(encoded) > MAX_REQUEST_BODY:
            errors.append(f"request body exceeds {MAX_REQUEST_BODY} bytes")
    except (TypeError, ValueError):
        errors.append("body is not serializable")
    if spec.get("barrier_policy") != "thread-release":
        errors.append("barrier_policy must be thread-release")
    errors.extend(_control_passed(spec.get("sequential_control"), "sequential_control"))
    errors.extend(_control_passed(spec.get("negative_control"), "negative_control"))
    if not _nonempty(spec.get("impact_limit")) or not _nonempty(spec.get("reconciliation_plan")):
        errors.append("impact_limit and reconciliation_plan must be non-empty strings")

    if execute:
        if not authorized or spec.get("authorization_confirmed") is not True:
            errors.append("live execution requires --authorized and authorization_confirmed=true")
        if case is None:
            errors.append("live execution requires a case manifest")
        else:
            errors.extend(f"case manifest: {error}" for error in validate_scope(case))
            rules = case.get("rules_of_engagement", {})
            if spec.get("case_id") != case.get("case_id") or spec.get("snapshot_id") != case.get("snapshot_id"):
                errors.append("spec case_id/snapshot_id does not match the case manifest")
            if rules.get("active_testing") is not True:
                errors.append("case manifest does not permit active testing")
            if "synchronized_requests" not in case.get("allowed_capabilities", []):
                errors.append("case manifest does not allow synchronized_requests")
            if spec.get("actor_context") not in rules.get("test_identities", []):
                errors.append("actor_context is not an authorized test identity")
            if isinstance(count, int) and count > rules.get("max_concurrency", 0):
                errors.append("concurrency exceeds the case limit")
            if isinstance(count, int) and count > rules.get("max_requests", 0):
                errors.append("request count exceeds the case limit")
            if spec.get("impact_limit") != rules.get("impact_limit"):
                errors.append("impact_limit does not match the case manifest")
            if rules.get("real_funds_allowed") is True:
                errors.append("the bundled race runner cannot enforce real-fund limits")
            try:
                expires = datetime.fromisoformat(str(case.get("authorization_expires_at", "")).replace("Z", "+00:00"))
                if expires <= datetime.now(timezone.utc):
                    errors.append("case authorization has expired")
            except (TypeError, ValueError):
                errors.append("case authorization expiry is invalid")
            case_allowlist = _case_web_allowlist(case)
            try:
                if parsed and not url_allowed(str(spec.get("url")), case_allowlist):
                    errors.append("url is outside the case manifest targets")
                if isinstance(allowlist, list):
                    for entry in allowlist:
                        if not url_allowed(entry, case_allowlist):
                            errors.append(f"spec allowlist entry is broader than case scope: {entry}")
            except (TypeError, ValueError) as exc:
                errors.append(f"case allowlist error: {exc}")
        if artifact_ids is None:
            errors.append("live execution requires a verified evidence manifest")
        else:
            for control_name in ("sequential_control", "negative_control"):
                control = spec.get(control_name)
                if isinstance(control, dict) and control.get("evidence_ref") not in artifact_ids:
                    errors.append(f"{control_name}.evidence_ref does not resolve")
        if parsed and not is_local_host(parsed.host) and not allow_external:
            errors.append("external execution requires --allow-external")
    return errors


def build_request(spec: dict[str, Any]) -> urllib.request.Request:
    body = spec.get("body", "")
    if isinstance(body, (dict, list)):
        body = json.dumps(body, separators=(",", ":"))
    if body and not isinstance(body, bytes):
        body = str(body).encode("utf-8")
    return urllib.request.Request(
        url=str(spec["url"]),
        data=body or None,
        headers={str(key): str(value) for key, value in dict(spec.get("headers", {})).items()},
        method=str(spec.get("method", "GET")).upper(),
    )


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


def _response_headers(headers: Any) -> tuple[dict[str, Any], dict[str, str]]:
    safe = redact({str(key): str(value) for key, value in headers.items()})
    server_ids = {
        str(key): str(value)
        for key, value in headers.items()
        if str(key).lower() in SERVER_ID_HEADERS
    }
    return safe, server_ids


def one_request(
    index: int,
    spec: dict[str, Any],
    barrier: threading.Barrier,
    timeout: float,
) -> dict[str, Any]:
    result: dict[str, Any] = {"request_index": index, "url": redact_url(str(spec["url"]))}
    capture_body = bool(spec.get("capture_body", False))
    request = build_request(spec)
    opener = urllib.request.build_opener(NoRedirect)
    try:
        ready_at = time.time()
        barrier.wait(timeout=min(timeout, 10))
        release_at = time.time()
        release_monotonic = time.perf_counter()
        result.update({"ready_at": ready_at, "release_requested_at": release_at})
        try:
            with opener.open(request, timeout=timeout) as response:
                payload = response.read(MAX_BODY_CAPTURE) if capture_body else b""
                safe_headers, server_ids = _response_headers(response.headers)
                result.update(
                    {
                        "status": response.status,
                        "headers": safe_headers,
                        "server_identifiers": server_ids,
                        "body_prefix": (
                            redact(payload.decode("utf-8", errors="replace"))
                            if capture_body
                            else "[not captured]"
                        ),
                    }
                )
        except urllib.error.HTTPError as exc:
            payload = exc.read(MAX_BODY_CAPTURE) if capture_body else b""
            safe_headers, server_ids = _response_headers(exc.headers)
            result.update(
                {
                    "status": exc.code,
                    "headers": safe_headers,
                    "server_identifiers": server_ids,
                    "body_prefix": (
                        redact(payload.decode("utf-8", errors="replace"))
                        if capture_body
                        else "[not captured]"
                    ),
                }
            )
        result["finished_at"] = time.time()
        result["elapsed_after_release_ms"] = round((time.perf_counter() - release_monotonic) * 1000, 3)
    except Exception as exc:  # each worker produces a bounded, explicit result
        result.update({"error": f"{type(exc).__name__}: {exc}", "finished_at": time.time()})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--case-manifest", type=Path)
    parser.add_argument("--evidence-manifest", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--allow-external", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        if not isinstance(spec, dict):
            raise ValueError("spec root must be an object")
        case = load_scope(args.case_manifest) if args.case_manifest else None
        evidence = load_manifest(args.evidence_manifest) if args.evidence_manifest else None
        artifact_ids = (
            {
                record.get("artifact_id")
                for record in evidence.get("artifacts", [])
                if isinstance(record, dict)
            }
            if evidence
            else None
        )
        if args.execute:
            if not args.evidence_manifest or not args.evidence_root:
                raise ValueError("execution requires --evidence-manifest and --evidence-root")
            integrity_errors = verify(args.evidence_manifest, args.evidence_root)
            if integrity_errors:
                raise ValueError("; ".join(integrity_errors))
            if evidence and case and (
                evidence.get("case_id"), evidence.get("snapshot_id")
            ) != (case.get("case_id"), case.get("snapshot_id")):
                raise ValueError("evidence manifest does not match the case manifest")
        errors = validate_execution_spec(
            spec,
            case=case,
            execute=args.execute,
            allow_external=args.allow_external,
            authorized=args.authorized,
            artifact_ids=artifact_ids,
        )
        if errors:
            raise ValueError("; ".join(errors))
        count = int(spec["concurrency"])
        if not args.execute:
            print(
                json.dumps(
                    {
                        "mode": "dry-run",
                        "case_id": spec["case_id"],
                        "snapshot_id": spec["snapshot_id"],
                        "url": redact_url(str(spec["url"])),
                        "concurrency": count,
                        "controls": "validated",
                    },
                    indent=2,
                )
            )
            return 0
        if args.case_manifest is None:
            raise ValueError("--case-manifest is required for execution")
        timeout = float(spec.get("timeout_seconds", 10))
        barrier = threading.Barrier(count)
        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=count) as pool:
            futures = [pool.submit(one_request, index, spec, barrier, timeout) for index in range(count)]
            for future in as_completed(futures):
                results.append(future.result())
        case_digest = hashlib.sha256(args.case_manifest.read_bytes()).hexdigest()
        evidence_digest = hashlib.sha256(args.evidence_manifest.read_bytes()).hexdigest()
        output = {
            "schema_version": "1.0",
            "case_id": spec["case_id"],
            "snapshot_id": spec["snapshot_id"],
            "case_manifest_digest": f"sha256:{case_digest}",
            "evidence_manifest_digest": f"sha256:{evidence_digest}",
            "mode": "executed",
            "url": redact_url(str(spec["url"])),
            "concurrency": count,
            "barrier_policy": "thread-release",
            "timing_limit": "release timestamps are client-side and do not prove simultaneous server execution",
            "results": sorted(results, key=lambda item: item["request_index"]),
            "sequential_control": spec["sequential_control"],
            "negative_control": spec["negative_control"],
            "reconciliation": {
                "status": "required",
                "plan": spec["reconciliation_plan"],
            },
        }
        text = json.dumps(redact(output), indent=2, sort_keys=True) + "\n"
        if args.output:
            atomic_write_text(args.output, text)
        else:
            print(text, end="")
        if any("error" in result for result in results):
            print("race runner completed with worker errors", file=sys.stderr)
            return 1
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"race runner blocked: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
