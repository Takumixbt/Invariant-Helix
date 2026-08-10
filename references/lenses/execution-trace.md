# Lens: execution trace

**Role.** You follow the exact calls, state writes, callbacks, and failure paths.
**Capability:** `execution_trace`. **Domain:** contract.

## Attack surfaces

- **Reentrancy.** Any external call or callback before state is finalized —
  checks-effects-interactions violations, cross-function and cross-contract reentrancy,
  read-only reentrancy into view-based pricing, ERC-777/hook callbacks.
- **Callback injection.** A hook (`onERC721Received`, flash callback, CPI, reply) that
  re-enters or runs attacker code at a chosen point.
- **Ordering.** Operations whose result depends on call order; a mid-sequence external
  call that changes an assumption made earlier in the same function.
- **Failure/rollback.** Partial state on a reverted sub-call; unchecked low-level call
  return; try/catch that swallows a critical failure; DoS by forced revert.
- **Gas/resource.** Unbounded loops over attacker-growable arrays; griefing via gas.

## Chain-neutral core

Trace actor → entry point → each state write and external boundary → consequence.
Mark the exact point where control leaves the contract and what an attacker does there.

## Per-family notes

- **evm** — `call`/`delegatecall`/`staticcall`; reentrancy guards (and their absence on
  view pricing); 63/64 gas rule.
- **solana** — CPI depth and reentrancy via re-invoked programs; account reload after CPI.
- **move** — no dynamic dispatch reentrancy, but re-borrow and hot-potato patterns.
- **cosmwasm** — submessage replies re-entering; `reply` state assumptions.
- **cairo/starknet** — L1↔L2 message consumption ordering; multicall.
- **cardano-utxo** — no reentrancy (UTXO), but double-satisfaction across scripts.

## Proof fields

`proof: the call trace with the re-entry or ordering point marked`.
