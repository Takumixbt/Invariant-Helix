# NEAR adapter

## Native semantics

Model accounts, access keys, contracts, promises, receipts, callbacks,
storage staking, gas attachment and asynchronous cross-contract calls.

## Required checks

- access-key permission and function-call scope;
- callback authorization and promise result assumptions;
- attached deposit and storage accounting;
- asynchronous failure and rollback behavior;
- promise ordering and stale state;
- upgrade and deployment authority;
- gas exhaustion and unbounded input;
- cross-contract asset and event reconciliation.

## Execution

Use local sandbox or testnet fixtures with receipt-level traces and account
state snapshots.

## Limits

A transaction success may only schedule later work. Verify the final receipt
chain and callback state before claiming success or failure.
