# Scrapling adapter (executable)

Binds the Scrapling library (D4Vinci/Scrapling, BSD-3) to the `surface_inventory`,
`http_crawl`, and `browser_workflow` capabilities. Discovery/breadth layer before
specialist testing.

## Install

```bash
pip install "scrapling[fetchers]"
scrapling install          # fetches browsers; chromium is already present here
```

## Use

- `Fetcher` / `FetcherSession` — fast HTTP with TLS fingerprinting (`http_crawl`).
- `StealthyFetcher` / `DynamicFetcher` — headless browser for JS-rendered routes and
  XHR capture (`browser_workflow`). Enable stealth/proxy rotation only when the case
  manifest explicitly permits it.
- `Spider` — resumable, concurrent crawl with checkpoints for `surface_inventory`.

Export routes, forms, links, scripts, sitemaps, and XHR responses as JSON/JSONL, then
normalize with `scripts/scrapling_to_obs.py` into `route`/`form`/`endpoint`/`script`
observation nodes (`status: observed`, real locators). Parser guesses enter as
`inferred`.

## Controls

- enforce the case allowlist and per-domain rate limits;
- keep session and auth material case-scoped and redacted;
- cache and replay dev responses instead of re-requesting.

## Boundary

Scrapling discovers and extracts. It does not prove authorization, injection, SSRF,
race, or business impact — use the Burp adapter or a direct client for proof. Absent =
`http_crawl`/`browser_workflow` recorded as coverage debt.
