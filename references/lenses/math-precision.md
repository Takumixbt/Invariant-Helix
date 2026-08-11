# Lens: math precision

**Role.** Force rounding, truncation, or scaling errors that move value to the attacker.  
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

1. **Div-before-mul** — find `/` then `*`; recompute with mul-before-div; show delta ≥ 1 wei.
2. **Round direction** — withdraw/mint/burn: does rounding always favor the protocol or the caller? Test amount = 1, mid, max.
3. **Share = assets * supply / balance** — zero supply, dust deposit, donation to vault before first deposit.
4. **Fee on transfer** — fee-on-transfer / rebasing tokens: accounting uses `amount` not `balanceOf` delta.
5. **Decimal mismatch** — 6 vs 18 decimals in oracle or pair math without scale.
6. **Unchecked cast** — `uint256` → `uint128` / `int256` truncation.
7. **Interest index** — ray/wad mix-ups; accumulate then truncate once vs per-step.

## Proof fields

`proof: exact inputs, both formulas, integer results, who gains the lost units`

## Required adversarial pass

- Evaluate zero, one, max, just-inside, just-outside, exact boundary, and sign-changing
  inputs for both token orderings and every rounding direction.
- Track units and decimals at every conversion. Look for double rounding, stale cached
  indexes, fee-before/after-rounding differences, and inverse operations that do not
  return to the original state.
- For concentrated liquidity, check each tick crossing and exact-in/exact-out branch;
  for shares, compare preview with execution under transfer fees and donations.
