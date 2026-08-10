# Scrapling adapter

## Role

Use Scrapling for broad HTTP discovery, adaptive extraction, resumable
multi-session crawling, structured output and browser-backed dynamic collection.

## Recommended placement

Scrapling is the breadth layer before specialist testing. Use it to discover
routes, forms, links, scripts, sitemaps, API calls and XHR responses. Feed
normalized observations to the graph.

## Controls

- enforce domain allowlists and per-domain rate limits;
- use the program's robots and rules where applicable;
- disable proxy rotation or stealth behavior unless explicitly permitted;
- keep session and authentication material case-scoped;
- cache and replay development responses instead of re-requesting them;
- mark parser guesses as inferred until validated.

## Boundary

Scrapling discovers and extracts. It does not prove authorization flaws,
injection, SSRF, race behavior or business impact. Use Playwright, Burp or a
direct client for the relevant proof.
