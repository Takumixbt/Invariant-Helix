# ExampleLend oracle manipulation

## Summary

Synthetic fixture. ExampleLend priced collateral from a spot AMM reserve that an
attacker moved with a flash loan, borrowing against the inflated price. CWE-682.
Estimated loss $8,500,000.

## Root Cause

The lending market read `getReserves` from a single Uniswap-style pair as its price
oracle. A flash loan skewed the reserve ratio within one transaction, so the oracle
reported a manipulated price and the borrow check passed against inflated collateral.

## References

https://example.test/postmortem/examplelend
