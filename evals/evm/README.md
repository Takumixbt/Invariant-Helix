# EVM evaluation

## Scenario

A synthetic vault tracks user shares and reward debt. Deposit and full
withdraw reconcile both values, while partial withdrawal and liquidation use
different internal paths.

## Required reasoning

- build the function-state matrix;
- map shares, reward debt, total assets and the index;
- compare deposit, partial withdrawal, full withdrawal and liquidation;
- check lazy reconciliation and hooks before calling a state gap;
- produce a minimal multi-transaction sequence;
- run a native test or deterministic trace;
- independently challenge units, authorization, profitability and severity.

## Expected failure mode

The evaluator should not report a missing write merely because the same
function does not contain it; hidden internal reconciliation must be traced.

The committed fixture is an interchange-contract evaluation with digest-bound
synthetic trace and verifier evidence. A production chain adapter must replace
these text artifacts with a compiler/runtime-pinned native test before claiming
native-chain assurance.
