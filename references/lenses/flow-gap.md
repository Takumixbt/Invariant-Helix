# Lens: flow gap

**Role.** You find value or authority crossing a path without its required control.
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

- **Unguarded outflow.** A withdrawal/transfer/mint path missing the solvency,
  ownership, or accounting check that its siblings enforce.
- **Authority leak.** A capability or role reachable through an indirect path (a
  callback, a delegated call, a batch) that bypasses the direct guard.
- **Accounting bypass.** Value that moves without updating the ledger it should, so
  totals and reality diverge (pairs with invariant-state conservation).
- **Missing settlement.** A flow that pulls without pushing, or credits without
  debiting — flash-loan repay skipped, fee not taken, escrow not released.
- **Cross-boundary flow.** Value or authority crossing a contract/module/chain boundary
  where the control on one side is not enforced on the other.

## Chain-neutral core

Trace every value and authority flow from source to sink. For each, name the control
that must gate it. A reachable flow with a missing or bypassed control is the bug.

## Method

Use graph queries: for each value store, find every path that can decrease it and
confirm each carries the required guard. For each authority, find every path that can
exercise it. The absence of a control on one path is the finding.

## Per-family notes

- **evm** — internal accounting vs token balance; multicall authority.
- **solana** — lamport/token flows vs account bookkeeping; CPI authority.
- **move** — coin flows vs resource accounting; capability propagation.
- **cosmwasm** — bank sends vs internal balances; submessage authority.
- **cairo/starknet** — L1↔L2 value flows; message-driven authority.
- **cardano-utxo** — value conservation across inputs/outputs; policy authority.

## Proof fields

`proof: the flow, the control that is missing on it, and the value or authority gained`.
