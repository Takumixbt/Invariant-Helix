# Lens: economic

**Role.** Break solvency, pricing, incentives, or conservation of value.  
**Capability:** `source_analysis`. **Domain:** contract.

## Attack surfaces

1. **Money map first** — list assets, tracked totals, equations; find a path where Δreality ≠ Δaccounting.
2. **Donation attack** — transfer tokens directly to the contract; skew exchange rate / rewards.
3. **Flash-loan price** — same-block oracle / spot TWAP abuse; manipulate then liquidate or mint.
4. **Fee bypass** — enter/exit routes that skip fee; multi-hop vs direct.
5. **Bad debt socialization** — undercollateralized position that cannot be liquidated profitably.
6. **MEV sandwich surface** — slippage params default 0 or unbounded.
7. **Incentive drain** — claim rewards without updating debt; partial withdraw without settle.

## Proof fields

`proof: capital in, capital out, tracked totals before/after, profit ≥ 0 for attacker`

## Required adversarial pass

- Write the money map as equations before reading the implementation: raw balances,
  internal totals, shares, debt, fees, rewards, and external positions. Check every branch
  including zero, partial, emergency, revert, and migration paths.
- Apply the token-behavior matrix to every accepted asset: fee-on-transfer, rebasing,
  decimals, false-return, blacklist/pause, and callback behavior. Apply the dependency
  matrix to every oracle, pool, strategy, bridge, and upgradeable proxy.
- Chain the seams explicitly: oracle → valuation → solvency; share price → withdrawal;
  fee/reward accumulator → cohort; external callback → intermediate state. Test whether
  a small local asymmetry compounds across repeated calls.
- Negative control: a normal supported transfer and inverse operation must conserve value
  within the documented rounding bound and leave no profitable self-loop.
