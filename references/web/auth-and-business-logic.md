# Authentication, authorization and business logic

These vulnerabilities arise from incorrect relationships between actors,
objects, state and allowed transitions. They require graph and journey
analysis, not only payload scanning.

## Authorization model

For each protected operation record:

~~~text
actor → identity proof → role/capability → object/tenant relation
      → action → state transition → response/side effect
~~~

Identify whether authorization is checked at the route, object, field,
operation, tenant, service and downstream dependency layers.

## Object and function authorization

Test with approved accounts:

- replace object identifiers;
- alter ownership, tenant, parent and nested identifiers;
- change HTTP method and content type;
- remove or duplicate authorization context;
- call internal or alternate routes directly;
- compare batch, export, search and notification paths;
- compare UI request with hand-built request.

A changed response is not enough. Confirm whether the actor could read,
modify, delete, authorize or cause a side effect on the other object's state.

## Business logic model

Write each important workflow as a state machine:

~~~text
states: created → pending → approved → settled → reversed
actors: customer, reviewer, operator, service, scheduler
guards: ownership, amount, time, status, idempotency, authority
effects: balance, ledger, inventory, notification, external call
~~~

For every transition ask:

- can it be repeated, skipped, reordered or performed by another actor?
- can a stale client or old token perform it?
- is the amount or object bound to the authorization decision?
- do alternate routes apply the same guards and effects?
- does failure roll back all coupled state?
- can a user obtain a benefit without satisfying the intended cost?

## Accounting and value

Track gross amount, net amount, fees, limits, holds, refunds, credits and
external settlement independently. Check conservation and idempotency across
partial, full, repeated, reversed and failed operations.

For casino, payment or withdrawal workflows, use disposable test accounts and
zero-value or program-approved amounts. Verify ledger state and settlement
state rather than attempting to extract real funds.

## Evidence standard

An authorization or business-logic finding needs:

- two actor or state contexts;
- a control showing intended denial or normal behavior;
- the minimal request/workflow difference;
- observable unauthorized read, write or side effect;
- server-side consequence;
- independent retest.
