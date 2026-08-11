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
