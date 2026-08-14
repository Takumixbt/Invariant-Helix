# Judging — the gate every finding must pass

A raw finding is a hypothesis. This is where it becomes a result — or dies.
Every deduplicated finding passes four sequential gates. **Fail any gate →
REJECTED, or DEMOTED to a lead.** Later gates are not evaluated for a finding
that already failed.

This is the deliberate, in-order refutation that the hunt is forbidden from
doing (`shared-rules.md` § 0). During discovery you deepen the bug; here, and
only here, you try to kill it.

```
   raw finding (SUSPECT)
        │
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
