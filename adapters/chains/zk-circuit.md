# ZK circuit adapter

Zero-knowledge arithmetic circuits (Circom, Halo2, Noir, Cairo AIR). Tier 3,
methodology-only: no toolchain is bundled, and soundness reasoning is not lexical.

## Detection

`pragma circom`, `template `, `signal input/output`, `component main`, `nargo`/Noir
`fn main`, halo2 advice/selector definitions.

## Authority model

**The prover chooses the witness.** Nothing in the source restricts a signal except an
explicit constraint. Code that computes correctly on honest input proves nothing — read
every assignment as attacker-controlled until a constraint binds it.

## Required checks

- every `<--` (or advice/hint assignment) has a matching `===`/`<==` constraint;
- division and inverse are constrained (`out * b === a`) with `b != 0` proven;
- range checks decompose to bits, each constrained boolean, with the recomposition
  constrained and the bit-width below the field modulus to prevent aliasing;
- nullifiers bind every input that must make them unique;
- public vs private signal declarations match the intended privacy model;
- the deployed verifying key matches the audited circuit;
- edge field values (0, 1, p-1) satisfy or correctly reject each constraint.

## Tooling (operator-supplied)

`circom` + `snarkjs` (compile, witness, `r1cs info` for constraint counts), `nargo` for
Noir, `halo2` test harnesses. `circomspect` provides lint-level under-constrained
detection. Absence of any of these is blocked coverage for `source_analysis` on this
family — not a pass.

## Known gaps

Constraint-system soundness is a reasoning task; Invariant Helix contributes the lens
(`references/lenses/zk-circuit.md`), the evidence discipline, and the graph, not an
automated prover. Trusted-setup provenance must be validated out of band.
