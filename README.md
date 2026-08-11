# Invariant Helix

Fail-closed security audit skill for **authorized** web apps, APIs, infra, and smart contracts.

AI findings are worthless until they climb:

```text
UNKNOWN → PLAUSIBLE → REACHABLE → REPRODUCED → VERIFIED
```

Gates G0–G9 + hashed evidence + independent falsification decide what is real. Missing tools become **coverage debt**, never silent passes.

## Install

```bash
git clone https://github.com/Takumixbt/Invariant-Helix.git
cd Invariant-Helix
pip install -e .
ih-self-audit
ih-check-capabilities
```

Python 3.10+. Optional: Foundry, Slither, recon CLIs, Burp (see `INSTALL.md`).

## Quick start (Solidity)

```bash
ih-audit path/to/contracts --local-dev-scope --out .ih-audit
# → observations, money-map, dispatch plan, lens bundles
# nothing is verified yet — run lenses, prove, falsify, then:

ih-poc .ih-audit/findings.json --output test/PoC_EXAMPLE.t.sol
forge test --match-contract PoC_ -vvv
```

Fixtures only (no target needed):

```bash
ih-solidity-analyze --scope evals/evm/sample-scope.json --root evals/evm --output leads.jsonl
ih-banner
```

## What you get

| Piece | Role |
|---|---|
| `SKILL.md` | Controller: G0–G9 + routing |
| 22 lenses | Attacker personas with concrete moves |
| `ih-*` CLIs | Validators, analyzers, dispatch, evidence |
| Graph + money map | Model value before hunting bugs |
| Knowledge base | Historical leads (never auto-findings) |

## Commands that matter

| Command | Does |
|---|---|
| `ih-audit` | One-shot prep: analyze → map → dispatch → bundles |
| `ih-solidity-analyze` | Lexical leads (hypothesized) |
| `ih-slither-ingest` | Slither JSON/SARIF → hypothesized leads |
| `ih-money-map` | Conservation / accounting candidates |
| `ih-lens-dispatch` | Graph-justified lenses + seed leads |
| `ih-poc` | Foundry PoC scaffold from a finding |
| `ih-validate-findings` | Schema + independence + proof gates |
| `ih-evaluate-case --release` | Release only if gates pass |
| `ih-self-audit` | Skill checks its own wiring |

## Rules (non-negotiable)

1. No target without written authorization.
2. Discoverer ≠ verifier (enforced).
3. Multi-agent agreement never sets status.
4. Incomplete work is not a clean bill of health.
5. Real-fund race tests are refused.

## Layout

```text
SKILL.md          controller
INSTALL.md        install tiers
references/       methodology + 22 lenses
adapters/         tool bindings
scripts/          ih-* engine (stdlib)
schemas/          JSON contracts
evals/            fixtures
tests/            adversarial suite
```

## License

MIT. See `SECURITY.md` for responsible use.
