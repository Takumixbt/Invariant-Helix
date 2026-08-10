# ExampleDEX reentrancy drain

## Summary

A synthetic incident fixture. ExampleDEX allowed a reentrant call into `withdraw`
before the balance mapping was updated, letting an attacker recursively drain the
pool. CWE-841. Estimated loss $12,000,000.

## Root Cause

The `withdraw` function performed an external call to transfer funds to `msg.sender`
before writing the reduced balance to storage, violating checks-effects-interactions.
A reentrancy guard was absent on the pool contract.

## References

https://example.test/postmortem/exampledex
