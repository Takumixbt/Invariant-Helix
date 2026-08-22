# Judging — the gate every finding must pass

A raw finding is a hypothesis. This is where it becomes a result — or dies.
Every deduplicated finding passes four sequential gates. **Fail any gate →
REJECTED, or DEMOTED to a lead.** Later gates are not evaluated for a finding
that already failed.

This is the deliberate, in-order refutation that the hunt is forbidden from
doing (`shared-rules.md` § 0). During discovery you deepen the bug; here, and
only here, you try to kill it.

## §0 — Discoverer ≠ verifier (who is allowed to run this file)

This gate is never run by the actor, pass, or lens that raised the finding.
Concretely:

- **Deep-logic loop (Feynman ↔ State):** a finding a Feynman pass raised is
  gated by the orchestrator, not re-approved by another Feynman pass. Same for
  State.
- **Parallel lens actors:** the orchestrator (strong tier) runs this file over
  every actor's output after convergence — never the actor itself, and never a
  second instance of the same lens.
- **Single-model / no-fanout collapse (`failure-modes.md` F4):** when the
  harness can't dispatch separate actors, the same agent still discovers and
  gates sequentially — but must treat them as two distinct, non-overlapping
  passes: close the discovery context (stop trying to strengthen the finding)
  before opening the gate context (start trying to kill it). Do not blend them
  into one pass that "discovers cautiously."

If you cannot name who discovered a finding, you cannot gate it yet — go back
and check convergence.md first.

```
   raw finding (SUSPECT)
        │
        ▼
   GATE 0 ── The only question ── hedged/theoretical language? ────────► DEMOTE
        │ clears (cheap pre-filter — see below)
        ▼
   GATE 1 ── Refutation ──── can a real guard block the exact step? ──► REJECT/DEMOTE
        │ clears
        ▼
   GATE 2 ── Reachability ── can the vulnerable state exist live? ────► REJECT/DEMOTE
        │ clears
        ▼
   GATE 3 ── Trigger ─────── can an unprivileged actor do it, profitably? ─► REJECT/DEMOTE
        │ clears
        ▼
   GATE 4 ── Impact ──────── is there material harm to a real victim? ──► REJECT/DEMOTE
        │ clears
        ▼
   CONFIRMED → verify with PoC/trace → verified.md
```

---

## Gate 0 — The only question that matters (a cheap pre-filter, before Gate 1)

Before running the four sequential gates, ask one question of the raw finding
as written: ***can an attacker do this right now, against a real user who took
no unusual action, causing real harm?*** This is a one-line filter — cheaper
than the four gates below — that exists because the single most common false
positive isn't a wrong mechanism, it's *hedged language describing a mechanism
that was never actually traced.* Kill on sight, before Gate 1, any finding
whose own wording contains:

```
"could theoretically..."          "in a worst-case scenario..."
"with the right preconditions..." "if an attacker were somehow able to..."
"this may allow..." / "this might permit..." (without a traced path proving it does)
"under certain conditions..." (without naming the conditions and proving they're reachable)
a reference to dead/unreachable code presented as if it were live
```

This is not a rewording exercise — a finding using this language usually means
the discovery pass never actually traced attacker → guard → consequence, it
pattern-matched a shape and described it defensively. **Demote to a LEAD and
send it back for a real trace; do not just delete the hedge words and reclassify
it as a finding.** A finding that survives Gate 0 still owes the full four gates
below — this filter catches the cheap kills, it doesn't replace refutation.

## Gate 1 — Refutation

Construct the **strongest argument that the finding is wrong.** Find the guard,
check, or constraint that kills the attack — quote the exact line and trace how
it blocks the claimed step.

- **Concrete refutation** — a specific guard blocks the exact claimed step →
  **REJECT** (or **DEMOTE** if a code smell worth investigating remains).
- **Speculative refutation** — "probably wouldn't happen", "likely intended",
  "the team surely checks this elsewhere" without finding the check → **clears**.
  A vague defense does not kill a finding; only a real, quoted guard does.

