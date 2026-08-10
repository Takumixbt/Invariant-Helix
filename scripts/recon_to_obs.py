#!/usr/bin/env python3
"""Normalize REAL recon tool output into Invariant Helix observations JSONL.

Parses what the tools actually emit -- not an idealized shape:

  nmap -oX      XML  (host/address, ports/port, service)
  httpx -json   JSONL (url, status_code, title, tech, host, port)
  ffuf -o -of json   JSON ({"results":[{"url","status","length",...}]})
  gobuster      text ("/admin  (Status: 301) [Size: 169]") or -o JSON
  amass/subfinder    text (one hostname per line) or -json JSONL
  generic       the IH shape {"hosts":[...], "routes":[...]}

Format is auto-detected; ``--format`` forces one. Discovery only: nodes are
``observed`` facts bound to the case/snapshot. Standard library only (no lxml --
``xml.etree`` is used with entity-expansion left disabled by default).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable

try:
    from .inventory import load_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from inventory import load_scope
    from security_utils import atomic_write_text

SLUG = re.compile(r"[^a-z0-9]+")
GOBUSTER_LINE = re.compile(r"^(?P<path>/\S*)\s+\(Status:\s*(?P<status>\d{3})\)(?:\s+\[Size:\s*(?P<size>\d+)\])?")
HOSTNAME = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", re.I)


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def _node(kind: str, label: str, locator: str, properties: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "id": slug(locator, kind), "kind": kind, "label": label[:120], "status": "observed",
        "sensitivity": "public",
        "confidence": {"level": "medium", "reason": reason},
        "properties": {k: v for k, v in properties.items() if v not in (None, "", [])},
        "locators": [locator], "evidence_refs": [f"recon:{locator}"],
    }


def parse_nmap_xml(text: str) -> list[dict[str, Any]]:
    """nmap -oX: <host><address addr=..><ports><port portid=..><service name=..>."""
    records: list[dict[str, Any]] = []
    root = ET.fromstring(text)  # noqa: S314 - trusted local tool output, no DTD processing
    for host in root.iter("host"):
        status = host.find("status")
        if status is not None and status.get("state") == "down":
            continue
        address = ""
        for candidate in host.iter("address"):
            if candidate.get("addr"):
                address = candidate.get("addr", "")
                break
        names = [h.get("name", "") for h in host.iter("hostname") if h.get("name")]
        label = names[0] if names else address
        if not label:
            continue
        records.append(_node("host", label, label, {"address": address, "hostnames": names}, "nmap host"))
        for port in host.iter("port"):
            portid = port.get("portid", "")
            state = port.find("state")
            if state is not None and state.get("state") != "open":
                continue
            service = port.find("service")
            svc_name = service.get("name", "") if service is not None else ""
            product = service.get("product", "") if service is not None else ""
            version = service.get("version", "") if service is not None else ""
            locator = f"{label}:{portid}"
            records.append(_node(
                "service", f"{svc_name or 'service'} {locator}".strip(), locator,
                {"port": portid, "protocol": port.get("protocol", ""), "service": svc_name,
                 "product": product, "version": version},
                "nmap open port",
            ))
    return records


def parse_httpx_jsonl(lines: Iterable[str]) -> list[dict[str, Any]]:
    """httpx -json: one JSON object per line with url/status_code/title/tech."""
    records: list[dict[str, Any]] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or item.get("input") or "").strip()
        if not url:
            continue
        records.append(_node(
            "origin", url, url,
            {"status_code": item.get("status_code"), "title": item.get("title"),
             "tech": item.get("tech") or item.get("technologies"),
             "webserver": item.get("webserver"), "host": item.get("host"), "port": item.get("port")},
            "httpx probe",
        ))
    return records


def parse_ffuf_json(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """ffuf -of json: {"results":[{"url","status","length","words","input"}]}."""
    records: list[dict[str, Any]] = []
    for item in payload.get("results", []) or []:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url", "")).strip()
        if not url:
            continue
        records.append(_node(
            "route", f"{item.get('status', '')} {url}".strip(), url,
            {"status": item.get("status"), "length": item.get("length"),
             "words": item.get("words"), "input": item.get("input")},
            "ffuf content discovery",
        ))
    return records


def parse_gobuster_text(lines: Iterable[str]) -> list[dict[str, Any]]:
    """gobuster dir default output: '/admin  (Status: 301) [Size: 169]'."""
    records: list[dict[str, Any]] = []
    for line in lines:
        match = GOBUSTER_LINE.match(line.strip())
        if not match:
            continue
        path = match.group("path")
        records.append(_node(
            "route", f"{match.group('status')} {path}", path,
            {"status": int(match.group("status")), "size": int(match.group("size") or 0)},
            "gobuster content discovery",
        ))
    return records


def parse_hostname_list(lines: Iterable[str]) -> list[dict[str, Any]]:
    """amass/subfinder plain output: one hostname per line."""
    records: list[dict[str, Any]] = []
    for line in lines:
        name = line.strip()
        if not name or not HOSTNAME.match(name):
            continue
        records.append(_node("host", name, name, {"discovery": "subdomain enumeration"}, "subdomain enumeration"))
    return records


def parse_generic(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """The Invariant Helix shape: {"hosts":[...], "services":[...], "origins":[...], "routes":[...]}."""
    kinds = {"hosts": "host", "services": "service", "origins": "origin", "routes": "route"}
    records: list[dict[str, Any]] = []
    for key, kind in kinds.items():
        for item in payload.get(key, []) or []:
            value = item if isinstance(item, str) else (
                item.get("value") or item.get("url") or item.get("host") if isinstance(item, dict) else None
            )
            if not value:
                continue
            properties = {k: v for k, v in item.items() if k not in {"value", "url", "host"}} if isinstance(item, dict) else {}
            records.append(_node(kind, str(value), str(value), properties, "recon discovery"))
    return records


def detect_and_parse(text: str, forced: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    stripped = text.lstrip()
    lines = text.splitlines()
    if forced == "nmap" or (forced is None and stripped.startswith("<") and "nmaprun" in text[:2000]):
        return "nmap", parse_nmap_xml(text)
    if forced in {"ffuf", "generic"} or (forced is None and stripped.startswith("{")):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            if forced == "ffuf" or "results" in payload:
                return "ffuf", parse_ffuf_json(payload)
            return "generic", parse_generic(payload)
    if forced == "httpx" or (forced is None and stripped.startswith("{")):
        return "httpx", parse_httpx_jsonl(lines)
    if forced == "gobuster" or (forced is None and any(GOBUSTER_LINE.match(line.strip()) for line in lines[:50])):
        return "gobuster", parse_gobuster_text(lines)
    if forced in {"amass", "subfinder", "hosts"} or forced is None:
        return "hostnames", parse_hostname_list(lines)
    raise ValueError(f"unsupported format: {forced}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("export", type=Path, help="recon tool output file")
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--format",
        choices=["nmap", "httpx", "ffuf", "gobuster", "amass", "subfinder", "hosts", "generic"],
        help="force a parser instead of auto-detecting",
    )
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        text = args.export.read_text(encoding="utf-8", errors="replace")
        detected, records = detect_and_parse(text, args.format)
        case_id, snapshot_id = str(case.get("case_id")), str(case.get("snapshot_id"))
        for record in records:
            record["case_id"], record["snapshot_id"] = case_id, snapshot_id
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"recon normalize error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(records)} observations, format={detected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
