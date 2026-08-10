# Lens: invariant and state

**Role.** You break relationships that must hold across every sequence of calls.
**Capability:** `source_analysis` (+`property_fuzzing` to prove). **Domain:** contract.
Runs the nemesis loop (`references/lenses/nemesis-loop.md`) with first-principles.

## Attack surfaces

- **Conservation.** For each function, find delta pairs `Δ(A)=+e, Δ(B)=−e` — the pair
  implies `A+B=const` or `scalar==Σ mapping[key]`. Check *every* write site: if any
  function writes one side without the other, the invariant is violated (On-chain=No).
- **Guard lift.** A per-call guard (`require(amount>=MIN)`) may imply a global property
  ("every active position ≥ MIN"). Grep all write sites of the constrained variable;
  if any writes it unguarded, that gap is simultaneously an invariant and a bug.
- **Ratio drift.** `A = B*C/D` snapshots taken before vs after other writes in the same
  function (ordering bug — e.g. `totalSupply` snapshotted before vs after `_burn`).
- **State machine.** One-shot latches (`require(x==default); x=concrete`) with a hidden
  reverse path; togglable flags mistaken for latches; cyclic states.
- **Solvency.** `Σ user balances ≤ backing`; can a path let claims exceed reserves?
- **Desync.** Aggregates vs components; caches vs summarized values; indexes vs
  per-actor snapshots updated on some paths but not others.

## Chain-neutral core

Every invariant is a claim `f(state) = c` that must survive all mutation paths. Find a
reachable path that violates it and prove the resulting state.

## Per-family notes

- **evm** — storage mappings + scalars; proxy storage-layout preservation.
- **solana** — account data desync across instructions; PDA-held aggregates vs per-user
  accounts.
- **move** — resource invariants; `global` storage; ability-guarded consistency.
- **cosmwasm** — `Item`/`Map` desync; reply-handler partial updates.
- **cairo/starknet** — storage vars; L1↔L2 message-driven state.
- **cardano-utxo** — datum continuity across the transaction; value preservation.

## Proof fields

`proof: the invariant, the write site that violates it, and the resulting bad state`.
