# Nomad bridge message verification failure

## Summary

Historical incident card. The Nomad bridge incident in August 2022 demonstrated how a
message receiver that accepts an invalid/default commitment can turn arbitrary message
data into token releases across a bridge.

## Root Cause

The receiver's message-authentication invariant was weakened during initialization and
upgrade handling. The seam is commitment state → proof/message validation → one-time
receipt processing → mint/unlock accounting.

## Safe Reproduction

Use a local two-ledger fixture with a deliberately invalid root, wrong source/destination
domain, duplicate nonce, and out-of-order message. Each invalid message must be rejected
without changing supply.

## References

https://cloud.google.com/blog/topics/threat-intelligence/dissecting-nomad-bridge-hack
