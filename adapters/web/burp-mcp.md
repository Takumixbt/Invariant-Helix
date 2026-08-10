# Burp-MCP adapter (executable)

Binds Burp Suite via the Burp-MCP-Unrestricted server (RamanMG, GPLv3 — referenced,
not vendored) to `proxy_observation`, `request_replay`, `http_crawl`, and
`oob_observation`.

## Install

Burp Suite (Community or Pro) + Java 21, then load the extension:

```bash
git clone https://github.com/RamanMG/Burp-MCP-Unrestricted.git
cd Burp-MCP-Unrestricted && ./gradlew embedProxyJar
# load build/libs/burp-mcp-all.jar via Burp → Extensions (Java)
```

The server binds `127.0.0.1:9876` and registers with the MCP client.

## MCP tools

- `get_proxy_http_history_latest` — newest-first proxy history (`proxy_observation`).
- `get_site_map` — discovered endpoints incl. spidered-but-unfetched (`http_crawl`).
- `repeater_send` / `repeater_read` / `repeater_rename` — replay (`request_replay`).
- `active_scan_url` / `crawl_url` — Pro only; active scan is **hypothesis-only** until
  G7 proves the finding.
- `get_scanner_issues`, Collaborator reads — `oob_observation`.

## Safety wrapper (mandatory)

**This fork disables approval prompts by default and enables config-editing tools.**
Re-enable approval prompts in the MCP+ tab. Treat every MCP tool as an untrusted
capability boundary: require case, scope, target, actor, and impact-limit checks before
any active operation (`active_scan_url`, `crawl_url`, `repeater_send`). Do not inherit
the permissive bridge defaults. A UI Repeater click is **not** a concurrency barrier
and must not be presented as race proof — use `scripts/race_runner.py` for that.

## Graph projection

Map proxy history to request/response/route/actor/role/state/evidence/snapshot nodes.
Preserve raw request evidence separately; redact cookies, tokens, and sensitive bodies
via `security_utils.redact`.

## Fallback

If Burp is unavailable, use browser network events + direct HTTP replay, and record the
missing `proxy_observation` capability as coverage debt.
