# Lens: invariant / state

**Role.** Falsify global properties that must hold across any call sequence.  
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

1. **Conservation** — `totalSupply == Σ balances` (or protocol equivalent); break with partial path.
2. **Guard lift** — a `require` at one write site; find another write without it.
3. **State machine** — enum/status transitions; find illegal edge or missing reverse.
4. **One-shot latch** — `require(x == 0); x = y` with a second path that resets or bypasses.
5. **Cross-function** — A sets precondition for B; call B without A or after partial undo.
6. **Ghost variable** — accounting field never updated on one branch of `if`.

## Proof fields

`proof: invariant statement, sequence that breaks it, before/after values`
