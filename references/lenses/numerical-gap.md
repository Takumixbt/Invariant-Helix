# Lens: numerical gap

**Role.** You find cached, scaled, truncated, or time-dependent values that fall out of
alignment with their source. **Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Cache drift.** A stored cached value (price, index, total, checkpoint) that is
  updated on some paths but read on others without refresh — act in the stale window.
- **Scale mismatch.** A value scaled by one factor on write and a different factor on
  read; a shared constant changed in one place but not another.
- **Index/accumulator lag.** Reward-per-token or interest indexes updated lazily;
  claim before or after the update to gain or avoid accrual.
- **Time dependence.** Values derived from `block.timestamp`/slot/round that are
  checked-then-updated vs updated-then-checked (stale read), or that assume a monotonic
  clock.
- **Snapshot ordering.** A snapshot taken before vs after a mutation in the same
  function, changing the derived value (overlaps math-precision and invariant-state).

## Chain-neutral core

For every derived or cached quantity, identify its source, its refresh sites, and its
read sites. A read that can observe the source and cache disagreeing is the bug.

## Per-family notes

- **evm** — accumulator patterns (Compound/Aave indexes); `block.timestamp` accrual.
- **solana** — clock sysvar slots; cached account values across instructions.
- **move** — timestamp module; cached aggregates in resources.
- **cosmwasm** — `env.block.time`; cached items refreshed in `reply` only.
- **cairo/starknet** — block timestamp from the sequencer; cached storage.
- **cardano-utxo** — validity-interval time; datum-cached values vs reference inputs.

## Proof fields

`proof: the source, the stale cache, and the window where they disagree`.
