# The binding matrix — the forcing function Helix was missing

`convergence.md` admits the gap in plain words: *"This is the same discipline
pashov's solidity-auditor enforces mechanically; Helix has no script to force
it."* This file is that forcing function.

Every other actor in Helix **hunts**: it forms a hypothesis and chases it. That
finds deep bugs and misses shallow ones, because a hunter stops when the thread
gets interesting. The binding matrix does the opposite — it **fills a grid**. No
hypothesis, no judgment, no stopping early. You enumerate every cell, and the
bugs fall out of the empty ones.

This was derived by reverse-engineering a commercial audit engine's output on a
14.5k-LOC Solana protocol (275 raw findings → 92 → 50 groups). Its entire
taxonomy collapses into six axes, and **26% of everything it found sat on axis 1
alone**. That is not a coincidence about one tool. It is what unauthenticated
data looks like at scale.

---

## The core question

> For every value the handler **uses**, and every asset branch the handler
> **takes**: who chose it, and what stops them choosing differently?

A value is **authenticated** if the caller cannot change it without invalidating
something: a proof public input, a signer, a PDA seed, a stored record, a
hardcoded constant. Everything else is **caller-supplied**, and every
caller-supplied value that reaches a fund-moving decision is a candidate.

The classic failure is not a missing check. It is a check that exists, and
**tests a value the attacker also supplies**. Write that in the matrix as
`SELF-REFERENTIAL` — it is the highest-yield cell in the grid and the easiest to
read past, because the code looks defended.

---

## The six axes

Enumerate each axis across **every** instruction. Do not skip an instruction
because it looks boring; the boring ones are where guards were never propagated.

```
1  AUTHENTICATION   every (value, handler): proof-bound | signer-bound | seed-bound
                    | record-bound | constant | CALLER-SUPPLIED
2  REPRESENTATION   every (asset, branch): native | wrapped | SPL | Token-2022
                    — does each branch exist, and do they agree?
3  LIFECYCLE        every account create/close vs every obligation still pending
                    against it (rent, requests, queued withdrawals)
4  AUTHORITY        bootstrap, rotation, policy mutation, and who can act mid-flight
5  ARITHMETIC       narrowing casts, saturating-vs-checked, truncating division,
                    and any fallback that swallows overflow into a valid-looking value
6  CPI ROLES        every account handed to an external program: derived and checked
                    locally, or passed through positionally on trust?
```

### Axis 1 is the one that pays

Build one row per handler argument and per struct field the handler reads:

| value | used for | authenticated by | caller can change? |
|---|---|---|---|
| `swap_amount` | how much leaves the vault | proof public input | no |
| `deadline` | expiry check | *nothing* | **yes — and it is the party being constrained** |
| `withdrawal_id` | which slot PDA | seed only | yes, picks a different slot |

Any row where "authenticated by" is empty and the value reaches a transfer, a
mint, an account derivation, or a guard, is a finding or a verified negative.
There is no third outcome, and "it's probably fine" is not one of them.

### The sibling rule, applied mechanically

Helix already knows the sibling rule. The matrix makes it unskippable: when a
guard appears in **one** cell, grep the codebase for that guard's identifier and
mark every sibling handler that should have it and does not. A guard the team
wrote themselves, with a comment saying why, that appears in exactly one of six
call sites, is the strongest finding shape there is — the team has already
conceded the threat model in their own words.

---

## The five phases (order is not optional)

**1. ENUMERATE.** Build the grid. No severity, no judgment, no writing prose.
Coverage number goes here: cells filled / cells total. Print it.

**2. EMIT EVERYTHING.** Every empty cell becomes a raw candidate, including ones
that feel trivial. **Do not self-censor at this stage** — this is precisely where
a hunting actor loses. On the reference engagement, three of the findings that
survived to the final report came out of the low/medium pile that a "only report
what matters" instinct would have suppressed.

**3. VERIFY.** Now judgment starts, and every candidate must earn its place:
- Read the **guard code**, not just the line you think is vulnerable. A candidate
  dies if a guard elsewhere in the same function contains it.
- Cite exact `file:line` against the **deployed** commit. A candidate with no
  citation is not a finding, it is a feeling.
- Verify on-chain state where the claim depends on it (is that account already
  initialised? is that authority on-curve?).

**4. SCOPE-GATE.** Against the engagement's actual rules, before anything is
written up. Kill: centralization-as-designed, pure liveness/DoS when the bounty
wants fund loss, anything already fixed on the deployed artifact, and anything
whose precondition closed at deployment.

**5. CONSOLIDATE.** Group duplicates under one canonical topic, re-severitize
against real impact and preconditions, and rank. Argue every severity in one
clause ("Medium not High, because the loss falls on the relayer, not the user").
A calibrated downgrade buys more credibility than an inflated High costs.

---

## Where the commercial engine fails, and you must not

Measured, not assumed, on the reference run:

- **It never verifies.** Every finding shipped `unreviewed`. Two of its six
  criticals were false: one for a bootstrap window that **closed at deployment**
  (one RPC call disproves it), one refuted by a guard sitting in the same
  function *with a comment explaining its purpose*.
- **It emits no `file:line`.** Symbol names only. A triager cannot check it, and
  neither can you.
- **It is scope-blind.** It rated centralization-as-designed as High on a
  fund-loss-only engagement.
- **Its prose is not evidence.** Both false positives above entered a real report
  because the reviewer trusted the write-up instead of reading the guard.

> **Rule:** a second engine's finding is a LEAD, at exactly the same trust level
> as your own first draft. Read the guard code before you file it. This is not
> optional; it is the failure that has actually happened.

Feed the engagement's scope, threat model, and exclusions in as **context
documents** where the tool supports it (v12: `v12 context upload` +
`--context-doc`). Most of the scope noise above is preventable that way, and
skipping it is an operator error, not a tool defect.

---

## Coverage gate (mirrors `convergence.md`)

Do not close the pass until you can print:

```
instructions enumerated      N / N
axis-1 rows filled           N / N   (unauthenticated: K)
representation branches      N / N   (asymmetric: K)
guards found in exactly one sibling  K   <- inspect every one
candidates emitted           N
candidates verified          N   (killed: K)
scope-gated out              K   (reason each)
```

An unexplained gap between "emitted" and "verified" is coverage debt, and it goes
in the report as coverage debt, not as silence.
