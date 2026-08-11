# Mango Markets thin-oracle manipulation

## Summary

Historical incident card. The CFTC describes an October 2022 Mango Markets incident in
which a thin market price used by the oracle moved sharply, inflating a leveraged
position and allowing assets to be withdrawn against the artificial collateral value.

## Root Cause

The solvency system trusted a manipulable market input without a sufficient liquidity,
deviation, freshness, or independent-reference bound. The seam is market action → oracle
normalization → collateral valuation → borrow/withdraw capacity.

## Safe Reproduction

Use a local oracle double with bounded liquidity and a fixed independent reference. Test
normal movement, a single-block spike, stale data, and an out-of-range deviation. Never
move a live market to reproduce the pattern.

## References

https://www.cftc.gov/PressRoom/PressReleases/8647-23
