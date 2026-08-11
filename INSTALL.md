# Install Invariant Helix

**One install = the full methodology.** Gates, 22 lenses, analyzers, graph, money-map, dispatch, evidence, PoC, KB, validators.

## Required

```bash
python --version   # 3.10+
git --version
git clone https://github.com/Takumixbt/Invariant-Helix.git
cd Invariant-Helix
pip install -e .
ih-banner
ih-self-audit
ih-check-capabilities
```

You now have every `ih-*` command. That is the skill.

## Capability tools (same methodology, more power)

IH asks for **capabilities**, not product brands. Whatever is on PATH is used; whatever is missing is **coverage debt** inside the same case — not a separate product.

| Capability | Typical tools |
|---|---|
| source_analysis | IH built-in + `slither` |
| chain_simulation / execution_trace / property_fuzzing | Foundry (`forge`/`cast`/`anvil`), echidna/medusa if present |
| surface / crawl / mutation | nmap, amass, httpx, ffuf, gobuster, scrapling, sqlmap |
| browser_workflow | playwright / chromium / scrapling |
| proxy / OOB | mitmproxy, Burp + MCP jar, interactsh-client |
| evidence / races | built into IH |

Windows notes and Burp jar load: [docs/BURP-MCP.md](docs/BURP-MCP.md).

## Verify

```bash
python -m unittest discover -s tests -q
ih-self-audit
ih-audit evals/evm --local-dev-scope --out ./out/smoke
```

One methodology. One package. Tools only deepen the same gates.
