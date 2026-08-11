# Invariant Helix

```text
██╗███╗   ██╗██╗   ██╗ █████╗ ██████╗ ██╗ █████╗ ███╗   ██╗████████╗
██║████╗  ██║██║   ██║██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║╚══██╔══╝
██║██╔██╗ ██║██║   ██║███████║██████╔╝██║███████║██╔██╗ ██║   ██║
██║██║╚██╗██║╚██╗ ██╔╝██╔══██║██╔══██╗██║██╔══██║██║╚██╗██║   ██║
██║██║ ╚████║ ╚████╔╝ ██║  ██║██║  ██║██║██║  ██║██║ ╚████║   ██║
╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝
        ██╗  ██╗███████╗██╗     ██╗██╗  ██╗
        ██║  ██║██╔════╝██║     ██║╚██╗██╔╝
        ███████║█████╗  ██║     ██║ ╚███╔╝
        ██╔══██║██╔══╝  ██║     ██║ ██╔██╗
        ██║  ██║███████╗███████╗██║██╔╝ ██╗
        ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝
  evidence-gated  ·  graph-driven  ·  fails closed
```

**One methodology.** Web, API, infra, smart contracts — same gates, same graph, same evidence rules.

```text
UNKNOWN → PLAUSIBLE → REACHABLE → REPRODUCED → VERIFIED
```

G0–G9. Discoverer ≠ verifier. Missing tools = coverage debt, never a silent pass.  
No URL, repo, or RPC implies authorization.

## Install (the whole skill)

```bash
git clone https://github.com/Takumixbt/Invariant-Helix.git
cd Invariant-Helix
pip install -e .
ih-banner
ih-self-audit
```

That is Invariant Helix. One package. All lenses, gates, analyzers, dispatch, money-map, PoC scaffold, KB, validators.

Tools on PATH (Foundry, Slither, nmap, Burp, …) unlock capabilities automatically. Missing ones are recorded as debt — the methodology still runs.

Details: [INSTALL.md](INSTALL.md) · Burp MCP: [docs/BURP-MCP.md](docs/BURP-MCP.md)

## Run

```bash
# full methodology on a Solidity tree (banner prints first)
ih-audit path/to/contracts --local-dev-scope --out .ih-audit

# prove a finding
ih-poc findings.json --output test/PoC_X.t.sol
forge test --match-contract PoC_ -vvv

# release only if gates pass
ih-evaluate-case --case-manifest case.json --graph graph.json \
  --findings findings.json --coverage coverage.json \
  --manifest evidence-manifest.json --evidence-root evidence --release
```

## What “one methodology” means

| Layer | Included |
|---|---|
| Controller | `SKILL.md` + G0–G9 |
| Attack surface | 22 lenses (contract, accounting, web, infra, ZK) |
| Model | graph + money-map + x-ray |
| Analyzers | solidity + slither ingest + recon parsers |
| Orchestration | dispatch, bundles, loop, converge |
| Proof | PoC scaffold, evidence digests, falsification |
| Release | CVSS, coverage debt, platform templates |

Not a pile of plugins. One fail-closed audit procedure.

## Commands

| | |
|---|---|
| `ih-banner` | Identity + live capability readout |
| `ih-audit` | Full prep pipeline (analyze → map → dispatch → bundles) |
| `ih-solidity-analyze` / `ih-slither-ingest` | Located leads (hypothesized only) |
| `ih-money-map` | Accounting model |
| `ih-lens-dispatch` / `ih-lens-bundle` | Graph-justified lenses |
| `ih-poc` | Foundry PoC scaffold |
| `ih-validate-findings` / `ih-evaluate-case` | Gates + release |
| `ih-self-audit` | Skill checks its own wiring |

## Rules

1. Written authorization first.  
2. Discoverer ≠ verifier.  
3. Agreement never sets status.  
4. Incomplete ≠ clean.  
5. No real-fund race tests.

## Layout

```text
SKILL.md       one controller
references/    one methodology body (method + lenses + web + chains)
scripts/       one engine (ih-*)
adapters/      tool bindings for the same capabilities
schemas/       enforced contracts
evals/ tests/  fixtures + adversarial suite
```

## License

MIT · [SECURITY.md](SECURITY.md)
