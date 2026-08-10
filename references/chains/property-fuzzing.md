# Property fuzzing

Adapts the fizz methodology to Invariant Helix's `property_fuzzing` capability. A green
fuzz campaign is coverage evidence, never a pass.

## Pipeline

1. **Entry-point selection** — from the graph: value-moving, permissionless, and
   role-gated handlers.
2. **Harness design** — handlers with semantic clamping (realistic actor/amount
   bounds), ghost variables, and snapshots. Reuse the project's existing setup.
3. **Property synthesis** — five discovery families, reconciled with
   `references/chains/invariant-taxonomy.md`:
   - conservation (sums, supply vs balances),
   - round-trip (deposit/withdraw, wrap/unwrap symmetry),
   - state-transition (one-shot latches, monotonic indexes),
   - adversarial (attacker-controlled sequences),
   - domain templates (protocol-type invariants).
4. **Guarantee tags** — each property is `SHOULD-HOLD` (a real invariant) or
   `EXPLORATORY` (a probe). Triage weights them differently.
5. **Campaign** — run the backend; on violation, minimize and generate a deterministic
   repro as an evidence artifact.

## Backends (routed by registry `property_strategy`)

- `adapters/fuzzing/echidna-medusa.md` — EVM stateful/property fuzzing.
- `adapters/fuzzing/foundry-invariant.md` — Foundry invariant/handler tests.
- `adapters/fuzzing/chain-native.md` — Anchor/trident (Solana), Move prover, cw-multi-test.

## Discipline

- A `SHOULD-HOLD` violation is a lead → a `hypothesis` finding for a lens to prove and
  a verifier to falsify. It is not a released finding on its own.
- A campaign that finds nothing is recorded as coverage with the properties tested and
  the seed/iteration budget — it does not close a coverage item as "safe."
- Missing fuzzing tools ⇒ `property_fuzzing` is blocked coverage, never a pass
  (`ih-check-capabilities`).
