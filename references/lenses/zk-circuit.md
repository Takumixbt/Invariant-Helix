# Lens: ZK circuit

**Role.** You attack arithmetic circuits: soundness, completeness, and privacy.
**Capability:** `source_analysis`. **Domain:** circuit (Circom, Halo2, Noir, Cairo AIR).

A circuit bug is not a code bug — it is a **missing constraint**. Code that "works" on
honest inputs proves nothing: the attacker supplies the witness. Ask of every signal:
*what stops a malicious prover from setting this to anything they like?*

## Attack surfaces

- **Under-constrained signals (soundness).** The dominant ZK bug class. Any signal assigned
  with `<--` (or a hint/advice cell) but never constrained with `===`/`<==` is fully
  attacker-chosen. Enumerate every `<--` and demand its matching constraint.
- **Non-deterministic division/inverse.** `out <-- a / b` must be paired with
  `out * b === a`, plus a proof that `b != 0`. Missing either is forgeable.
- **Missing range checks.** Field elements wrap modulo p. A value assumed to be `n` bits
  must be decomposed and each bit constrained boolean (`b * (b - 1) === 0`), and the
  recomposition constrained. Otherwise "small" values can exceed the range and alias.
- **Unconstrained bit decomposition.** `Num2Bits` without the sum-check, or with `n` large
  enough that two representations map to one field element (alias attack above `p`).
- **Signal aliasing / double-spend of a nullifier.** A nullifier not bound to *all* of its
  inputs lets one secret produce two nullifiers, or two secrets collide.
- **Public/private confusion (privacy).** A signal intended private declared public, or
  leaked through a derived public output. Also: a public input not actually constrained
  into the proof is attacker-malleable at verification time.
- **Completeness failures.** Constraints so tight that valid inputs cannot produce a proof
  — a liveness/DoS bug, not a theft bug, but still a finding.
- **Trusted-setup / verifier mismatch.** Verifying key not matching the deployed circuit;
  proof-system parameters reused across circuits.
- **Edge inputs.** Zero, one, `p-1`, and the field characteristic itself. Test each against
  every constraint.

## Chain-neutral core

For each output signal, write the relation it is *supposed* to satisfy, then check the
constraint system actually enforces it. Soundness = "no false statement can be proven";
completeness = "every true statement can be proven". Name which one a finding breaks.

## Per-family notes

- **circom** — `<--` vs `<==`, `assert()` is compile-time only and constrains nothing,
  `Num2Bits`/`LessThan` misuse, unconstrained component outputs.
- **halo2** — advice cells without a gate, missing selector activation, lookup-table gaps.
- **noir** — unconstrained functions (`unconstrained fn`) whose results are trusted.
- **cairo** — AIR constraint gaps; felt252 wraparound.

## Boundary

The verifier is on-chain; the circuit is off-chain. A finding must state which side is
broken and what an attacker gains — a forged proof accepted on-chain is critical, a
completeness bug is availability.

## Proof fields

`proof: the unconstrained signal, a concrete malicious witness, and what it proves falsely`.
