```
    ╔══════════════════════════════════════════════════════════════╗
    ║              I N V A R I A N T   H E L I X                    ║
    ║          two strands, one target. nothing survives both.     ║
    ╚══════════════════════════════════════════════════════════════╝
```

# Invariant Helix

A complete, peak bug-hunting skill for **any** target — a web app, an API, a
Solidity/Move/Rust protocol, or a system that is all three at once. Helix is a
**double helix**: two full audit strands that run independently and then cross.
Most tools do one strand. The bugs that pay the most live where the two touch.

Drop it a link — an **X (Twitter) post**, a **bounty program**, a **repo**, a
**domain**, or a **contract address** — and it scopes itself, hunts, gates every
finding, and hands you a platform-ready or Notion in-house report. Built for the
**DeepSeek/Hermes** harness and **Claude Code**. Language-agnostic. No runtime
required.

New here? **[`docs/FIELD-GUIDE.md`](docs/FIELD-GUIDE.md)** walks through every
file below in plain language. **[`INSTALL.md`](INSTALL.md)** has the exact
install command for every tool, for Linux/macOS/WSL and native PowerShell.

---

## What it does

```
   DROP A LINK → INTAKE → PRIME → ┌─ STRAND A (web) ─┐
                                  │    CROSSOVER     │ → CONVERGE → GATE →
                                  └─ STRAND B (web3) ┘   VERIFY → REPORT → LEARN
```

- **Strand A — Web / API full recon audit.** Surface mapping (subdomains,
  endpoints, JS, secrets, fingerprint), then the hunt across every web class:
  IDOR, auth/JWT/OAuth, SSRF, injection, business logic, race, smuggling, CORS,
  cache poisoning, account takeover. The sibling rule — "same op done two ways,
  one is wrong" — drives ~30% of paid findings.
- **Strand B — Smart Contract / Web3 full audit.** x-ray recon → the **alternating
  loop** (Feynman ↔ State-Inconsistency, run back and forth to convergence) → the
  web3 lens catalog (economic/oracle, precision, access, reentrancy), every
  hypothesis grounded in real historical exploits.
- **The Crossover — the intertwine.** After both strands run, Helix hunts the
  seam where web2 drives web3: a web admin panel that holds a minter key, an API
  that triggers an on-chain drain, a leaked `.env` that's also a validator key, a
  frontend that builds the tx you sign. Neither strand alone sees these.

Every finding passes a four-gate judge (**refutation → reachability → trigger →
impact**), climbs the uncertainty ladder (SUSPECT → REACHABLE → CONFIRMED) only
on evidence, and gets a runnable PoC before it ships. Helix **learns** across
engagements — confirmed patterns and burned false positives are remembered, so
each run starts sharper.

---

## The design in one breath

Four capabilities fuse in one skill, which is what makes it peak:

- **Recall** — aggressive, concrete attacker lenses across web and web3.
- **Memory** — every hypothesis pattern-matched against real historical exploits
  and disclosed reports, plus what Helix itself has confirmed before.
- **Real tools** — crawlers, proxies, fuzzers, and chain tooling bound to
  capability names and degraded to coverage-debt when absent.
- **Discipline** — evidence gates, an independent verifier, a hard raw→verified
  boundary, and a **self-audit** (`references/failure-modes.md`) that names the
  skill's own loopholes and the failsafe for each — so it can't quietly fool itself.

Grounding raises recall; the gate keeps the proof bar high. Nothing is vendored —
external tools are the operator's own install.

---

## Structure

