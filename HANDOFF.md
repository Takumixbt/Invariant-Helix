# Handoff — what this project is and how to run it

Written for someone taking this over who has never done a security audit. No prior
knowledge assumed. Read this top to bottom once; after that use it as a reference.

---

## 1. The problem this solves

A **bug bounty** is a program where an organisation pays you for finding security flaws in
their software and reporting them privately instead of exploiting them. A **security
audit** is the same work done under contract before a launch. Either way the job is: find
a real flaw, prove it is real, and write it up convincingly.

You can point an AI at a codebase and ask "find bugs." It will return a dozen
confident-sounding paragraphs. Some are real, some are hallucinated, some are real but
unreachable in practice. **You cannot tell which is which, and neither can the AI, because
it is grading its own work.** Submitting a wrong report wastes a triager's time and burns
your reputation; missing a real one costs the money.

Invariant Helix exists to make that difference machine-checkable.

## 2. What it actually is

Two halves that fit together.

**A rulebook the AI follows.** `SKILL.md` plus ~50 files in `references/`. Loaded into a
coding agent (Claude Code, Codex, or any CLI agent) as its operating procedure.

**A referee that checks the AI's homework.** 27 Python programs in `scripts/`. Standard
library only — no dependencies. These are the part that cannot be talked out of anything.
Every one of them is a place where the model is unable to lie to you.

It is *not* an exploit kit, and not a scanner you point at a URL. It is an operating
procedure with enforcement.

## 3. The ten gates (the spine of everything)

Work proceeds through gates G0–G9. The controller may not silently skip one; skipping
requires a recorded reason.

| Gate | Name | What happens | Enforced by |
|---|---|---|---|
| G0 | Bound | Authorization, scope, expiry, limits are written down and validated | `ih-inventory` |
| G1 | Snapshot | Pin the exact version under review (commit, addresses, build) | case manifest |
| G2 | Inventory | Enumerate everything: files, entry points, hosts, routes | `ih-xray-enumerate`, recon tools |
| G3 | Model | Build the graph and the **money map** | `ih-normalize` |
| G4 | Coverage | Write down what you promise to check, and who verifies it | `ih-validate-coverage` |
| G5 | Hypotheses | Generate attack ideas — lenses + knowledge base | `ih-lens-dispatch`, `ih-kb-match` |
| G6 | Execution | Run only permitted tests, cheapest proof first | `ih-race`, fuzzers |
| G7 | Proof | Trace actor → guard → consequence → impact | `ih-validate-findings` |
| G8 | Falsification | An *independent* person tries to disprove it | `ih-validate-findings` |
| G9 | Release | Everything resolves, digests verify, then publish | `ih-evaluate-case` |

**The one idea to take away:** a claim moves up this ladder only by evidence.

```
UNKNOWN → PLAUSIBLE → REACHABLE → REPRODUCED → VERIFIED
```

Nothing skips a rung. Not agreement between agents, not a knowledge-base match, not
confidence, not severity.

## 4. Why the graph, the JSON, and the Python exist

These look like bureaucracy. Each one removes a specific way the work goes wrong.

- **JSON instead of prose** — a computer can validate JSON. It cannot validate a paragraph.
- **The graph** — the good bugs on a mixed target live on the *seam*. A web API decides who
  you are and hands a contract a signed message; the contract trusts it. Review each side
  alone and both look fine. The graph puts web nodes and contract nodes in **one structure**
  so you can ask "what paths reach funds without passing an authority check." You cannot ask
  that of two separate reports.
- **Evidence manifest** — every screenshot and log gets a SHA-256 fingerprint. Findings cite
  `artifact:ec80df…`, not "see attached." Nobody can quietly swap a file later.
- **discoverer ≠ verifier** — enforced in code. The thing that found the bug cannot be the
  thing that confirms it.
- **Coverage ledger** — a written list of what you promised to check, so "I found nothing"
  can never masquerade as "there is nothing there."

The tests are deliberately adversarial. Real test names in `tests/`: *"FALSE_POSITIVE cannot
be verified"*, *"self-verification rejected"*, *"convergence cannot evade by renaming the
key."* Those exist because those are the lies that get told.

## 5. Repository layout

