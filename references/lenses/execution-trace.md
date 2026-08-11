# Lens: execution trace

**Role.** Find order, reentrancy, and call-path bugs that only show in execution.  
**Capability:** `execution_trace`. **Domain:** contract.

## Attack surfaces

1. **CEI break** — external call then storage write; reenter the same or sibling function.
2. **Read-only reentrancy** — view functions used by others while state is mid-update (e.g. Curve-style).
3. **Unchecked call** — `.call` / `.send` return ignored; force failure path.
4. **Multicall ordering** — batch where step 2 depends on stale step 1 assumptions.
5. **Callback tokens** — ERC777/ERC1155/ERC721 hooks reenter before accounting settles.
6. **try/catch swallow** — failed external call ignored; state already mutated.
7. **Gas grief** — unbounded loop over attacker-growable array.

## Proof fields

`proof: call stack, storage before/after each step, reenter entry, final balances`
