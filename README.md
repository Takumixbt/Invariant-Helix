# Invariant Helix

An evidence-gated, graph-driven security-audit skill for authorized web apps, APIs,
infrastructure, and smart contracts. It combines four things no single tool does at
once:

- **Recall** — aggressive attacker lenses (12 contract + 5 web/infra) with concrete moves.
- **Memory** — hypotheses grounded against a knowledge base of real exploits and CVEs.
- **Real tools** — Scrapling, Burp-MCP, Foundry, recon CLIs, bound to capability names.
- **Discipline** — G0–G9 gates, hashed evidence, and independent falsification decide
  what is actually real on *this* target.

It does not promise omniscience. It makes tested paths, proof, independent
falsification, unresolved assumptions, and coverage debt explicit, and fails closed when
scope, provenance, or execution limits are incomplete.

## How it works (three lanes)

1. **Tool adapters** bind a real tool to one of 13 capability names; a missing tool
   becomes coverage debt, never a silent gap (`ih-check-capabilities`).
2. **Orchestration** dispatches only the lenses the graph justifies, each with an
   independent verifier and a SHA-256-hashed bundle, then converges, scores (CVSS 3.1),
   and reports — convergence raises priority/confidence, never status.
3. **Knowledge base** grounds hypothesis generation (G5) against real history; every
   match is a lead the gates must still prove.

## Repository tree

```text
Invariant-Helix/
├── SKILL.md              controller: G0–G9 gates + capability routing
├── INSTALL.md            tiered install commands (core needs only Python)
├── QUICKSTART.md         copy-paste end-to-end run
├── references/           the methodology, grouped:
│   ├── method/           gates, safety, coverage, evidence, graph, reporting, x-ray
│   ├── lenses/           17 attacker lenses + shared-rules, SOP, nemesis-loop
│   ├── web/              recon, toolchain, session model, auth logic, race testing
│   ├── chains/           contract audit, neutral IR, invariants, property fuzzing
│   └── knowledge/        incident patterns, CVE intel, knowledge base, integration
├── adapters/             bind tools to capabilities:
│   ├── web/              scrapling · burp-mcp · recon-cli · cve-intel · http · race
│   ├── chains/           11 chain families + registry.json
│   ├── fuzzing/          echidna-medusa · foundry-invariant · chain-native
│   ├── audit/            pashov · nemesis skill bridges
│   └── claude-code.md · codex.md · generic-cli.md
├── scripts/              stdlib-only: validators + the new engine (x-ray, dispatch,
│                         converge, cvss, chain, kb, capabilities, normalizers)
├── schemas/              JSON contracts the validators enforce
├── knowledge/            report templates + gitignored fetched corpus cache
├── evals/                synthetic fixtures (web, evm, solana, kb)
└── tests/                adversarial regression suite
```

## Quick start

Python 3.10+. `pip install -e .` exposes the `ih-*` commands. Full walk-through in
[QUICKSTART.md](QUICKSTART.md); install tiers in [INSTALL.md](INSTALL.md).

```bash
pip install -e .
python -m unittest discover -s tests -v          # all gates green
ih-check-capabilities                            # what is installed vs blocked
ih-xray-enumerate --scope evals/evm/sample-scope.json --root evals/evm --output /tmp/x.jsonl
ih-normalize /tmp/x.jsonl --output /tmp/graph.json
ih-lens-dispatch --graph /tmp/graph.json --actor a --actor b
```

## Active testing safety

Passive/local analysis is the default. Active scans, fuzzing, race tests, OOB callbacks,
and production reproductions require an explicit case manifest and capability admission.
The bundled race runner enforces scope/identity/expiry/actor/concurrency/impact limits
and refuses real-fund execution because it cannot enforce a monetary ceiling. No URL,
RPC endpoint, repository, or source tree implies authorization.

## Project status

Version 0.3 adds the attacker-lens engine, executable x-ray, knowledge-base grounding,
CVSS/kill-chain/reporting, and executable tool adapters — all behind the existing gates,
with the adversarial regression suite extended to cover them. It remains a methodology
and orchestration contract, not an exploit kit or a guarantee that every vulnerability
will be found. Native adapter maturity and unavailable capabilities stay visible as
coverage debt.

See [SECURITY.md](SECURITY.md) for responsible use, and
[references/knowledge/pashov-integration.md](references/knowledge/pashov-integration.md)
for what was ported from pashov, bountyforge, and nemesis and how each maps to the gates.