This is where the Feynman/State false-positive catalogs apply (hidden auth in
another layer, lazy reconciliation, rounding cleaned downstream, language-level
safety). If the "bug" is one of those, it dies here.

## Gate 2 — Reachability

Prove the vulnerable state can exist in a live, deployed system.

- **Structurally impossible** — an enforced invariant prevents the state from
  ever occurring → **REJECT**.
- **Requires privileged misconfiguration** — owner must misconfigure, multisig
  must collude, an admin must act against the protocol → **DEMOTE**.
- **Achievable through normal usage** — normal calls, fee-on-transfer/rebasing
  tokens, common admin actions, ordinary user sequences → **clears**.

## Gate 3 — Trigger

Prove an unprivileged (or minimally privileged) actor can execute it profitably.

- **Only a trusted role can trigger** → **DEMOTE** (report as the lower severity,
  not critical).
- **Cost exceeds extraction** — gas/capital cost > gain → **REJECT** (but
  re-check with a flash loan: if the capital is borrowable inside the tx, "needs
  $10M" is not a defense).
- **Unprivileged actor triggers profitably** → **clears**.

## Gate 4 — Impact

Prove material harm to an identifiable victim.

- **Self-harm only** — attacker loses their own funds, no other victim → **REJECT**.
- **Dust-level, non-compounding, no cascade** → **DEMOTE** to low/info.
- **Material loss to an identifiable victim** — user funds drained, protocol
  insolvent, data breached, account taken over → **CONFIRMED**.

---

## Severity adjustment after the gates

Once all four clear, adjust down for real-world friction:

- Attack needs specific timing (e.g., one-block window): **−1 level**
- Attack needs non-trivial *non-borrowable* capital for the target's value: **−1 level**
- Impact bounded (profit but not full drain): **−1 level**
- Fix already deployed on mainnet but not in the reviewed commit: **DEMOTE + note**

CVSS is computed after this adjustment (`cvss-guide.md`); the vector's severity
band and the label must agree.

---

## Lead promotion (before finalizing)

Some leads deserve promotion to findings even without a complete solo path:

1. **Cross-contract / cross-endpoint echo** — same root cause confirmed as a
   finding in component A → promote in component B where the identical pattern
   appears (confidence ~75).
2. **Multi-lens convergence** — 2+ lenses flagged the same area and it was
   demoted (not rejected) → promote (confidence ~75).
3. **Partial-path completion** — the only weakness is an incomplete trace, but
   the path is reachable and unguarded → promote (confidence ~75).
4. **Crossover chain** — a web finding that reaches on-chain power, or an on-chain
   assumption resting on a web control → chain and promote to the combined
   severity (`strands/crossover.md`).

---

## Do Not Report

These never ship (they waste the operator's credibility and the triager's time):

**Both domains**
- Theoretical issues with no reachable path on this target.
- Anything requiring the protocol/app to be already compromised.
- Best-practice deviations with no exploit (missing headers, missing NatSpec, missing events).

**Web / API**
- Self-XSS with no escalation path.
- Logout CSRF; CSRF on non-state-changing or unauthenticated actions.
- Rate-limiting that genuinely prevents exploitation in the defined threat model.
- Missing security headers with no demonstrated impact.
- Vulnerabilities only exploitable with a physical/MITM position out of scope.

**Smart contract / Web3**
- Centralization risk with no exploit path (unless the design itself is the vuln).
- Admin privileges functioning as designed.
- Gas micro-optimizations, linter/compiler suggestions.
- "Reentrancy" on a function already protected by a working `nonReentrant` guard.
- Implausible preconditions requiring owner self-sabotage.

When in doubt between DEMOTE and REJECT: if the mechanism is real but the impact
is small, DEMOTE to low/info; if the mechanism is wrong or blocked, REJECT. Never
inflate to hit a payout tier — a calibrated medium keeps the operator's
reputation; an inflated "critical" that gets closed as informational costs it.