```
Invariant-Helix/
├── SKILL.md                 # the controller: intake → strands → crossover → report → learn
├── AGENTS.md                # how an agent installs, boots, and operates Helix
├── INSTALL.md               # tiered setup + per-tool commands (Linux/macOS/WSL + PowerShell)
├── CHANGELOG.md · VERSION · LICENSE
├── README.md                # this file
├── docs/
│   └── FIELD-GUIDE.md       # a walkthrough of every component, in plain language
├── references/
│   ├── shared-rules.md      # the contract every actor obeys (format · CWE · severity · anti-hallucination)
│   ├── methodology.md       # Feynman/Socratic/Inversion + the alternating loop + the uncertainty ladder
│   ├── model-profiles.md    # orchestrator/actor role→model mapping per harness (the tiering)
│   ├── judging.md           # the 4-gate finding judge + Do-Not-Report
│   ├── convergence.md       # the dedup/promotion pipeline (signal from a deep swarm)
│   ├── failure-modes.md     # the skill's SELF-AUDIT — its own loopholes + failsafes
│   ├── scope-intake.md      # turn a dropped link into a scope card
│   ├── knowledge.md         # disclosed-report method + real-incident grounding
│   ├── learning-loop.md     # how Helix remembers across engagements (Hermes-tuned)
│   ├── report-formatting.md # platform templates + the Notion peak audit format
│   ├── cvss-guide.md        # CVSS 3.1 vectors and scoring
│   ├── local-tooling.md     # capability binding · Burp (+MCP) · PowerShell→WSL routing
│   └── strands/
│       ├── web-recon.md     # STRAND A — web/API orchestration + actor roster
│       ├── web3-audit.md    # STRAND B — smart-contract/Web3 orchestration + actor roster
│       └── crossover.md     # THE INTERTWINE — the web2↔web3 seam (strong-tier)
├── agents/                  # the actors — parallel specialty hunters
│   ├── recon · access-control · injection · client-side · business-logic   # web core
│   ├── graphql · supply-chain                                              # web deep
│   ├── economic · math · access-upgrade · integration                      # web3 core
│   ├── invariant · execution-trace · periphery · gap-hunter                # web3 deep
│   └── README.md            # the bundle spec + the roster
├── skills/                  # the two deep-logic engines (also standalone-invokable)
│   ├── feynman-auditor/SKILL.md              # first-principles logic (any language)
│   └── state-inconsistency-auditor/SKILL.md  # coupled-state desync (any language)
└── memory/                  # the learning store (append-only JSONL)
    ├── patterns.jsonl · false-positives.jsonl · engagements.jsonl · README.md
```

**How it runs:** a **strong-tier orchestrator** (Opus 4.8 · deepseek-v4-pro) does
intake, dispatch, crossover synthesis, convergence/dedup, the gate, and the report;
**fast-tier actors** (Sonnet 5 max · deepseek-v4-flash) hunt every lens in parallel
and return raw findings; the **deep-logic loop** (feynman ↔ state) runs on
contracts and web backend logic alike. Discoverer ≠ verifier. Runs **deep by
default** (full roster — 15 hunters + the loop), `--quick` for the core only.
Full mapping: `references/model-profiles.md`. With one model the tier split
collapses harmlessly and the alternating loop carries the rigor.

---

## Usage

```
/helix https://x.com/someone/status/123...      # resolve the X post → scope → full run
/helix https://immunefi.com/bug-bounty/proto/   # a bounty program
/helix https://github.com/acme/contracts        # a repo (web3)
/helix acme.com                                  # a web target
/helix 0xABC...DEF (ethereum)                    # a deployed contract

/helix --web <link>        # strand A only
/helix --web3 <link>       # strand B only
/helix --crossover         # crossover pass over existing strand output
/helix --report immunefi   # re-emit findings for a platform
/helix --report notion     # the in-house peak audit report
/helix --continue          # resume an interrupted engagement

/feynman        # standalone first-principles logic pass
/state-audit    # standalone coupled-state pass
```

Drop a bare link with no flag → Helix runs the full lifecycle and lets intake
pick the strand(s). Install: **[INSTALL.md](INSTALL.md)**.

---

## The non-negotiables

```
EVIDENCE OR SILENCE      no finding without file:line, request/response, or PoC
QUESTION EVERYTHING      no line, no guard, no assumption accepted at face value
FULL FIRST, TARGETED AFTER   complete passes before you chase suspects
SCOPE IS THE FENCE       never touch what the case card did not list
RAW IS NOT VERIFIED      hypotheses live in raw.md; only proof ships
DEEPEN, DON'T REFUTE     when hunting, amplify the bug; refute only at the gate
LEARN EVERY RUN          every confirmed bug and every false positive is remembered
```

---

## License

Invariant Helix is MIT. No external code is vendored — every tool it can drive
(crawlers, proxies, fuzzers, chain tooling) is the operator's own install,
invoked as a subprocess or over MCP, and degrades to coverage-debt when absent.

*For authorized security research and bug-bounty programs only. Use it against
targets you own or have explicit permission to test.*
