---
name: state-inconsistency-auditor
description: Finds coupled-state desync bugs — where an operation mutates one piece of coupled state without updating its dependent counterpart, causing silent corruption or reverts in later operations. Language-agnostic. The second half of the Helix alternating loop. Triggers on /state-audit, state inconsistency audit, or coupled state audit.
---

# State Inconsistency Auditor

The second half of Helix's alternating loop (`references/methodology.md`).
Systematically finds bugs where an operation mutates one piece of coupled state
without updating its dependent counterpart. Structural, exhaustive — it maps
before it hunts.

> Obeys `references/shared-rules.md` for finding format, severity, and
> anti-hallucination. This file adds the coupled-state process.

## The abstract pattern

Every system has **coupled state pairs** — two or more stored values that must
maintain an invariant with each other. When an operation changes one side
without adjusting the other, the invariant breaks, and future operations that
read both produce incorrect results.

```
balance ↔ checkpoint          shares ↔ any per-share derived value
stake ↔ rewardDebt            principal ↔ cumulative index
collateral ↔ debt/health      totalSupply ↔ sum of balances
liquidity ↔ fee-growth        position ↔ cached health factor
voting power ↔ snapshot       numerator ↔ denominator
```

**The bug:** operation X correctly updates State A but fails to adjust the
coupled State B. B is now stale relative to A.

## Core rules

```
RULE 0  MAP BEFORE YOU HUNT. You can't find a missing update if you don't know
        what update is required.
RULE 1  EVERY MUTATION PATH MATTERS. If 5 functions modify a variable, all 5
        must update the coupled state. 4 do, 1 doesn't → that's the bug.
RULE 2  PARTIAL OPERATIONS ARE THE #1 SOURCE. Full removals usually reset
        everything; partial ops ("reduce by X") forget to proportionally reduce
        the coupled state.
RULE 3  COMPARE PARALLEL PATHS. transfer() and burn() both reduce balance — both
        must update the same coupled set.
RULE 4  DEFENSIVE CODE MASKS BUGS. `x > y ? x - y : 0`, `min(computed, available)`
        silently hide broken invariants. Red flags, not safety nets.
RULE 5  EVIDENCE ONLY. Every finding: the coupled pair, the breaking op, a
        concrete trigger sequence, the downstream consequence.
```

---

## Process

### Phase 1 — Map all coupled state pairs

For every storage variable ask: **"What other values MUST change when this
changes?"** Build the Coupled State Dependency Map:

```
PAIR: userBalance[u] ↔ checkpoint[u]
  Invariant: checkpoint reflects balance at last update
  Mutation points: deposit(), withdraw(), transfer(), burn(), liquidate()
```

Look for: any per-user value paired with a per-user accumulator; any balance
paired with a snapshot/checkpoint; any numerator with its denominator; any total
with the components that sum to it; any cached computation with its inputs; any
value stored at time T later used with a value from T+1.

### Phase 2 — Find every mutation of each state

For each variable from Phase 1, list **every** function and path that modifies
it: direct writes, `+=`/`-=`, deletions/resets, indirect (`_mint`/`_burn`/
`_transfer`), implicit (rebasing), batch loops, callback/hook side effects.
Build the Mutation Matrix and mark `???` where you haven't confirmed the coupled
state is also updated:

```
| State        | Function     | Mutation        |
| checkpoint[u]| deposit()    | full reset      |
| checkpoint[u]| transfer()   | ??? CHECK THIS  |
| checkpoint[u]| liquidate()  | ??? CHECK THIS  |
```

The `???` entries are your primary audit targets.

### Phase 3 — Cross-check (the core audit)

For every (operation, state) pair: *"This modifies State A. Does it ALSO update
every coupled state that depends on A?"*

```
□ Full removal (A→0): every coupled state reset?
□ Partial removal (A decreases): every coupled state proportionally reduced?
□ Increase (A grows): every coupled state proportionally increased?
□ Transfer (A moves): coupled state moved too?
□ Deletion (mapping entry removed): paired mapping entry also removed?
□ Batch: coupled state updated per-iteration or only once?
```

Trace the full path: read the function, search for any write to State B within
it, any internal call that writes B, any modifier/hook that writes B. None found
→ confirmed finding. **If ANY path updates A without B → FINDING.**

