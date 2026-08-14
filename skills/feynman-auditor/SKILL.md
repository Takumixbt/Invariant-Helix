---
name: feynman-auditor
description: Deep business-logic bug finder using the Feynman technique. Language-agnostic — Solidity, Move, Rust, Go, C++, TypeScript, or any codebase. Questions every line, every ordering choice, every guard, and every implicit assumption to surface logic bugs that pattern-matching misses. One half of the Helix alternating loop. Triggers on /feynman, feynman audit, or deep logic review.
---

# Feynman Auditor

The first half of Helix's alternating loop (`references/methodology.md`). Finds
bugs pattern-matching cannot: if you cannot explain WHY a line exists, you do not
understand the code — and where understanding breaks down, bugs hide.

**Language-agnostic.** Logic bugs live in the reasoning, not the syntax. Detect
the language, adapt the vocabulary (contract/module/package, modifier/guard/
middleware, `msg.sender`/`&signer`/`ctx`), keep the questions identical.

> Obeys `references/shared-rules.md` for the finding format, severity, and the
> anti-hallucination protocol — this file adds the question framework and the
> process.

## Core rules

```
RULE 0  QUESTION EVERYTHING, ASSUME NOTHING.
        Every line exists because a developer made a decision. Question it.
RULE 1  EVIDENCE-BASED ONLY.
        Every finding: the exact line(s), the question that exposed it, a
        concrete scenario, and why the code fails in that scenario.
RULE 2  COMPLETE COVERAGE.
        Every function in scope. Bugs hide in the code everyone assumes correct.
RULE 3  NO PATTERN MATCHING.
        Don't fall back to "this looks like reentrancy." Reason from first
        principles about what THIS specific code does.
RULE 4  CROSS-FUNCTION REASONING.
        A line correct in isolation may be wrong in context. Consider how
        functions interact and share state.
```

---

## The Feynman question framework

For every function, apply these categories. You need not ask every question of
every line — use judgment (state-changing lines → heavy on ordering + assumptions;
guards → purpose + consistency; external calls → assumptions + returns; math →
boundaries).

### Category 1 — Purpose (WHY is this here?)

```
Q1.1  Why does this line exist? What invariant does it protect?
      → Can't name the invariant? It's dead code, or it guards something
        undocumented you must find.
Q1.2  What if I DELETE this line? Nothing breaks → dead. Something breaks → you
      found what it protects. Something SHOULD break but doesn't → missing dependency.
Q1.3  What specific attack/edge motivated this check? Trace zero/empty/max
      through the whole function.
Q1.4  Is this check SUFFICIENT? `amount > 0` doesn't stop dust griefing;
      `caller == owner` doesn't stop key compromise; a bounds check doesn't stop
      off-by-one within bounds.
```

### Category 2 — Ordering (WHAT IF I MOVE THIS?)

```
Q2.1  What if this executes BEFORE the line above? Would a different order allow
      state manipulation? (validate-then-act violations, reentrancy windows)
Q2.2  What if this executes AFTER the line below? Does delaying it create an
      inconsistent-state window a callback can exploit?
Q2.3  First line that WRITES state vs last line that READS state — is there a
      gap? Reads after writes see stale data; writes before validation leave
      dirty state on abort.
Q2.4  If this function ABORTS halfway, what state/side-effects persist?
      (external calls already made, events emitted, cross-module writes)
Q2.5  Can the ORDER in which users call this matter? Front-running, races,
      behavior dependent on another user's prior call.
```

### Category 3 — Consistency (WHY does A have it but B doesn't?)

```
Q3.1  If functionA has a guard and functionB doesn't — WHY? List ALL functions
      that write the same state; every one should have consistent access control
      unless there's an explicit reason. The odd one out is the bug.
Q3.2  If deposit() checks X, does withdraw()? Pair analysis: deposit/withdraw,
      stake/unstake, mint/burn, borrow/repay, open/close, add/remove. The inverse
      must validate at least as strictly.
Q3.3  Same parameter P in two functions — both validate it? If not, one is wrong.
Q3.4  If A emits an event, does B (doing similar work)? Missing events desync
      off-chain systems.
Q3.5  If A uses overflow-safe math, does B? Inconsistent protection = the
      unprotected one overflows.
```

### Category 4 — Assumptions (WHAT IS IMPLICITLY TRUSTED?)

```
Q4.1  What does this assume about THE CALLER? EOA vs contract vs proxy vs
      address(0)? Enforced or just assumed? What if the caller is the system itself?
Q4.2  What about EXTERNAL DATA it receives? Tokens: fee-on-transfer, rebasing,
      odd decimals, silent-false? API/input: malformed, empty, adversarial?
Q4.3  What about CURRENT STATE? "Never called when paused" — is it enforced?
      "Balance always sufficient" — who guarantees it? "Already initialized" —
      what if not?
Q4.4  What about TIME/ORDERING? Timestamp manipulation, stale deadline, time=0,
      out-of-order events.
Q4.5  What about PRICES/RATES/EXTERNAL VALUES? Manipulable same-tx? Stale oracle?
      Value=0 or MAX? Precision mismatch between source and consumer?
Q4.6  What about AMOUNTS/SIZES? amount=0? MAX? amount=1 (dust)? exceeds available?
      empty collection? millions of entries?
```

### Category 5 — Boundaries & edges (WHAT BREAKS AT THE EDGES?)

```
Q5.1  FIRST call / empty state — first depositor, div-by-zero when total=0,
      share/ratio inflation, uninitialized treated as valid.
Q5.2  LAST call / exhaustion — last withdraw, dust that can't be extracted,
      rounding that traps value, invariant broken by last-element removal.
Q5.3  TWICE in rapid succession — re-init, double-spend, double-count, same-block
      double-call.
Q5.4  Two DIFFERENT functions in one context — borrow in A, manipulate in B,
      repay in A. Callback patterns where control flow is non-linear.
Q5.5  System ITSELF as a parameter — transfer to self, compare with self, both
      sender and receiver.
```

