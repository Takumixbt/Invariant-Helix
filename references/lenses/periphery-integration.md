# Lens: periphery and integration

**Role.** You break wrappers, routers, adapters, and peripheral contracts that are
assumed to preserve core safety. **Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Router trust.** A router/multicall that forwards `msg.sender`, `msg.value`, or
  approvals in a way the core did not intend; leftover approvals; `permit` front-run.
- **Adapter drift.** An integration adapter that assumes token/oracle/AMM behavior the
  real dependency does not guarantee (fee-on-transfer, rebasing, non-standard return,
  reentrant token).
- **Wrapper invariants.** A wrapper (vault-of-vault, LP-of-LP) that double-counts,
  mis-forwards fees, or loses a safety check the base enforced.
- **Upgrade/migration.** Old entry points live after migration; storage-layout clashes;
  a proxy pointing at an unvetted implementation.
- **Composability.** Two independently safe contracts unsafe when composed (shared
  approval, shared oracle, shared reentrancy surface).

## Chain-neutral core

For each boundary edge into an external or peripheral component, ask what the caller
assumes and what the callee actually guarantees. The gap is the bug.

## Per-family notes

- **evm** — SafeERC20 vs raw; approval race; proxy/impl split.
- **solana** — CPI to an arbitrary program id; account ownership assumptions.
- **move** — generic type parameters instantiated with a hostile type; friend modules.
- **cosmwasm** — cw20 vs native; submessage to an arbitrary contract addr.
- **cairo/starknet** — library calls (`class_hash`); bridge adapters.
- **cardano-utxo** — reference scripts; composed validators and double-satisfaction.

## Proof fields

`proof: the caller assumption, the callee reality, and the exploited gap`.

## Required adversarial pass

- Build a caller-assumption/callee-guarantee table for every adapter and wrapper. Include
  non-standard token returns, fee-on-transfer, rebasing, callbacks, decimal changes,
  paused dependencies, and upgradeable proxies.
- Revoke and reuse approvals across migration, failed calls, multicall, permit, and
  delegatecall paths. Check that `msg.sender`, `msg.value`, chain/domain, and asset
  identity survive each forwarding boundary.
- Negative control: call the core directly and through the periphery with the same inputs;
  the authoritative state, fees, and failure behavior must agree.
