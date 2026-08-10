"""Shared safety, canonicalization, redaction, and atomic-write helpers."""

from __future__ import annotations

import ipaddress
import os
import posixpath
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit


SECRET_KEY = re.compile(
    r"(password|passwd|secret|private.?key|seed.?phrase|authorization|proxy.?authorization|"
    r"cookie|access.?token|refresh.?token|api.?key|session|client.?secret)",
    re.IGNORECASE,
)
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "code",
    "cookie",
    "key",
    "password",
    "refresh_token",
    "secret",
    "session",
    "sig",
    "signature",
    "token",
}
VALUE_PATTERNS = (
    re.compile(r"(?i)\b(bearer|basic)\s+[a-z0-9._~+/=-]{6,}"),
    re.compile(
        r"(?i)\b(password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|"
        r"session|authorization)\s*[:=]\s*([^&\s,;]+)"
    ),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----", re.S),
)
ENCODED_PATH_META = re.compile(r"%(?:2e|2f|5c)", re.IGNORECASE)
CONTROL_CHARACTER = re.compile(r"[\x00-\x1f\x7f]")


@dataclass(frozen=True)
class ParsedHttpTarget:
    scheme: str
    host: str
    port: int
    path: str
    query: str

    @property
    def origin(self) -> str:
        default = (self.scheme == "http" and self.port == 80) or (
            self.scheme == "https" and self.port == 443
        )
        display_host = f"[{self.host}]" if ":" in self.host else self.host
        netloc = display_host if default else f"{display_host}:{self.port}"
        return urlunsplit((self.scheme, netloc, "", "", ""))

    @property
    def canonical_url(self) -> str:
        return urlunsplit((self.scheme, self.origin.split("//", 1)[1], self.path, self.query, ""))


def _canonical_path(path: str) -> str:
    decoded = path
    for _ in range(3):
        if ENCODED_PATH_META.search(decoded):
            raise ValueError("URL path contains an ambiguous encoded dot or separator")
        expanded = unquote(decoded)
        if expanded == decoded:
            break
        decoded = expanded
    if "\\" in decoded:
        raise ValueError("URL path contains a backslash separator")
    path = decoded or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    normalized = posixpath.normpath(path)
    if path.endswith("/") and normalized != "/":
        normalized += "/"
    # Preserve URL-safe delimiters while ensuring control characters cannot survive.
    return quote(normalized, safe="/%:@!$&'()*+,;=-._~")


def parse_http_target(value: str, *, allow_query: bool = True) -> ParsedHttpTarget:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("URL must be a non-empty string")
    value = value.strip()
    if CONTROL_CHARACTER.search(value):
        raise ValueError("URL contains a control character")
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL must be an absolute HTTP or HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL userinfo is not allowed")
    if parsed.fragment:
        raise ValueError("URL fragments are not allowed")
    try:
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        port = parsed.port or (443 if scheme == "https" else 80)
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f"invalid URL host or port: {exc}") from exc
    if not host:
        raise ValueError("URL host is empty")
    path = _canonical_path(parsed.path)
    query = parsed.query if allow_query else ""
    return ParsedHttpTarget(scheme=scheme, host=host, port=port, path=path, query=query)


def canonical_http_url(value: str, *, allow_query: bool = True) -> str:
    return parse_http_target(value, allow_query=allow_query).canonical_url


def url_allowed(url: str, allowlist: Iterable[str]) -> bool:
    if isinstance(allowlist, (str, bytes)):
        raise ValueError("target_allowlist must be an array, not a string")
    entries = list(allowlist)
    if not entries or not all(isinstance(item, str) and item.strip() for item in entries):
        raise ValueError("target_allowlist must contain non-empty URL strings")
    candidate = parse_http_target(url)
    for entry in entries:
        allowed = parse_http_target(entry, allow_query=False)
        if (candidate.scheme, candidate.host, candidate.port) != (
            allowed.scheme,
            allowed.host,
            allowed.port,
        ):
            continue
        prefix = allowed.path.rstrip("/") or "/"
        if prefix == "/" or candidate.path == prefix or candidate.path.startswith(f"{prefix}/"):
            return True
    return False


def is_local_host(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host == "localhost" or host.endswith(".test"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def redact_text(value: str) -> str:
    redacted = value
    for pattern in VALUE_PATTERNS:
        if pattern.pattern.startswith("(?i)\\b(bearer"):
            redacted = pattern.sub(lambda match: f"{match.group(1)} [REDACTED]", redacted)
        elif "PRIVATE KEY" in pattern.pattern:
            redacted = pattern.sub("[REDACTED PRIVATE KEY]", redacted)
        else:
            redacted = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)
    return redacted


def redact_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return redact_text(value)
        host = parsed.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        display_host = f"[{host}]" if ":" in host else host
        try:
            port = parsed.port
        except ValueError:
            port = None
        netloc = display_host if port is None else f"{display_host}:{port}"
        query = urlencode(
            [
                (key, "[REDACTED]" if key.lower() in SENSITIVE_QUERY_KEYS else redact_text(value))
                for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            ],
            doseq=True,
        )
        return urlunsplit((parsed.scheme.lower(), netloc, parsed.path, query, ""))
    except (UnicodeError, ValueError):
        return redact_text(value)


def redact(value: Any, key: str = "") -> Any:
    if SECRET_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(item_key): redact(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    if isinstance(value, tuple):
        return [redact(item, key) for item in value]
    if isinstance(value, str):
        if value.lower().startswith(("http://", "https://")):
            return redact_url(value)
        return redact_text(value)
    return value


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = handle.name
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