### Category 6 — Return values & error paths

```
Q6.1  What does it return? Who consumes it? Does the language even FORCE a check?
      (Solidity low-level call bool often unchecked; Go `_` swallows errors.)
Q6.2  The ERROR/ABORT path — side effects before the error? Info leak? Attacker
      can force targeted errors (griefing/DoS)? Cleanup correct?
Q6.3  If an external call fails SILENTLY, is it caught or swallowed?
Q6.4  Is there a path with NO return and NO error? Fall-through returning zero
      values, missing else/match arm.
```

### Category 7 — Reordering & multi-transaction state

**Part A — external-call reordering (within one tx):** for every external call,
try swapping it with the adjacent state update. The direction that *reverts*
tells you which ordering the code depends on; the direction that *works cleanly*
tells you which an attacker can exploit. Ask: "what can the callee do with the
state at THIS exact moment?" — including re-entering a *different* function that
reads not-yet-updated state.

**Part B — multi-tx state corruption (across time):**

```
Q7.5  Call with X, then again with Y — does the second call account for the
      first's state change, or assume fresh state? (deposit when totalSupply≠0,
      borrow against updated vs stale collateral)
Q7.6  After T1 changes state, does T2 revert-when-it-shouldn't or succeed-when-it-
      shouldn't? Test T2 after MANY T1s, extreme-value T1, cross-user T1,
      partially-reverted T1.
Q7.7  Does accumulated state from MANY calls reach a state no single call can?
      Compounding rounding (1 wei/call × 1000 = real loss), monotonic counters
      hitting a ceiling, stale reward accumulators, dust fragmentation blocking
      future ops. KEY: does SUM(individual ops) == the aggregate op? If not, the
      accumulator is path-dependent and exploitable.
Q7.8  Can an attacker craft a SEQUENCE reaching a state no normal path produces?
      deposit-borrow-withdraw-liquidate leaving bad debt; stake-unstake-restake
      compounding errors. The attacker CHOOSES order, amounts, timing — test
      adversarial sequences, not happy paths.
```

---

## Process

**Phase 0 — Attacker mindset (before reading a line).** Answer four questions;
their answers tell you WHERE to spend time: (1) worst thing an attacker can do
here? (2) what's novel/custom (not a battle-tested fork)? (3) where does value
sit? (4) what's the most complex interaction path? Functions appearing in
multiple answers get audited first and deepest. Output: the attacker's hit list.

**Phase 1 — Scope & inventory.** List every module and every entry point. Build
the **Function-State Matrix**: `| Function | Reads | Writes | Guards | Calls |`.
Identify inverse pairs (deposit/withdraw, etc.). This matrix is your map for
Category 3.

**Phase 2 — Per-function deep dive.** Run the interrogation on each entry point
(priority order from Phase 0). For each suspect line, record the question, the
verdict (SOUND | SUSPECT | VULNERABLE), and — if suspect/vulnerable — the
concrete scenario.

**Phase 3 — Cross-function analysis.** Using the matrix: guard consistency
(group by written state, flag the sibling missing a guard), inverse-operation
parity, state-transition integrity, value-flow conservation (value in == value
out).

**Phase 4 — Synthesize raw findings.** For each SUSPECT/VULNERABLE: the question,
the step-by-step scenario, the exact code, why it fails, the impact, a severity,
a minimal fix. Save to `.audit/findings/feynman-pass{N}-raw.md`.
**These are hypotheses, not results. Do not present raw findings to the operator.**

**Phase 5 — Verification gate (MANDATORY).** No C/H/M finding ships unverified.

| Severity | Required | Method |
|---|---|---|
| CRITICAL | PoC required | demonstrate value loss / permanent DoS with concrete numbers |
| HIGH | trace + PoC recommended | confirm the broken invariant is reachable |
| MEDIUM | code trace minimum | confirm mechanism, not mitigated elsewhere |
| LOW | inspection | is the line/function real? |

Per finding, check: does the cited code exist at those lines? is the mechanism
correct (trace the actual math/logic)? are there mitigating factors the finding
missed (guards in callees, upstream checks, language-level safety)? is severity
accurate for the ACTUAL impact?

**Common Feynman false positives** (kill these before they ship):
1. "Missing authorization" that exists in a different layer (router/middleware enforces it first).
2. "Rounding drift" cleaned by downstream code (input is always a clean multiple).
3. "No validation" that errors downstream (the callee validates, just with a confusing error).
4. "Unbounded loop" bounded by design or economics.
5. Severity inflation — claims CRITICAL (value loss) but a safety check caps it at MEDIUM (revert/DoS).
6. Language safety ignored — claims overflow where the language aborts by default (Move, Solidity ≥0.8).

Save survivors to `.audit/findings/feynman-verified.md` with a verification
summary table (ID | original severity | verdict | final severity), the
Function-State Matrix, guard-consistency and inverse-parity results, the verified
findings (shared-rules.md format), the false positives eliminated (with why), and
the downgrades. **Only the verified file is presented.**

---

## Hand-off to the loop

When run inside the alternating loop, Feynman feeds the State auditor:
- every SUSPECT that involves two related storage values → a coupled-pair target
- every ordering concern (Q2, Q7) → a mutation-ordering target

And it receives from State: every coupled-state gap becomes a fresh Feynman
interrogation point ("WHY does this operation not update the paired value?").
Carry the hand-off explicitly at the top of each raw file.
