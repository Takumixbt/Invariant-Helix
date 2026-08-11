# Tool output inside the methodology

Invariant Helix is **one** audit methodology. External tools (Slither, Burp, Foundry, recon CLIs) are not separate products — they feed the **same** gates as native analyzers.

## Rule

Any external output enters as a **hypothesis** only. G7 proof + G8 independent falsification still required. Tools never adjudicate.

## How it plugs in

| Tool output | IH step |
|---|---|
| Slither JSON/SARIF | `ih-slither-ingest` / auto in `ih-audit` → hypothesized leads |
| Foundry / fuzz crash | evidence + hypothesis |
| Recon (nmap, httpx, …) | `ih-recon-normalize` → graph |
| Burp / HAR | `ih-scrapling-normalize` → graph |

Missing a tool does not fork the methodology. It records **coverage debt** and continues.
