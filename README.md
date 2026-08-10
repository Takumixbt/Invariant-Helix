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

An evidence-gated, graph-driven security-audit skill for authorized web apps, APIs,
infrastructure, smart contracts, and ZK circuits. Run `ih-banner` to print this plus a
live readiness readout of what your installation can actually do. It combines four
things no single tool does at once:

- **Recall** — 22 attacker lenses (contract, accounting, web, infra, ZK) with concrete moves.
- **Memory** — hypotheses grounded against real exploits, CVEs, and researcher findings.
- **Real tools** — Scrapling, Burp-MCP, Foundry, recon CLIs, bound to capability names.
- **Discipline** — G0–G9 gates, hashed evidence, and independent falsification decide
  what is actually real on *this* target.

It is an **executable** skill, not a prompt pack: `ih-self-audit` mechanically verifies
that every lens is dispatchable, every documented command resolves, and every claim the
docs make matches what the validators enforce.

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
├── HANDOFF.md            full walkthrough for someone new to auditing
├── references/           the methodology, grouped:
│   ├── method/           gates, safety, coverage, evidence, graph, reporting, x-ray,
│   │                     money-map (model the value before hunting the bugs)
│   ├── lenses/           22 attacker lenses + shared-rules, SOP, nemesis-loop
│   ├── web/              recon, toolchain, session model, auth logic, race testing
│   ├── chains/           contract audit, neutral IR, invariants, property fuzzing
│   └── knowledge/        incident patterns, CVE intel, knowledge base, integration
├── adapters/             bind tools to capabilities:
│   ├── web/              scrapling · burp-mcp · recon-cli · cve-intel · http · race
│   ├── chains/           12 families incl. zk-circuit + registry.json
│   ├── fuzzing/          echidna-medusa · foundry-invariant · chain-native
│   ├── audit/            pashov · nemesis bridges · peer-tools.json
│   └── claude-code.md · codex.md · generic-cli.md
├── scripts/              stdlib-only: validators + the new engine (x-ray, dispatch,
│                         converge, cvss, chain, kb, capabilities, normalizers)
├── schemas/              JSON contracts the validators enforce
├── knowledge/            report templates + gitignored fetched corpus cache
├── evals/                synthetic fixtures (web, evm, solana, kb, recon)
└── tests/                adversarial regression suite
```

## Quick start

Python 3.10+. `pip install -e .` exposes the `ih-*` commands. Full walk-through in
[QUICKSTART.md](QUICKSTART.md); install tiers in [INSTALL.md](INSTALL.md). New to security
auditing, or taking this project over? Start with **[HANDOFF.md](HANDOFF.md)**.

```bash
pip install -e .
ih-banner                                        # identity + live readiness
ih-self-audit                                    # the skill checks its own wiring
python -m unittest discover -s tests -v          # all gates green
ih-check-capabilities                            # what is installed vs blocked
ih-solidity-analyze --scope case.json --root src --output leads.jsonl   # located leads
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
