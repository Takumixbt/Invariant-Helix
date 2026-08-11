# Recon CLI adapter (executable)

Binds recon CLIs to `surface_inventory`, `http_crawl`, and `input_mutation`.
Discovery layer for the recon-infra and web-api lenses.

## Install

Install via your package manager or vendor binaries onto PATH:

```bash
# discovery
nmap amass httpx gobuster
# fuzzing / mutation (active — needs case admission)
ffuf wfuzz sqlmap
```

## Use

- `nmap` / `amass` / `httpx` → hosts, ports, subdomains, live services (`surface_inventory`).
- `gobuster` / `ffuf` → routes, directories, parameters (`http_crawl`).
- `ffuf` / `wfuzz` / `sqlmap` → payload mutation (`input_mutation`) — active.

Normalize output with `scripts/recon_to_obs.py` into `host`/`service`/`origin`/`route`/
`parameter` observation nodes. Discovery findings are `observed`; inferred takeovers or
misconfigs are `inferred` leads.

## Controls

- every invocation is rate- and scope-bounded by the case manifest allowlist;
- `sqlmap` and active fuzzers require `active_testing: true` and capability admission;
- deny-dominant exclusions override any discovery; no scan implies authorization.

## Fallback

Absent tools → the corresponding capability is blocked coverage (`ih-check-capabilities`
names exactly which). Discovery degrades to a direct HTTP client for `request_replay`.
