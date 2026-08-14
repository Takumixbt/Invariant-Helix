# Field Guide — a walkthrough of every component

This is the tour. If `SKILL.md` is the map, this is the guide that walks you
around it — what each file is for, why it exists, and how the pieces click
together. For exact install commands per tool, see `INSTALL.md`; this file is
about what the skill *is*, not what to run on your machine.

Quick facts: **45 files** across the skill, **15 actors**, **2 strands + 1
crossover**, **4 gates**, **14 self-audited failure modes**.

---

## The mental model

```
   DROP A LINK ──► INTAKE ──► ┌─ STRAND A · web ──┐
                              │                   ├─► CROSSOVER ──► CONVERGE ──► GATE ──► VERIFY ──► REPORT + LEARN
                              └─ STRAND B · web3 ──┘
```

You drop a link — an X post, a bounty program page, a repo, a domain, a
contract address. **Intake** turns that into a written scope card. Helix then
runs one or both **strands** in parallel: a team of **actors** hunts the web
surface, another hunts the smart-contract logic, and a **crossover** pass
hunts the seam where the two meet — a web admin panel that holds an on-chain
key is worth more than either half alone. Everything that comes out of a
hunt is a *hypothesis* until it survives **convergence** (dedup) and the
**gate** (four rounds of deliberate refutation). Only what's proven ships in
the report, and every confirmed pattern — and every false alarm — gets
written to memory so the next engagement starts smarter.

Hold that shape in your head and every file below's job becomes obvious.

---

## The controller

The two files everything else answers to.

**`SKILL.md`** — the orchestrator itself. States the engagement-context
posture (you're inside an authorized audit; hunt without hedging, stay inside
scope), defines the eleven-step lifecycle from intake to learning, explains
the orchestrator/actor tiering, and indexes every other file in the skill. If
you read one file, read this one.

**`AGENTS.md`** — written for whichever agent is actually running the skill,
not for you. Covers install for Claude Code, a Hermes-style runtime, or a
hand-rolled agent loop; lists the *host-capability contract* (file read is the
one hard requirement, everything else scales depth and degrades gracefully);
ends with a smoke test to confirm the skill actually loaded.

---

## Core discipline

The rules that make findings trustworthy instead of just plausible-sounding.

| File | What it does |
|---|---|
| `references/shared-rules.md` | The exact finding format every actor must use, the canonical bug-class + CWE map, severity tables, and the anti-hallucination protocol — never cite a line you haven't read. |
| `references/methodology.md` | The reasoning engine: three mental tools (Feynman, Socratic, Inversion) plus the alternating Feynman↔State loop — real adversarial rigor from one model, no bigger model required to check it. |
| `references/judging.md` | The gate. Four sequential rounds every finding must survive: Refutation, Reachability, Trigger, Impact. Fail one and it's rejected or demoted to a lead. This file is why Helix doesn't report noise. |
| `references/convergence.md` | The dedup pipeline that runs after a deep swarm of actors returns findings — merges four actors flagging the same bug four ways into one high-confidence finding. |
| `references/model-profiles.md` | Maps the orchestrator/actor roles onto real models on your harness (Opus↔Sonnet on Claude Code, DeepSeek-V4-Pro-0813↔DeepSeek-V4-Flash-0731 on Hermes) so discovery and verification are never the same pass. |
| `references/failure-modes.md` | Helix auditing itself. Fourteen ways an agent running this skill can quietly fail, each with its failsafe, plus preflight and release checklists. Read this once before a real engagement. |

---

## Getting-started files

What runs before the actual hunting does.

**`references/scope-intake.md`** — turns whatever you drop into a written
scope card. This is what lets you feed Helix lazily instead of hand-writing a
target spec.

**`references/knowledge.md`** — where Helix checks "has this exact bug shape
happened before?" The disclosed-report method and historical-incident
grounding. A match raises priority; it never counts as proof on its own.

**`references/learning-loop.md`** — how confirmed findings and burned false
positives get appended to `memory/` as plain JSONL, so the next audit on a
similar stack opens already knowing what to check first.

---

## The two strands + crossover

The actual double-helix structure the skill is named for, in
`references/strands/`.

**`web-recon.md` — Strand A, web.** Map the whole surface first (subdomains,
routes, JS, secrets), then dispatch the web actors against it in parallel,
chain findings that combine into something worse, hand off to the gate.

**`web3-audit.md` — Strand B, web3.** x-ray recon to map entry points and
invariants, the Feynman↔State alternating loop as the deep-logic core, the
web3 actor roster layered on top, every hypothesis checked against historical
incident shapes.

