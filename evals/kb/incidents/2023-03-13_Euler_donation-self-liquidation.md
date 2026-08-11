# Euler donation and self-liquidation accounting gap

## Summary

Historical incident card. Euler Finance reported an exploit of roughly $197 million in
March 2023. A donation/reserve path changed the attacker's account health without the
health check that protected the ordinary paths; the attacker then used liquidation
mechanics to extract value. This is a pattern card, not a reproduction recipe.

## Root Cause

An accounting mutation altered collateral and liquidation state without preserving the
same health invariant required by normal transfers. The key review seam is raw balance →
internal exchange rate → health/liquidation eligibility → liquidation bonus.

## Safe Reproduction

Use a local synthetic lending fixture. Prove that an out-of-band balance change either
updates all dependent totals and health checks or is rejected. Use a normal deposit and a
non-profitable self-liquidation as negative controls.

## References

https://www.euler.finance/blog/war-peace-behind-the-scenes-of-eulers-240m-exploit-recovery
