# KyberSwap Elastic tick and rounding discrepancy

## Summary

Historical incident card. KyberSwap reported a November 2023 exploit in concentrated-
liquidity pools involving a discrepancy in the tick-based swap mechanism amplified by a
rounding error. Some pool assets were extracted or became inaccessible.

## Root Cause

The implementation's boundary math did not preserve the same invariant across tick
crossings and rounding directions. The seam is swap step → tick/liquidity update → fee
or delta rounding → next-step state.

## Safe Reproduction

Use a local pool with tiny integer reserves. Check both token orderings, exact-in and
exact-out, zero/one-unit deltas, every nearby tick boundary, and the inverse swap. Assert
that the pool invariant and LP accounting remain within the documented rounding bound.

## References

https://blog.kyberswap.com/post-mortem-kyberswap-elastic-exploit/