**`crossover.md` — the intertwine.** Runs only when both strands produced
output. Hunts the seven concrete places a web2 surface reaches web3 power —
an admin panel that holds a minter key, an API that triggers an on-chain
drain, a leaked `.env` that's also a validator key. Neither strand alone sees
these; this is the part that makes Helix worth more than the sum of its two
halves.

---

## The actors

Fifteen specialty hunters in `agents/`, dispatched in parallel by the
orchestrator, each returning raw findings — never a verdict.

**Web · core** (the fast pass): `recon-agent` maps the surface everyone else
hunts. `access-control-agent` owns IDOR, broken auth, JWT, OAuth/SSO,
privilege escalation. `injection-agent` owns SSRF, SQLi, RCE, SSTI, XXE, path
traversal. `client-side-agent` owns XSS, CORS, open redirect, cache
poisoning, smuggling. `business-logic-agent` owns workflow abuse, race
conditions, mass-assignment, limit bypass.

**Web · deep:** `graphql-agent` (introspection, field-auth gaps, aliasing/
batching abuse, nested-query DoS) and `supply-chain-agent` (dependency
confusion, CI/CD exposure, leaked pipeline secrets).

**Web3 · core** (the fast pass): `economic-agent` owns oracle manipulation,
flash-loan attacks, price manipulation, MEV. `math-agent` owns precision
loss, overflow/underflow, donation-inflation, rounding direction.
`access-upgrade-agent` owns access control, initializers, upgrade paths,
delegatecall, storage collision. `integration-agent` owns reentrancy,
unvalidated callbacks, weird-token assumptions, signature replay.

**Web3 · deep:** `invariant-agent` attacks every stated invariant with a
concrete sequence, escalating to property fuzzing when a trace can't settle
it. `execution-trace-agent` traces complete, cross-contract attack paths end
to end — the biggest source of chained findings. `periphery-agent` audits
the code everyone skips: libraries, hooks, init/upgrade/migration/emergency
paths. `gap-hunter-agent` hunts what's *missing* rather than what's wrong,
dispatched three times in parallel across numerical, trust, and flow gaps.

Full spec, bundle contract, and roster table: `agents/README.md`.

---

## The deep-logic engines

Two files in `skills/`, run in alternation, that do the heaviest reasoning in
the whole skill — and work identically on Solidity, Rust, Go, Python, or
TypeScript.

**`feynman-auditor/SKILL.md`** — first-principles interrogation: seven
question categories asked of every function — why does this line exist, what
happens if it moves, what does it silently assume. Standalone via `/feynman`.

**`state-inconsistency-auditor/SKILL.md`** — maps every pair of coupled state
values (a balance and its checkpoint, a stake and its reward debt) and finds
every path where one side updates without the other. Standalone via
`/state-audit`.

Run back to back and then alternated on each other's suspects until neither
turns up anything new, these two produce genuine two-auditor scrutiny from
one model — which is exactly what makes Helix viable on a single API key.

---

## Output & tooling references

How a confirmed finding becomes a document, and how Helix reaches your local
tools.

**`references/report-formatting.md`** — submission templates for HackerOne,
Immunefi, Bugcrowd, Intigriti, and audit contests, plus a Notion-ready "peak
audit" format for in-house and client reports.

**`references/cvss-guide.md`** — how to build a correct CVSS 3.1 vector and
score for a finding, with worked examples per bug class.

**`references/local-tooling.md`** — the full capability→tool binding table,
the Burp-via-MCP integration and its safety notes, and the PowerShell→WSL
auto-routing logic. Pairs with `INSTALL.md`, which has the exact install
command for every tool named here.

---

## Memory

Append-only, plain JSONL, in `memory/` — no database. This is how the skill
gets sharper without any training.

`patterns.jsonl` holds confirmed bug patterns — the exact code shape, the
question that found it, the fix. Only gate-passed findings ever get written
here. `false-positives.jsonl` holds hypotheses that looked real and weren't,
and why, so the skill stops re-raising the same dead end. `engagements.jsonl`
is a running index of what's been hunted.

---

## Project scaffolding

The files a repository carries, not the skill itself: `README.md` (the
pitch, the tree, the invocation commands), `INSTALL.md` (tiered setup, with
the full tool-by-tool command reference), `CHANGELOG.md` / `VERSION` (what
shipped, versioned going forward), and `LICENSE` (MIT — nothing external is
vendored; every tool is your own install).

---

## Where to go next

- Setting up tools on your machine → `INSTALL.md`
- Running the skill for the first time → `AGENTS.md` § Minimal smoke test
- Understanding what can go wrong → `references/failure-modes.md`
- The actual controller you'll read most → `SKILL.md`