```
SKILL.md              the controller: gates + routing. The agent reads this first.
INSTALL.md            what to install, in tiers. Core needs only Python + git.
QUICKSTART.md         copy-paste run against bundled fixtures.
HANDOFF.md            this file.

references/           the rulebook (~50 files)
  method/             gates, safety, coverage, evidence, reporting, x-ray, money-map
  lenses/             22 attacker lenses + shared-rules, SOP, nemesis-loop
  web/                recon, browser/session, auth logic, race testing
  chains/             contract audit, chain-neutral IR, invariants, property fuzzing
  knowledge/          incident patterns, CVE intel, knowledge base, integration record

adapters/             bind real tools to capability names
  web/                scrapling · burp-mcp · recon-cli · cve-intel · http · race
  chains/             12 chain families + registry.json
  fuzzing/            echidna-medusa · foundry-invariant · chain-native
  audit/              peer-tools.json + pashov/nemesis bridges

schemas/              6 JSON contracts the validators enforce
scripts/              27 programs, standard library only
knowledge/            report templates + gitignored corpus cache
evals/                synthetic fixtures (web, evm, solana, kb, recon)
tests/                219 adversarial regression tests
```

## 6. The 22 lenses

A **lens** is an attacker persona with concrete moves, not a checklist. Each says *what to
try*, e.g. "as first depositor, donate to inflate the exchange rate so the next depositor
rounds to zero shares."

- **Contract (12):** access-control, math-precision, economic, execution-trace,
  invariant-state, periphery-integration, first-principles, asymmetry, boundary,
  numerical-gap, trust-gap, flow-gap
- **Accounting (4):** share-exchange-rate, temporal-cohort, liquidation-solvency,
  cross-chain-state
- **Web/infra (5):** web-api, auth-session, recon-infra, credential-leak, race-condition
- **Circuits (1):** zk-circuit

`ih-lens-dispatch` selects **only lenses the graph justifies** — no ZK lens on a project
with no circuits — assigns each an owner and an *independent verifier at plan time*, and
blocks any lens whose required tool is missing.

---

## 7. The knowledge base — CVE, DeFi hacks, and 0xsimao findings

This is the part most worth understanding, and the most commonly misunderstood.

### Why it exists

Without it, the AI improvises hypotheses from whatever it notices. With it, **every target
is matched against things that have actually happened.** Most real findings are not novel
inventions — they are a known bug class in a new place, reached by a path nobody checked.

### The three corpora

| Corpus | What it is | How it arrives |
|---|---|---|
| **DeFi incident database** (`kismp123/DeFi-Security-Incident`) | ~800 real exploits, 2020–2026, by year and ~25 vuln classes, with post-mortems and PoCs | `ih-kb-sync --fetch` (git clone) |
| **CVE-PoC corpus** (`trickest/cve`) | Public CVEs with links to proof-of-concept exploits, by year | `ih-kb-sync --fetch` (git clone) |
| **Researcher findings** (0xsimao and similar) | Individual audit write-ups — the highest signal, because each is a *confirmed* bug whose root cause a human explained | **you fetch locally**, then `ih-findings-ingest` |

### Why 0xsimao is handled differently — read this carefully

`0xsimao.com/findings` is a **website, not a git repository**. There is nothing to clone.
Many audit hosts also block outbound web traffic by policy, and scraping terms vary by
site. So there is no automatic fetch and **that is deliberate**, not an oversight.

The flow is explicitly two-step and local:

```bash
# 1. On a machine with network access, mirror pages you are entitled to read
wget -r -l2 -k -p https://0xsimao.com/findings -P ./simao

# 2. On the audit host, turn that directory into knowledge-base entries
ih-findings-ingest ./simao --source 0xsimao --output knowledge/cache/simao.json
```

`ih-findings-ingest` parses HTML with Python's built-in parser — scripts and styles are
**discarded, never executed** — and markdown. It skips index/nav stubs.

### How "configuration" actually works

There is no config file to edit. The wiring is: **directory in → normalized index out →
matched against your target.**

```
  corpora on disk                  one JSON index                  your target
 ┌───────────────────┐            ┌──────────────┐            ┌──────────────┐
 │ DeFi incidents    │─ kb-sync ─▶│              │            │              │
 │ CVE records       │─ kb-sync ─▶│  index.json  │─ kb-match ▶│ graph.json   │
 │ 0xsimao writeups  │─ ingest ──▶│              │            │              │
 └───────────────────┘            └──────────────┘            └──────────────┘
                                                                     │
                                                          ranked leads, each
                                                          routed to a lens
```

Every entry is normalized to the same shape regardless of source. A real one:

```json
{
  "id": "0xsimao:rounding-direction-on-withdrawal-favours-the-caller",
  "source": "0xsimao",
  "vuln_class": "accounting",
  "lenses": ["invariant-state", "math-precision"],
  "severity": "high",
  "poc_refs": ["https://…/report/1"],
  "keywords": ["rounding", "direction", "withdrawal", "vault", "shares", …]
}
```

The `lenses` field is the important one. The ingester reads the write-up, recognises the bug
class, and **routes it to the lens that owns it** — a rounding write-up reaches
`math-precision`, a stale-price write-up reaches `trust-gap`. So history does not sit in a
folder; it is delivered to the specialist who can use it.

