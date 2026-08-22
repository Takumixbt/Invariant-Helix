# Convergence — turning a swarm's raw output into signal

When Helix runs deep, many actors produce many raw findings, and they overlap.
Depth without convergence is noise. This is the orchestrator's mandatory pipeline
(strong tier) between the actors returning raw findings and the gate
(`judging.md`). It is a set of **hard gates**, run in order, and nothing reaches
the report that skips them.

```
   raw findings from all actors + the alternating loop
        │
        ▼
   1. MERGE (wide → narrow)      collapse duplicates by description, then location
        ▼
   2. FUNCTION ISOLATION          one finding must not smuggle in a second bug
        ▼
   3. FIX PRESERVATION            keep the strongest fix; offer distinct alternatives
        ▼
   4. COMPLETENESS                every in-scope surface accounted for (found or cleared)
        ▼
   5. LEAD PROMOTION              promote the leads that cross-corroborate
        ▼
   6. CONVERGENCE CHECK           did this pass add anything? if yes, loop again (max 6)
        │
        ▼
   → the GATE (judging.md), then verification, then report
```

---

## Gate 1 — Merge (wide description first, then function-level)

Two passes, in this order:

- **Wide-description merge:** group findings whose *root cause described in plain
  words* is the same, even if the actors phrased them differently or flagged
  different lines. Two actors describing "the withdraw path updates balance but
  not the reward accumulator" are one finding, not two. Merge to the clearest
  statement; union their evidence.
- **Function-level second pass:** within a function, collapse findings that share
  a `group_key` (`target | location | bug_class`). Keep the highest-confidence,
  best-evidenced version; carry every actor's name in `lens:` so the corroboration
  is visible (multiple actors on one finding raises confidence — see Gate 5).

Merging **raises** confidence (independent actors converged); it never loses
evidence. If two "duplicates" actually describe *different* mechanisms at the same
location, they are **not** duplicates — split them back out (Gate 2).

**HARD — never merge across different `location:` values.** Same bug_class,
same-sounding description, different function/endpoint = different bugs. This
holds even when one clearly caused the other (write to `chain_with:`, not a
merge). The wide-description pass groups by *plain-words root cause*, not by
*bug_class label* — two actors can tag the same location with different class
names and still be one finding; two actors can share a class name at different
locations and still be two findings. When in doubt, keep them separate — Gate 5
promotes real corroboration back together via `lens:` counting, so splitting
costs nothing; merging across locations silently drops a finding for good.

## Gate 2 — Function isolation

Each finding describes **exactly one** bug. A raw finding that bundles "and also
this other thing is wrong here" is split into separate findings, each with its own
mechanism, trigger, and fix. This matters for the gate (each mechanism must pass
refutation independently) and for the report (each is a separate submission). A
finding that cannot be stated as one mechanism → one impact is not yet a finding.

## Gate 3 — Fix preservation

For each surviving finding, keep the **strongest** fix, and where more than one
real remediation exists, list the distinct options (not restatements) so the
operator/client can choose. A fix that would break legitimate functionality is
noted as such. Never drop a finding because "the fix is unclear" — a real bug with
an unclear fix is still a real bug; say the fix is non-trivial and why.

**Distinctness check (HARD GATE, before writing the final `fix:`).** Collect every
raw `fix:` any actor proposed for this (target, location). Two fixes are
distinct if they differ in the called function/expression, the check direction
(validate/restrict/ban), or the parameter checked — not if they're the same fix
worded differently.

- **1 fix (or all restatements of one idea)** → write it as the single `fix:`.
- **≥2 distinct fixes** → print both, verbatim from the raw actor output, no
  paraphrase:

  ```
  **Fix (Option A — <one-word label>)**: <verbatim diff/snippet from actor N1>
  **Fix (Option B — <one-word label>)**: <verbatim diff/snippet from actor N2>
  ```

  Silently picking one and discarding the other is the failure mode this gate
  exists to catch — a merged finding with 2+ distinct raw fixes and only 1
  printed is a violation, fix it before the report ships.

## Gate 4 — Completeness

Before promotion, confirm **every in-scope surface is accounted for** — either a
finding/lead was produced for it, or it was examined and cleared. A surface that
no actor covered is **coverage-debt**, named explicitly (`local-tooling.md`),
never a silent gap. The x-ray entry-point list (web3) and the recon surface map
(web) are the checklists: every entry point / every endpoint is either hunted or
flagged as unhunted. This is what separates "we audited it" from "we ran some
agents."

**HARD GATE — this must be a counted number, not a claim.** Before the report
prints, list every unique (target, location) tuple that appears in *any* raw
actor output (findings or leads), count it, then count how many survive into
the final merged set (as a finding, a lead, or an explicit coverage-debt line).
Print both numbers inline, before the report body:

```
Completeness: N unique (target, location) in raw → N covered in final.
```

If the two numbers don't match, something was silently dropped in Gate 1's
merge — go back and find it. This is the same discipline pashov's
solidity-auditor enforces mechanically; Helix has no script to force it, so the
orchestrator prints the count itself as a literal line, not a summary sentence
like "coverage looks complete."

## Gate 5 — Lead promotion

Promote the leads that earned it (from `judging.md`, applied here before the
gate):

1. **Cross-actor convergence** — 2+ actors independently flagged the same area and
   it was demoted, not rejected → promote (confidence ~75).
2. **Cross-component echo** — a root cause confirmed in component A appears
   identically in component B → promote in B (confidence ~75).
3. **Partial-path completion** — the only weakness is an incomplete trace, but the
   path is reachable and unguarded → promote (confidence ~75).
4. **Crossover chain** — a web finding reaching on-chain power (or the reverse) →
   chain and promote to the combined severity (`strands/crossover.md`).

## Gate 6 — Convergence check (the loop's terminator)

Did this pass produce **any** new finding, lead, or merge? 
- **Yes** → there may be more to find. Feed the new suspects back: a new state gap
  becomes a feynman target, a new logic suspect becomes a state target, a new web
  finding becomes a crossover input. Run another targeted pass.
- **No** → **converged.** Stop.

Hard cap: **6 passes.** Depth is bounded so a run terminates; rigor comes from the
alternation and the gates, not from looping forever.

---

## Why this is mandatory when Helix runs deep

The lean roster (few actors) overlaps little, so convergence is light. The deep
roster (15+ actors + the loop over 6 passes) overlaps **heavily** — invariant,
execution-trace, gap-hunter, and feynman will all touch the same critical function
from different angles. That's the point: multiple independent confirmations of a
real bug, and multiple independent chances to catch one. But it means the raw pile
is full of near-duplicates and partial traces. **Convergence is the price of
depth.** Skip it and the operator drowns; run it and the swarm's redundancy becomes
its rigor — the same bug found four ways is a bug you can trust, stated once.
