# Chain-native fuzzing adapter

Non-EVM `property_fuzzing` / `chain_simulation` backends, routed by the registry
`property_strategy` per chain family.

## Backends

- **Solana** — Anchor test validator + trident fuzzer.
  `cargo install trident-cli` (needs `cargo`, present); `anchor test`, `trident fuzz`.
- **Move (Aptos/Sui)** — the Move Prover for formal properties + `aptos move test` /
  `sui move test`.
- **CosmWasm** — `cw-multi-test` integration harness via `cargo test`.
- **Cairo/Starknet** — `snforge` (starknet-foundry) fuzz tests; `scarb test`.

## Use

Design properties from the same five families as EVM
(`references/chains/property-fuzzing.md`), expressed in the native harness. Preserve
native semantics — account model, resource abilities, UTXO value conservation — per the
chain adapter.

## Discipline

Same as the EVM backends: a violation is a `hypothesis` lead with a deterministic
native repro artifact; a green run is coverage, not a pass. Families whose registry
entry is Tier 3 methodology-only (NEAR, Substrate, TON, Tron, Cardano) have no
executable fuzzer yet — record as coverage debt with the registry `known_gaps`.
