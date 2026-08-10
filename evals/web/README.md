# Web evaluation

## Scenario

A synthetic multi-tenant application exposes a profile route. The API receives
an object identifier from the client, while owner and non-owner identities are
available for a controlled differential test. A separate dry-run fixture checks
the race runner's safety contract without sending traffic.

## Required reasoning

- create two isolated actor contexts;
- record the UI and direct API requests;
- compare object and tenant identifiers;
- model the profile state, owner and tenant keys;
- validate sequential and negative controls before any concurrency test;
- prove the server-side consequence;
- attempt to refute the hypothesis through middleware, service and ledger code;
- report the unavailable export workflow as low-impact coverage debt.

## Expected failure mode

The evaluator should not call a changed response an authorization finding
without comparing the same existing object across owner and non-owner contexts
and proving the unauthorized synthetic consequence.
