# Install

Invariant Helix is tiered: the core needs nothing but Python, and every external tool
is optional. A missing tool becomes recorded coverage debt, never a silent gap. Run
`ih-check-capabilities` any time to see what is installed and what each gap blocks.

## Tier 0 — Core (required)

Runs every gate, lens, x-ray, dispatch, convergence, CVSS, and knowledge-base match.

```bash
python --version        # 3.10+
git --version
pip install -e .        # exposes the ih-* commands
```

That is the whole requirement for the core. No other install is needed to model a
target, dispatch lenses, ground hypotheses, score CVSS, or validate a release.

## Tier 1 — Web discovery & proof (optional)

```bash
pip install "scrapling[fetchers]" && scrapling install   # crawl + stealth browser
# recon CLIs onto PATH (apt/brew/vendor binaries):
#   nmap amass httpx gobuster ffuf wfuzz sqlmap
# chromium is already present in the managed environment
```

Supplies `surface_inventory`, `http_crawl`, `browser_workflow`, `input_mutation`.

## Tier 2 — Burp proxy (optional)

Burp Suite (Community/Pro) + Java 21:

```bash
git clone https://github.com/RamanMG/Burp-MCP-Unrestricted.git
cd Burp-MCP-Unrestricted && ./gradlew embedProxyJar
# load build/libs/burp-mcp-all.jar in Burp -> Extensions (Java)
```

Supplies `proxy_observation`, `request_replay`, `oob_observation`. **Re-enable the
approval prompts** (see `adapters/web/burp-mcp.md`) — this fork disables them by default.

## Tier 3 — Smart-contract tools (optional, per chain family)

```bash
# EVM
curl -L https://foundry.paradigm.xyz | bash && foundryup   # forge/cast/anvil
#   plus: echidna, medusa, halmos, slither for fuzzing/static
# Solana (cargo is usually present)
cargo install trident-cli        # + solana CLI, anchor
# Move: aptos or sui CLI + move-prover ;  Cairo: scarb + starknet-foundry
```

Supplies `source_analysis`, `chain_simulation`, `execution_trace`, `property_fuzzing`.
NEAR/Substrate/TON/Tron/Cardano remain Tier-3 methodology-only (coverage debt).

## Tier 4 — Knowledge base (optional, recommended)

Grounds hypothesis generation against real history. Corpora are fetched on demand into
the gitignored `knowledge/cache/`; nothing is committed.

```bash
ih-kb-sync --fetch                              # clones the incident + CVE corpora
# researcher findings that are network-restricted from the audit host:
ih-kb-sync --source /path/to/your/findings --index knowledge/cache/index.json
```

## Verify the install

```bash
python -m unittest discover -s tests -v         # all gates green
ih-check-capabilities                           # installed vs blocked capabilities
```
