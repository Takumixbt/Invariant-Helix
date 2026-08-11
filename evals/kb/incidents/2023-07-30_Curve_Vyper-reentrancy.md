# Curve pools and the Vyper reentrancy-lock compiler gap

## Summary

Historical incident card. Multiple Curve pools were exploited in July 2023 when affected
Vyper compiler versions emitted incorrect named reentrancy-lock behavior. The source
decorator therefore did not guarantee the bytecode-level protection expected by the
protocol.

## Root Cause

The security property depended on a compiler-generated guard whose version and bytecode
semantics were not treated as part of the deployed trust boundary. The seam is source
annotation → compiler output → callback ordering → cross-function state mutation.

## Safe Reproduction

Compile a minimal local fixture with the exact pinned compiler, inspect the generated
guard, and run a local callback test. Treat compiler version, optimizer settings, and
generated libraries as evidence inputs; do not execute a public exploit against a live
pool.

## References

CVE-2023-39363
https://hackmd.io/@vyperlang/HJUgNMhs2
https://github.com/vyperlang/vyper/security/advisories/GHSA-5824-cm3x-3c38