### Phase 4 — Ordering within functions

Trace the exact order of multiple state changes in one function. At each step:
"are all coupled pairs still consistent? does step N use a value step N-1
invalidated? if I read the pair right here, does the invariant hold? if an
external call happens between these steps, can the callee observe inconsistent
state?" Common: claim rewards before reducing stake (rewards on old stake);
update index after modifying supply (index uses stale supply); read cached price
after changing position.

### Phase 5 — Compare parallel paths

Find operations achieving similar outcomes differently — transfer/burn,
withdraw/liquidate, partial/full, normal/emergency, single/batch,
user/keeper-initiated. Tabulate which coupled state each updates:

```
| Coupled State | withdraw() | liquidate() | emergencyWithdraw() |
| balance       | ✓          | ✓           | ✓                   |
| checkpoint    | ✓          | ✗ MISSING   | ✗ MISSING           |
| rewardDebt    | ✓          | ✗ MISSING   | ✗ MISSING           |
```

Any column that skips a coupled update → FINDING.

### Phase 6 — Multi-step user journeys

Simulate: enter position → time passes / external state evolves → PARTIAL
modification (coupled state may break here) → more time → operation reading the
coupled state. At the last step, is it valid given the partial change? Key
sequences: deposit→partial withdraw→claim; stake→unstake half→restake→unstake
all; open→add collateral→partial close→check health; provide liquidity→swap→
remove liquidity.

### Phase 7 — What masks the bug

Flag defensive code that converts a loud failure into a silent one:

```
MASK 1  x > y ? x - y : 0          why would x < y? if the invariant held, never.
MASK 2  try target.call() {} catch {}   the revert from broken state, swallowed.
MASK 3  if (value == 0) return;    skips the computation on broken-state zero.
MASK 4  min(computed, available)   caps the over-count instead of fixing it.
MASK 5  SafeMath without root-cause fix   stops the underflow revert, not the cause.
MASK 6  mapping[key] default 0      masks a deleted entry whose pair still exists.
```

Each instance: trace whether it hides a real inconsistency. The invariant is
still broken — the symptom is just suppressed.

### Phase 8 — Verification gate (MANDATORY)

No C/H/M ships unverified. **Method A (code trace):** read the breaking function,
trace every internal call for a hidden coupled update, check modifiers/hooks/base
overrides, confirm no event/callback reconciliation. **Method B (PoC):** write a
test in the project's framework, execute the trigger sequence, assert the coupled
state is inconsistent after the op and that a later op produces a wrong result.

**Common state false positives:**
1. **Hidden reconciliation** — the pair IS updated via an internal chain you missed (`_beforeTokenTransfer` hook).
2. **Lazy evaluation** — intentionally stale, reconciled on next read (an `_updateReward()` modifier runs before every function).
3. **Immutable after init** — the pair is set once; A never changes either.
4. **Designed asymmetry** — the two are intentionally not coupled the way you assumed (read the docs/comments).

Save survivors to `.audit/findings/state-verified.md` with the dependency map,
the mutation matrix, the parallel-path table, a verification summary, and the
verified findings (shared-rules.md format). **Only the verified file is
presented.** Raw goes to `.audit/findings/state-pass{N}-raw.md`.

---

## Red-flags checklist

```
□ A function modifies a base value but has no write to its coupled state
□ transfer vs burn handle coupled state differently
□ a claim/collect step runs before a reduce/remove step with no reconciliation
□ partial ops exist alongside full ops, but only the full op resets coupled state
□ a defensive ternary/min() in a computation over two coupled values
□ delete/reset of one mapping but not its pair
□ a loop accumulates into a shared coupled value without per-iteration adjustment
□ an emergency/admin function bypasses the normal update path
□ a migration copies State A but not State B
□ a callback/hook modifies A but the caller doesn't know to update B
```

## Hand-off to the loop

State feeds Feynman: every confirmed or suspected desync → "WHY does this
operation not update the paired value? was it a deliberate design or an
oversight?" — a first-principles interrogation point. And it receives from
Feynman: every ordering concern and every two-related-values suspect becomes a
coupled-pair target. Carry the hand-off explicitly at the top of each raw file.
The loop alternates until neither produces a new finding (max 6 passes).
