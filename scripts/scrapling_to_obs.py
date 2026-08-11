#!/usr/bin/env python3
"""Normalize REAL web-crawl output into Invariant Helix observations JSONL.

Parses what crawlers and proxies actually emit:

  scrapling   JSON/JSONL items (url + optional method/params/forms/status)
  har         HTTP Archive 1.2 (log.entries[].request) -- Burp, browser devtools,
              mitmproxy, and most proxies export this
  burp        Burp site-map / proxy-history JSON export (url/method/status)
  generic     the IH shape {"routes":[...], "forms":[...], "scripts":[...]}

Every URL is canonicalized through ``security_utils.parse_http_target`` -- which
rejects userinfo, ambiguous encoded separators, and control characters -- so a crawl
cannot smuggle a scope-confusing URL into the graph. Query parameter NAMES are kept as
attack surface; values are dropped (they carry secrets and add no structural signal).
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

try:
    from .inventory import load_scope
    from .security_utils import atomic_write_text, parse_http_target, redact
except ImportError:  # direct script execution
    from inventory import load_scope
    from security_utils import atomic_write_text, parse_http_target, redact

SLUG = re.compile(r"[^a-z0-9]+")


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def _route(url: str, method: str, extra: dict[str, Any], reason: str) -> dict[str, Any] | None:
    """Canonicalize a URL into a route node, or return None if it is unsafe/unusable."""
    try:
        target = parse_http_target(url)
    except ValueError:
        return None  # userinfo, encoded separators, control chars -- refuse it
    params = sorted({name for name, _ in parse_qsl(target.query, keep_blank_values=True)})
    locator = f"{target.origin}{target.path}"
    properties = {"method": method.upper(), "origin": target.origin, "path": target.path}
    if params:
        properties["query_params"] = params  # names only; values are dropped
    properties.update(redact({k: v for k, v in extra.items() if v not in (None, "", [], {})}))
    return {
        "id": slug(f"{method}-{locator}", "route"), "kind": "route",
        "label": f"{method.upper()} {target.path}"[:120], "status": "observed",
        "sensitivity": "internal",
        "confidence": {"level": "medium", "reason": reason},
        "properties": properties, "locators": [locator], "evidence_refs": [f"crawl:{locator}"],
    }


def parse_har(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """HAR 1.2: log.entries[].request{url,method,queryString,postData}."""
    records: list[dict[str, Any]] = []
    for entry in payload.get("log", {}).get("entries", []) or []:
        if not isinstance(entry, dict):
            continue
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        url = str(request.get("url", "")).strip()
        if not url:
            continue
        post = request.get("postData") or {}
        body_params = sorted({
            str(p.get("name")) for p in (post.get("params") or []) if isinstance(p, dict) and p.get("name")
        })
        node = _route(url, str(request.get("method", "GET")), {
            "status": response.get("status"),
            "mime_type": (response.get("content") or {}).get("mimeType"),
            "body_params": body_params,
        }, "HAR entry")
        if node:
            records.append(node)
    return records


def parse_burp(payload: Any) -> list[dict[str, Any]]:
    """Burp site-map / proxy-history JSON export."""
    items = payload.get("items", payload) if isinstance(payload, dict) else payload
    records: list[dict[str, Any]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("request_url") or "").strip()
        if not url:
            continue
        node = _route(url, str(item.get("method", "GET")), {
            "status": item.get("status") or item.get("status_code"),
            "mime_type": item.get("mime_type"),
        }, "Burp site map")
        if node:
            records.append(node)
    return records


def parse_items(items: list[Any]) -> list[dict[str, Any]]:
    """Scrapling-style items and the generic IH shape's list members."""
    records: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, str):
            node = _route(item, "GET", {}, "crawl discovery")
            if node:
                records.append(node)
            continue
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("link") or item.get("action") or item.get("path") or "").strip()
        if not url:
            continue
        node = _route(url, str(item.get("method", "GET")), {
            "status": item.get("status") or item.get("status_code"),
            "form_fields": item.get("fields") or item.get("inputs") or item.get("params"),
            "title": item.get("title"),
        }, "crawl discovery")
        if node:
            records.append(node)
    return records


def detect_and_parse(text: str, forced: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    stripped = text.lstrip()
    if not stripped:
        return "empty", []
    payload: Any = None
    if stripped.startswith(("{", "[")):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
    if payload is not None:
        if forced == "har" or (forced is None and isinstance(payload, dict) and "log" in payload):
            return "har", parse_har(payload)
        if forced == "burp":
            return "burp", parse_burp(payload)
        if isinstance(payload, list):
            return "items", parse_items(payload)
        if isinstance(payload, dict):
            if any(key in payload for key in ("routes", "forms", "scripts", "endpoints")):
                records: list[dict[str, Any]] = []
                for key in ("routes", "forms", "scripts", "endpoints"):
                    records.extend(parse_items(payload.get(key) or []))
                return "generic", records
            if "items" in payload:
                return "burp", parse_burp(payload)
    # JSONL fallback: one crawl item per line.
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            items.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return "jsonl", parse_items(items)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("export", type=Path, help="crawler/proxy export file")
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--format", choices=["har", "burp", "scrapling", "generic"], help="force a parser")
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        text = args.export.read_text(encoding="utf-8", errors="replace")
        detected, records = detect_and_parse(text, args.format)
        case_id, snapshot_id = str(case.get("case_id")), str(case.get("snapshot_id"))
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for record in records:
            if record["id"] in seen:
                continue
            seen.add(record["id"])
            record["case_id"], record["snapshot_id"] = case_id, snapshot_id
            unique.append(record)
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in unique))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"crawl normalize error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(unique)} observations, format={detected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
