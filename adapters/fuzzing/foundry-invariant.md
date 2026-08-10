# Foundry invariant adapter

Foundry invariant/handler testing backend for `property_fuzzing` (and `chain_simulation`
/ `execution_trace` via `anvil`/`cast`). Selected for EVM when `forge` is on PATH.

## Install

```bash
curl -L https://foundry.paradigm.xyz | bash && foundryup
```

## Use

- `invariant_*` test functions with handler contracts and bounded actors.
- `forge test --match-test invariant` / `forge test --fuzz-runs N`.
- `forge coverage` for coverage metrics (failure = coverage debt, not "no tests").
- `anvil` fork + `cast` for `execution_trace` reproduction.

## Discipline

An invariant failure is a lead → `hypothesis` finding for a lens to prove and a verifier
to falsify. Record compiler flags, chain id, block, and fuzz seed with every run.
Absent = `property_fuzzing` blocked coverage.
