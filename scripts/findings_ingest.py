#!/usr/bin/env python3
"""Ingest researcher finding writeups (HTML or markdown) into the knowledge base.

Public audit findings -- 0xsimao's index, Solodit exports, contest reports, a firm's
published PDFs converted to text -- are the highest-signal corpus available, because
each entry is a *confirmed* bug with a root cause a human wrote down. This turns a
directory or a saved page of them into knowledge-base entries that ``kb_match`` can
query, so hypothesis generation is grounded in what real auditors actually found.

Sites like 0xsimao.com are often unreachable from an audit host (egress policy), so
this reads from a LOCAL path you fetched yourself:

    # on a machine with network access
    wget -r -l2 -np -k -p https://0xsimao.com/findings -P ./simao
    ih-findings-ingest ./simao --source 0xsimao --output entries.json
    ih-kb-sync --fetch --findings-index entries.json --index knowledge/cache/index.json

The index page produces one record per finding. If individual detail pages are present
in the mirror, they are merged into the corresponding row and contribute the written
root cause, impact, recommendation, tool, code references, and fix links.

HTML is parsed with the standard library's HTMLParser -- no external dependency, and
scripts/styles are discarded rather than executed. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text

SLUG = re.compile(r"[^a-z0-9]+")
WHITESPACE = re.compile(r"\s+")
CWE = re.compile(r"CWE[-\s]?(\d{1,5})", re.IGNORECASE)
SEVERITY = re.compile(r"\b(critical|high|medium|low|informational|info|qa|gas)\b", re.IGNORECASE)
DATE = re.compile(r"\b\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+,?\s+\d{4}\b")
MONEY = re.compile(r"\$[\s]?\d[\d,]*(?:\.\d+)?\s?(?:k|m|b|million|billion|thousand)?", re.IGNORECASE)
CHAINS = (
    "ethereum", "evm", "solana", "aptos", "sui", "move", "cosmos", "near", "starknet",
    "polkadot", "substrate", "arbitrum", "optimism", "polygon", "bsc", "base", "avalanche",
)
# Bug-class vocabulary seen across public audit findings, mapped to the IH lens that owns it.
BUG_CLASS_LENS = {
    "reentrancy": "execution-trace",
    "read-only reentrancy": "execution-trace",
    "access control": "access-control",
    "missing access control": "access-control",
    "unprotected initializer": "access-control",
    "privilege escalation": "access-control",
    "rounding": "math-precision",
    "precision loss": "math-precision",
    "division before multiplication": "math-precision",
    "overflow": "math-precision",
    "underflow": "math-precision",
    "decimals": "math-precision",
    "first depositor": "math-precision",
    "share inflation": "math-precision",
    "oracle manipulation": "economic",
    "price manipulation": "economic",
    "flash loan": "economic",
    "sandwich": "economic",
    "front-run": "race-condition",
    "frontrun": "race-condition",
    "mev": "economic",
    "liquidation": "economic",
    "slippage": "economic",
    "invariant": "invariant-state",
    "accounting": "invariant-state",
    "insolvency": "invariant-state",
    "state desync": "invariant-state",
    "dos": "boundary",
    "denial of service": "boundary",
    "unbounded loop": "boundary",
    "griefing": "boundary",
    "edge case": "boundary",
    "gas limit": "boundary",
    "out of gas": "boundary",
    "revert": "boundary",
    "paused": "boundary",
    "frozen": "boundary",
    "supply cap": "boundary",
    "zero amount": "boundary",
    "zero value": "boundary",
    "constructor": "access-control",
    "initializer": "access-control",
    "initializers": "access-control",
    "owner": "access-control",
    "admin": "access-control",
    "role": "access-control",
    "governance": "access-control",
    "delegate": "access-control",
    "counterfactual wallet": "access-control",
    "beneficiary": "access-control",
    "approval check": "access-control",
    "maxlevel": "access-control",
    "stop the": "access-control",
    "signature replay": "trust-gap",
    "replay": "trust-gap",
    "domain separator": "trust-gap",
    "signature": "trust-gap",
    "eip712": "trust-gap",
    "encoding": "trust-gap",
    "malleable": "trust-gap",
    "stale price": "trust-gap",
    "freshness": "trust-gap",
    "sequencer": "trust-gap",
    "unexpected delay": "temporal-cohort",
    "trust": "trust-gap",
    "callback": "periphery-integration",
    "hook": "periphery-integration",
    "integration": "periphery-integration",
    "fee-on-transfer": "periphery-integration",
    "rebasing": "periphery-integration",
    "safeerc20": "periphery-integration",
    "safe erc20": "periphery-integration",
    "transfer fee": "periphery-integration",
    "approve": "periphery-integration",
    "allowance": "periphery-integration",
    "erc20": "periphery-integration",
    "erc4626": "share-exchange-rate",
    "share": "share-exchange-rate",
    "shares": "share-exchange-rate",
    "deposit": "share-exchange-rate",
    "withdraw": "share-exchange-rate",
    "redeem": "share-exchange-rate",
    "vault": "share-exchange-rate",
    "yield": "economic",
    "rewards": "economic",
    "staking": "economic",
    "liquidity": "economic",
    "fee": "economic",
    "fees": "economic",
    "flashloan": "economic",
    "donation": "economic",
    "redemption": "economic",
    "repurchase": "economic",
    "drained": "economic",
    "utilization": "economic",
    "limit order": "economic",
    "amm": "economic",
    "price deviation": "economic",
    "interest": "economic",
    "apr": "economic",
    "overpay": "math-precision",
    "overpaying": "math-precision",
    "underpay": "math-precision",
    "debt": "liquidation-solvency",
    "collateral": "liquidation-solvency",
    "liquidat": "liquidation-solvency",
    "insolvent": "liquidation-solvency",
    "bridge": "cross-chain-state",
    "cross-chain": "cross-chain-state",
    "layerzero": "cross-chain-state",
    "omnichain": "cross-chain-state",
    "other chains": "cross-chain-state",
    "synchronizing": "cross-chain-state",
    "lzreceive": "cross-chain-state",
    "epoch": "temporal-cohort",
    "deadline": "temporal-cohort",
    "expiry": "temporal-cohort",
    "expiration": "temporal-cohort",
    "timestamp": "temporal-cohort",
    "time window": "temporal-cohort",
    "finalize": "temporal-cohort",
    "time-sensitive": "temporal-cohort",
    "fixed term": "temporal-cohort",
    "front run": "race-condition",
    "race condition": "race-condition",
    "tick": "math-precision",
    "truncation": "math-precision",
    "incorrect calculation": "math-precision",
    "miscalculate": "math-precision",
    "underestimate": "math-precision",
    "overestimate": "math-precision",
    "decimal": "math-precision",
    "precision": "math-precision",
    "rounding error": "math-precision",
    "balance": "invariant-state",
    "state": "invariant-state",
    "storage": "invariant-state",
    "desync": "invariant-state",
    "inconsistent": "invariant-state",
    "mismatch": "invariant-state",
    "incorrectly": "invariant-state",
    "stuck": "invariant-state",
    "lost funds": "invariant-state",
    "burned": "invariant-state",
    "incorrect selector": "periphery-integration",
    "mint": "periphery-integration",
    "safe mint": "periphery-integration",
    "validate": "boundary",
    "validation": "boundary",
    "cancellation": "boundary",
    "buffer": "boundary",
    "block creators": "boundary",
    "blocked": "boundary",
    "refund": "cross-chain-state",
    "strategy": "economic",
    "private key": "credential-leak",
    "secret": "credential-leak",
    "password": "credential-leak",
    "wallet": "credential-leak",
    "idor": "web-api",
    "ssrf": "web-api",
    "xss": "web-api",
    "injection": "web-api",
    "authorization": "auth-session",
    "authentication": "auth-session",
    "session": "auth-session",
}
STOPWORDS = frozenset(
    "the a an and or of to in on for with by from at is are was were be been this that as "
    "it its into via can could may will not no if then than when where which who how what "
    "we they you i finding issue report audit severity impact recommendation mitigation".split()
)


class TextExtractor(HTMLParser):
    """Collect visible text and headings; discard script/style/nav chrome."""

    SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.headings: list[str] = []
        self.links: list[str] = []
        self._skip_depth = 0
        self._heading: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
        if tag in {"h1", "h2", "h3", "h4"}:
            self._heading = ""
        if tag == "a":
            for name, value in attrs:
                if name == "href" and value and value.startswith(("http://", "https://")):
                    self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"h1", "h2", "h3", "h4"} and self._heading is not None:
            text = WHITESPACE.sub(" ", self._heading).strip()
            if text:
                self.headings.append(text)
            self._heading = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)
        if self._heading is not None:
            self._heading += data

    @property
    def text(self) -> str:
        return WHITESPACE.sub(" ", " ".join(self.parts)).strip()


def slug(text: str) -> str:
    return SLUG.sub("-", text.lower()).strip("-")[:100] or "entry"


def clean_text(text: str) -> str:
    """Collapse markup whitespace without allowing control characters into the index."""
    return WHITESPACE.sub(" ", "".join(ch for ch in text if ch in "\t\n\r" or ord(ch) >= 32)).strip()


def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
    return {name.lower(): value for name, value in attrs if value is not None}


def _classes(attrs: list[tuple[str, str | None]]) -> set[str]:
    return set(_attrs(attrs).get("class", "").split())


def _absolute_url(href: str | None, base_url: str | None) -> str | None:
    if not href:
        return None
    value = href.strip()
    if value.startswith(("javascript:", "data:", "mailto:", "#")):
        return None
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return None
    if parsed.scheme or parsed.netloc:
        return value
    if base_url:
        return urljoin(base_url.rstrip("/") + "/", value)
    return value if value.startswith("/") else None


def _default_base_url(source: str, base_url: str | None) -> str | None:
    if base_url:
        return base_url
    if source.lower().replace("-", "") in {"0xsimao", "0xsimaofindings"}:
        return "https://0xsimao.com"
    return None


def _severity(value: str | None) -> str | None:
    if not value:
        return None
    low = clean_text(value).lower()
    if "critical" in low:
        return "critical"
    if "high" in low:
        return "high"
    if "medium" in low:
        return "medium"
    if "low" in low:
        return "low"
    if "informational" in low or re.search(r"\binfo\b", low):
        return "informational"
    if re.search(r"\bqa\b", low):
        return "qa"
    if re.search(r"\bgas\b", low):
        return "gas"
    return None


def _unique(values: list[str | None]) -> list[str]:
    result: list[str] = []
    for value in values:
        if not value:
            continue
        value = value.strip()
        if value and value not in result:
            result.append(value)
    return result


def _chains(text: str) -> list[str]:
    low = text.lower()
    return [chain for chain in CHAINS if chain in low]


def _simao_slug(href: str | None, fallback: str) -> str:
    if href:
        path = urlparse(href).path.rstrip("/")
        candidate = path.rsplit("/", 1)[-1]
        if candidate and candidate.lower() not in {"findings", "index", "index.html"}:
            return slug(candidate)
    return slug(fallback)


def _meta_fields(meta: str) -> dict[str, str | None]:
    """Decode the compact 0xSimao report metadata strip."""
    value = clean_text(meta).replace("•", "·")
    date_match = DATE.search(value)
    disclosed_at = date_match.group(0) if date_match else None
    before_date = value[: date_match.start()] if date_match else value
    parts = [clean_text(part) for part in before_date.split("·") if clean_text(part)]
    parts = [part for part in parts if not part.lower().startswith("by ")]
    return {
        "project_context": parts[0] if parts else None,
        "audit_platform": parts[1] if len(parts) > 1 else None,
        "protocol_category": parts[2] if len(parts) > 2 else None,
        "disclosed_at": disclosed_at,
    }


def classify(text: str) -> list[tuple[str, str]]:
    """Return [(bug_class, lens)] for every vocabulary term present in the writeup."""
    low = text.lower()
    hits = [(name, lens) for name, lens in BUG_CLASS_LENS.items() if name in low]
    # Prefer the most specific match when several overlap (e.g. "reentrancy" vs
    # "read-only reentrancy") by sorting longest-first and de-duplicating by lens.
    hits.sort(key=lambda item: -len(item[0]))
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for name, lens in hits:
        if lens in seen:
            continue
        seen.add(lens)
        unique.append((name, lens))
    return unique


def keywords(text: str, limit: int = 40) -> list[str]:
    found: list[str] = []
    for token in re.findall(r"[a-z][a-z0-9\-]{2,}", text.lower()):
        if token in STOPWORDS or token in found:
            continue
        found.append(token)
        if len(found) >= limit:
            break
    return found


class SimaoIndexParser(HTMLParser):
    """Parse the one-row-per-finding ledger used by 0xsimao.com/findings."""

    SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self, base_url: str | None) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.records: list[dict[str, Any]] = []
        self._skip_depth = 0
        self._section: dict[str, Any] | None = None
        self._card: dict[str, Any] | None = None
        self._capture: tuple[dict[str, Any], str, str, list[str]] | None = None
        self._capture_nested = 0

    def _begin(self, target: dict[str, Any], key: str, tag: str) -> None:
        self._finish_capture()
        self._capture = (target, key, tag, [])

    def _finish_capture(self) -> None:
        if self._capture is None:
            return
        target, key, _tag, parts = self._capture
        target[key] = clean_text("".join(parts))
        self._capture = None
        self._capture_nested = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.SKIP:
            self._skip_depth += 1
            return
        if self._capture is not None:
            self._capture_nested += 1
        attr = _attrs(attrs)
        classes = _classes(attrs)
        if tag == "section" and "sa-eng" in classes:
            self._finish_capture()
            self._section = {
                "name": "",
                "meta": "",
                "report_url": _absolute_url(attr.get("data-report"), self.base_url),
                "cards": [],
            }
            return
        if self._section is None:
            return
        if tag == "article" and "sa-find" in classes:
            self._card = {
                "source_url": None,
                "severity_label": attr.get("data-sev"),
                "title": "",
                "finding_ref": "",
                "summary": "",
            }
            return
        if tag == "h2" and "sa-name" in classes:
            self._begin(self._section, "name", tag)
        elif tag == "span" and "sa-meta" in classes:
            self._begin(self._section, "meta", tag)
        elif tag == "a" and "sa-ehl" in classes:
            self._section["report_url"] = _absolute_url(attr.get("href"), self.base_url)
        if self._card is None:
            return
        if tag == "a" and "sa-frow" in classes:
            href = attr.get("href")
            self._card["source_url"] = _absolute_url(href, self.base_url)
            self._card["slug"] = _simao_slug(href, self._card.get("title", "finding"))
        elif tag == "span" and "sa-sev" in classes:
            self._begin(self._card, "severity_label", tag)
        elif tag == "span" and "sa-ft" in classes:
            self._begin(self._card, "title", tag)
        elif tag == "span" and "sa-fnum" in classes:
            self._begin(self._card, "finding_ref", tag)
        elif tag == "p" and "sa-fsum" in classes:
            self._begin(self._card, "summary", tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._capture is not None:
            if self._capture_nested:
                self._capture_nested -= 1
            elif self._capture[2] == tag:
                self._finish_capture()
        if tag == "article" and self._card is not None:
            if self._card.get("source_url") or self._card.get("title"):
                self._section["cards"].append(self._card)
            self._card = None
        elif tag == "section" and self._section is not None:
            section = self._section
            for card in section["cards"]:
                card["section_name"] = section.get("name", "")
                card["meta"] = section.get("meta", "")
                card["report_url"] = card.get("report_url") or section.get("report_url")
            self.records.extend(section["cards"])
            self._section = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth or self._capture is None:
            return
        self._capture[3].append(data)

    def close(self) -> None:
        super().close()
        self._finish_capture()


class SimaoDetailParser(HTMLParser):
    """Extract the structured sections present on an individual 0xSimao finding."""

    SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self, base_url: str | None) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[str] = []
        self.canonical_url: str | None = None
        self.report_url: str | None = None
        self.report_text: list[str] = []
        self.title: list[str] = []
        self.meta: list[str] = []
        self.severity: list[str] = []
        self.finding_ref: list[str] = []
        self._sections: dict[str, list[str]] = {}
        self._current_section: str | None = None
        self._label: list[str] = []
        self._in_label = False
        self._in_h1 = False
        self._in_meta = False
        self._in_severity = False
        self._in_ref = False
        self._in_report = False
        self._in_body = False
        self._body_depth = 0
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = _attrs(attrs)
        classes = _classes(attrs)
        if tag == "link" and "canonical" in attr.get("rel", "").lower():
            self.canonical_url = _absolute_url(attr.get("href"), self.base_url)
        if tag == "meta":
            key = attr.get("property", attr.get("name", "")).lower()
            if key in {"og:url", "twitter:url"}:
                self.canonical_url = _absolute_url(attr.get("content"), self.base_url)
        if tag in self.SKIP:
            self._skip_depth += 1
            return
        if tag == "a":
            href = _absolute_url(attr.get("href"), self.base_url)
            if href and href not in self.links:
                self.links.append(href)
            if "sa-mlk" in classes:
                self.report_url = href or self.report_url
                self._in_report = True
            if attr.get("data-rep"):
                self.report_url = _absolute_url(attr["data-rep"], self.base_url) or self.report_url
        if tag == "h1":
            self._in_h1 = True
        if tag == "p" and "sa-meta" in classes:
            self._in_meta = True
        if tag == "span" and "sa-sev" in classes and not self.severity:
            self._in_severity = True
        if tag == "span" and "sa-fnum" in classes and not self.finding_ref:
            self._in_ref = True
        if tag == "p" and "sa-fh" in classes:
            self._in_label = True
            self._label = []
        if tag == "div" and "sa-fbody" in classes:
            self._in_body = True
            self._body_depth = 1
        elif self._in_body and tag == "div":
            self._body_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "h1":
            self._in_h1 = False
        elif tag == "p" and self._in_meta:
            self._in_meta = False
        elif tag == "span" and self._in_severity:
            self._in_severity = False
        elif tag == "span" and self._in_ref:
            self._in_ref = False
        elif tag == "a" and self._in_report:
            self._in_report = False
        elif tag == "p" and self._in_label:
            label = clean_text("".join(self._label)).lower()
            self._current_section = label or self._current_section
            self._in_label = False
        if self._in_body and tag == "div":
            if self._body_depth > 1:
                self._body_depth -= 1
            else:
                self._in_body = False
                self._body_depth = 0

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_h1:
            self.title.append(data)
        if self._in_meta:
            self.meta.append(data)
        if self._in_severity:
            self.severity.append(data)
        if self._in_ref:
            self.finding_ref.append(data)
        if self._in_label:
            self._label.append(data)
        elif self._current_section and self._in_body:
            self._sections.setdefault(self._current_section, []).append(data)
        if self._in_report:
            self.report_text.append(data)


def _section_value(parts: dict[str, list[str] | str], *names: str) -> str:
    for name in names:
        raw = parts.get(name.lower(), [])
        value = clean_text(" ".join(raw) if isinstance(raw, list) else str(raw))
        if value:
            return value
    return ""


def _entry_fields(
    *,
    source: str,
    title: str,
    summary: str,
    root_cause: str,
    severity_label: str | None,
    source_url: str | None,
    report_url: str | None,
    finding_ref: str | None,
    links: list[str],
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    title = clean_text(title)[:200]
    summary = clean_text(summary)
    root_cause = clean_text(root_cause)
    context_keys = ("project", "project_context", "audit_platform", "protocol_category", "tool_used")
    context = " ".join(str((extra or {}).get(key, "")) for key in context_keys)
    combined = " ".join(value for value in (title, summary, root_cause, str((extra or {}).get("impact", "")), context) if value)
    classes = classify(combined)
    cwe = CWE.search(combined)
    money = MONEY.search(combined)
    refs = _unique([source_url, report_url, *links])
    entry: dict[str, Any] = {
        "id": f"{source}:{_simao_slug(source_url, title)}",
        "source": source,
        "entry_type": "researcher-finding",
        "title": title or "untitled finding",
        "vuln_class": classes[0][0] if classes else "unclassified",
        "all_classes": [name for name, _ in classes],
        "lenses": [lens for _, lens in classes],
        "severity": _severity(severity_label),
        "severity_label": clean_text(severity_label or "") or None,
        "cwe": f"CWE-{cwe.group(1)}" if cwe else None,
        "summary": summary[:1000],
        "root_cause": root_cause[:1500],
        "chains": _chains(combined),
        "poc_refs": refs[:12],
        "keywords": keywords(combined, limit=60),
        "estimated_loss": money.group(0).strip() if money else None,
        "path": None,
        "source_url": source_url,
        "report_url": report_url,
        "finding_ref": clean_text(finding_ref or "") or None,
        "content_depth": "detail",
        "provenance": {
            "authority": "upstream-published-finding",
            "source_url": source_url,
            "retrieval": "local-mirror",
        },
    }
    if extra:
        for key, value in extra.items():
            if value not in (None, "", [], {}):
                entry[key] = value
    return entry


def parse_simao_index(raw: str, source: str = "0xsimao", base_url: str | None = None) -> list[dict[str, Any]]:
    """Return one metadata record per finding row on a 0xSimao ledger page."""
    base_url = _default_base_url(source, base_url)
    parser = SimaoIndexParser(base_url)
    try:
        parser.feed(raw)
        parser.close()
    except Exception:  # noqa: BLE001 - malformed upstream HTML must not abort a corpus run
        return []
    entries: list[dict[str, Any]] = []
    for card in parser.records:
        section_meta = _meta_fields(str(card.get("meta", "")))
        title = clean_text(str(card.get("title", "")))
        summary = clean_text(str(card.get("summary", "")))
        source_url = card.get("source_url")
        if not source_url:
            source_url = urljoin(base_url.rstrip("/") + "/", f"findings/{card.get('slug', slug(title))}") if base_url else None
        report_url = card.get("report_url")
        entry = _entry_fields(
            source=source,
            title=title,
            summary=summary,
            root_cause=summary,
            severity_label=str(card.get("severity_label") or "") or None,
            source_url=source_url,
            report_url=report_url,
            finding_ref=str(card.get("finding_ref") or "") or None,
            links=[],
            extra={
                "project": clean_text(str(card.get("section_name") or "")) or None,
                "project_context": section_meta["project_context"],
                "audit_platform": section_meta["audit_platform"],
                "protocol_category": section_meta["protocol_category"],
                "disclosed_at": section_meta["disclosed_at"],
                "content_depth": "index-summary",
                "provenance": {
                    "authority": "upstream-published-finding-index",
                    "source_url": source_url,
                    "retrieval": "local-mirror",
                },
            },
        )
        # The parser stores section values separately from the row so that the
        # row remains stable even if the site's card markup changes.
        entry["project"] = clean_text(str(card.get("section_name") or "")) or None
        entries.append(entry)
    return entries


def parse_simao_detail(raw: str, path: Path, source: str = "0xsimao", base_url: str | None = None) -> dict[str, Any] | None:
    """Parse an individual 0xSimao page, retaining section-level postmortem detail."""
    base_url = _default_base_url(source, base_url)
    parser = SimaoDetailParser(base_url)
    try:
        parser.feed(raw)
        parser.close()
    except Exception:  # noqa: BLE001 - malformed upstream HTML must not abort a corpus run
        return None
    title = clean_text("".join(parser.title))
    if not title:
        return None
    fields = _meta_fields(clean_text("".join(parser.meta)))
    source_url = parser.canonical_url
    if not source_url:
        source_url = _absolute_url(f"/findings/{path.stem}", base_url)
    sections = {key: clean_text(" ".join(value)) for key, value in parser._sections.items()}
    summary = _section_value(sections, "summary")
    detail = _section_value(sections, "vulnerability detail", "vulnerability", "root cause")
    impact = _section_value(sections, "impact")
    recommendation = _section_value(sections, "recommendation", "mitigation", "remediation")
    tool_used = _section_value(sections, "tool used", "tools used")
    code_snippet = _section_value(sections, "code snippet", "code")
    fixed_pr = _section_value(sections, "fixed pr", "fix", "resolution")
    entry = _entry_fields(
        source=source,
        title=title,
        summary=summary,
        root_cause=detail or summary,
        severity_label=clean_text("".join(parser.severity)) or None,
        source_url=source_url,
        report_url=parser.report_url,
        finding_ref=clean_text("".join(parser.finding_ref)) or None,
        links=parser.links,
        extra={
            "path": str(path),
            "project_context": fields["project_context"],
            "audit_platform": fields["audit_platform"],
            "protocol_category": fields["protocol_category"],
            "disclosed_at": fields["disclosed_at"],
            "report": clean_text("".join(parser.report_text)) or None,
            "impact": impact,
            "vulnerability_detail": detail,
            "recommendation": recommendation,
            "tool_used": tool_used,
            "code_snippet": code_snippet[:4000] if code_snippet else None,
            "fixed_pr": fixed_pr,
            "content_depth": "detail",
        },
    )
    return entry


def parse_document(path: Path, source: str, base_url: str | None = None) -> dict[str, Any] | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if not raw.strip():
        return None
    if path.suffix.lower() in {".html", ".htm"}:
        if re.search(r'<div[^>]+class=["\'][^"\']*\bsa-one\b', raw, re.IGNORECASE):
            return parse_simao_detail(raw, path, source, base_url)
        parser = TextExtractor()
        try:
            parser.feed(raw)
        except Exception:  # noqa: BLE001 - malformed HTML must not abort a corpus run
            return None
        text = parser.text
        title = parser.headings[0] if parser.headings else path.stem
        links = parser.links[:8]
    else:
        text = WHITESPACE.sub(" ", re.sub(r"[#*`>]", " ", raw)).strip()
        heading = re.search(r"^#{1,3}\s+(.+)$", raw, re.M)
        title = heading.group(1).strip() if heading else path.stem
        links = re.findall(r"https?://[^\s)\]]+", raw)[:8]
    if len(text) < 80:
        return None  # index pages / nav stubs carry no finding content
    classes = classify(text)
    severity = SEVERITY.search(text)
    cwe = CWE.search(text)
    source_url = _absolute_url(links[0] if links else None, _default_base_url(source, base_url))
    return {
        "id": f"{source}:{slug(title)}",
        "source": source,
        "entry_type": "researcher-finding",
        "title": WHITESPACE.sub(" ", title).strip()[:200],
        "vuln_class": classes[0][0] if classes else "unclassified",
        "all_classes": [name for name, _ in classes],
        "lenses": [lens for _, lens in classes],
        "severity": _severity(severity.group(1) if severity else None),
        "severity_label": severity.group(1).lower() if severity else None,
        "cwe": f"CWE-{cwe.group(1)}" if cwe else None,
        "summary": text[:500],
        "root_cause": text[:500],
        "chains": [],
        "poc_refs": links,
        "keywords": keywords(text),
        "path": str(path),
        "source_url": source_url,
        "report_url": None,
        "finding_ref": None,
        "content_depth": "generic",
        "provenance": {
            "authority": "local-researcher-source",
            "source_url": source_url,
            "retrieval": "local-source",
        },
    }


def _parse_many(path: Path, source: str, base_url: str | None) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".html", ".htm"}:
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        index_entries = parse_simao_index(raw, source, base_url)
        if index_entries:
            for entry in index_entries:
                entry["path"] = str(path)
            return index_entries
    entry = parse_document(path, source, base_url)
    return [entry] if entry else []


def _merge_entries(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Prefer full finding pages over index cards while retaining provenance."""
    depth = {"generic": 0, "index-summary": 1, "detail": 2}
    result = dict(old)
    replace = depth.get(str(new.get("content_depth")), 0) >= depth.get(str(old.get("content_depth")), 0)
    for key, value in new.items():
        if value in (None, "", [], {}):
            continue
        if replace or key not in result or result[key] in (None, "", [], {}):
            result[key] = value
    for key in ("all_classes", "lenses", "chains", "poc_refs", "keywords"):
        result[key] = _unique([*(old.get(key) or []), *(new.get(key) or [])])
    if depth.get(str(new.get("content_depth")), 0) > depth.get(str(old.get("content_depth")), 0):
        result["content_depth"] = new.get("content_depth")
    return result