### How it is used during a hunt

`ih-kb-match` scores your target's graph — node kinds, labels, properties — against every
entry's keywords and vuln class, boosting same-chain history. Verified example: run against
an analysed Solidity vault, the rounding write-up scored **3.0**, matching on
`shares`/`division`/`vault`. That contract does have a rounding bug.

Each match becomes an **`inferred` observation** carrying its source URL, plus a hypothesis
family for the relevant lens at G5.

### The hard rule

**A knowledge-base match is a lead, never a finding.** It says "this shape has bitten
someone before, go look." Reachability and impact *on your target* still have to be proven
by the lens and attacked by the verifier. A match cannot set status, raise severity, or
substitute for evidence.

### Two honest limits

- **It transfers patterns; it does not invent bug classes.** No corpus match discovers a
  category nobody has published. Novelty comes from the lenses reasoning about *your*
  system's economics and composition, and from `ih-chain` combining proven findings into a
  path nobody examined whole.
- **Corpora are never committed.** They live in gitignored `knowledge/cache/`, so the repo
  stays small and upstream licences stay with upstream. Re-run the sync before a campaign.

---

## 8. Running a real job

```bash
pip install -e .
ih-banner                # identity + what this install can actually do
ih-self-audit            # the skill verifies its own wiring
ih-check-capabilities    # which tools are installed, what each gap blocks
```

Then:

```bash
# G0 — write case.json (authorization, scope, expiry, limits), then validate
ih-inventory --scope case.json --output inventory.json

# G2/G3 — model the target
ih-solidity-analyze --scope case.json --root src --output leads.jsonl   # contracts
ih-recon-normalize nmap.xml --scope case.json --output recon.jsonl      # infra
ih-normalize leads.jsonl --output graph.json

# G5 — ground and dispatch
ih-kb-sync --fetch
ih-kb-match --graph graph.json --index knowledge/cache/index.json
ih-lens-dispatch --graph graph.json --actor alice --actor bob --output plan.json
ih-lens-bundle --dispatch plan.json --output-dir bundles
ih-evidence bundles --case-id … --snapshot-id … --producer bundler --output bm.json

# G8/G9 — converge, score, release
ih-converge findings.json --output converged.json
ih-cvss "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"
ih-evaluate-case --case-manifest case.json --graph graph.json --findings findings.json \
  --coverage coverage.json --manifest bm.json --evidence-root evidence --release
```

Exit 0 from `ih-evaluate-case --release` means releasable. Exit 1 means not done.

## 9. Rules you must not break

1. **No target without written authorization.** No URL, repo, or RPC endpoint implies
   permission. G0 is a hard stop, not a formality.
2. **Never mark work "excluded" because you ran out of time.** `excluded` means *outside the
   engagement*. Skipped work is `blocked` or `uncovered` so it stays visible as debt. The
   validator rejects violations — this is the single easiest way to fake a clean audit.
3. **A verifier may not verify their own finding.** Enforced in code.
4. **Incomplete work is never a clean bill of health.** Release verified findings *plus* a
   separate coverage-debt inventory.
5. **The race runner refuses real funds.** It cannot enforce a monetary ceiling, so it
   declines rather than guess.

## 10. Maintaining it

- `ih-self-audit` — 11 structural checks: every lens dispatchable, every command resolves,
  every documented path exists, every script has a test. **Run this after any change.**
- `python -m unittest discover -s tests` — 219 tests, must stay green.
- CI runs both on every push (`.github/workflows/validate.yml`).

Adding a lens: write `references/lenses/<name>.md` with `**Role.**`, `## Attack surfaces`,
and `## Proof fields`; register it in `LENSES` in `scripts/lens_dispatch.py`. The self-audit
fails if you do one without the other.

## 11. Honest state of things

**Strong:** audit discipline and anti-fabrication; multi-chain breadth (12 families); web
recon parsing real tool output (nmap XML, httpx, ffuf, gobuster, HAR, Burp); CVSS matching
the official calculator; the Solidity analyzer detecting 6/6 planted bugs with
false-positive suppression proven by test.

**Unproven:** raw bug-finding recall against a *real third-party protocol*. The lens prompts
are a good-faith synthesis, not battle-tested across paid engagements. Detection rate on our
own fixture is a floor, not proof of field performance.

**Known limits:** the Solidity analyzer is lexical, not a compiler — it will not catch
economic logic or cross-contract composition (that is the lens's job). All 12 chain adapters
are methodology-only Tier 3: IH tells the agent how to think and hands it no native tool, so
you supply Foundry/Anchor/etc. or it becomes recorded coverage debt.

The most valuable next step is pointing this at a known-vulnerable public codebase where
someone else already found the bugs, and comparing.
