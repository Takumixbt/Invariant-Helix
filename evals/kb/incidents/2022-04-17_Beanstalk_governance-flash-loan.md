# Beanstalk flash-loan governance takeover

## Summary

Historical incident card. Beanstalk reported a governance exploit on April 17, 2022 that
stole roughly $77 million in non-Bean assets. Flash-loaned voting power was used to pass
an on-chain proposal that transferred protocol-held assets.

## Root Cause

Voting power and proposal execution were not sufficiently resistant to temporary capital
or tightly scoped by a delay and independent execution review. The seam is temporary
voting power → proposal approval → arbitrary execution authority.

## Safe Reproduction

Use a local governance fixture and synthetic voting units. A voter acquired after the
snapshot, a replayed proposal, and an execution outside the voted action must all fail.

## References

https://bean.money/blog/beanstalk-governance-exploit