def ingest(root: Path, source: str, base_url: str | None = None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".html", ".htm", ".md", ".txt"}:
            continue
        for entry in _parse_many(path, source, base_url):
            key = str(entry.get("source_url") or entry.get("id"))
            if key in seen:
                seen[key] = _merge_entries(seen[key], entry)
            else:
                seen[key] = entry
    entries = list(seen.values())
    entries.sort(key=lambda item: item["id"])
    return entries


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", type=Path, help="local directory of saved finding writeups")
    parser.add_argument("--source", default="researcher-findings", help="corpus label, e.g. 0xsimao")
    parser.add_argument("--base-url", help="canonical site base URL for relative links (default: 0xsimao.com for 0xsimao)")
    parser.add_argument("--output", required=True, type=Path, help="knowledge-base index JSON")
    args = parser.parse_args(argv)
    try:
        if not args.root.is_dir():
            raise ValueError(f"directory not found: {args.root}")
        entries = ingest(args.root, args.source, args.base_url)
        index = {
            "schema_version": "1.0",
            "generated_from": [args.source],
            "entry_count": len(entries),
            "entries": entries,
        }
        atomic_write_text(args.output, json.dumps(index, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"findings ingest error: {exc}", file=sys.stderr)
        return 2
    by_lens: dict[str, int] = {}
    for entry in entries:
        for lens in entry["lenses"] or ["unrouted"]:
            by_lens[lens] = by_lens.get(lens, 0) + 1
    for lens, count in sorted(by_lens.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {count:>3}  {lens}")
    print(f"\nwrote {args.output} ({len(entries)} finding(s) from {args.source})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
