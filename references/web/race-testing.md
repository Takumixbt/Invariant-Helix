# Race and concurrency testing

Race testing checks whether a system makes a decision from state that can be
changed before the corresponding action commits. It is valid only when the
program explicitly permits it and must use disposable test identities and
impact limits.

## Race model

Define:

~~~text
precondition P
check C
concurrent actor or request R
commit A
expected serialization or idempotency rule
observable outcome O
~~~

The claim must identify which operation should be atomic and what invariant
should hold after N concurrent attempts.

## Test design

1. Establish a clean baseline.
2. Run a sequential control with the same request.
3. Prepare N identical or deliberately different requests.
4. Release them from one barrier, not from UI clicks.
5. Record send and receive timestamps, status, body and server identifiers.
6. Reconcile balances, ledger entries, state transitions and events.
7. Repeat with lower N and a negative control.
8. Stop at the first permitted signal; do not compound impact.

Use a dedicated runner or a native load-test facility with an explicit
allowlist. Burp Repeater is useful for manually preparing a request but is not
a proof of simultaneous server execution.

## Double-withdrawal analysis

The expected invariant is usually:

~~~text
sum(settled_withdrawal_amounts) ≤ authorized_amount
successful_settlement_count ≤ permitted_settlement_count
ledger_debit = settled_amount
idempotency_key has at most one settlement
pending_hold + available_balance = accounted_balance
~~~

Test only with a test account and approved amount. Compare:

- two identical requests;
- two distinct idempotency keys;
- same request after a token refresh;
- UI request versus direct API request;
- withdrawal versus cancellation or retry path;
- concurrent requests across different API replicas when permitted.

A duplicate HTTP 200 is not sufficient. Inspect server-side transaction IDs,
ledger entries, settlement provider calls and final account state.

## Smart-contract races

On a chain, “race” may mean transaction ordering, stale oracle data, MEV,
reentrancy, asynchronous receipts or cross-chain finality. Use a fork,
simulator or testnet and model adversarial ordering explicitly. Do not submit
transactions intended to manipulate a live protocol unless the program
explicitly authorizes that test.

## Race finding evidence

Require:

- sequential control;
- concurrent run metadata;
- count of accepted operations;
- final authoritative state;
- duplicate or missing side-effect proof;
- idempotency and retry behavior;
- impact calculation;
- cleanup and program communication plan.
