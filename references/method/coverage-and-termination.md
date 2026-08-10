# Coverage and termination

## Exclusion is a scope fact, not a place to hide unfinished work

`excluded` asserts that a path lies **outside the engagement** — out of scope, denied by
the rules of engagement, third-party owned, not applicable. It is the one closed status
that requires no evidence, which is exactly why it is the easiest way to fake a clean
audit.

A path you did not test because you ran out of time, lacked a tool, or found it too
difficult is **`blocked`** (name the blocker) or **`uncovered`** — never `excluded`.
Only those statuses keep it visible in `coverage_debt_by_impact`.

`validate_coverage` enforces this: an `exclusion_reason` that describes work not done
(time, effort, difficulty, missing tooling) is rejected unless it also cites an
engagement boundary, and excluding a critical/high path requires explicit
scope/authorization grounds. A `complete` or `complete_with_limitations` termination
additionally requires that at least one item — and at least one critical/high item —
was actually exercised (`tested`/`verified`/`refuted`). An audit that tested nothing
terminates `inconclusive`, with its debt intact.


An audit ends when its coverage obligations are satisfied or honestly blocked,
not when the agents stop generating text.

## Coverage dimensions

Track each high-value path across:

- breadth: all assets, routes, entry points and dependencies;
- depth: callers, callees, state and external boundaries;
- identity: anonymous, users, roles, tenants, admins and programs;
- state: fresh, stale, partial, repeated, failed and recovered;
- time: before/after updates, expiry, retry and finality;
- differential: parallel, inverse, wrapper, batch and emergency paths;
- composition: external calls, bridges, oracles, callbacks and services;
- execution: static trace, simulator, browser/API or testnet;
- falsification: independent verifier and negative control.

## Coverage item contract

Each item records case and snapshot; target nodes/path; explicit impact class;
owner; hypothesis families; planned observations; negative controls; verifier;
dependencies; status; evidence references; and blocker/exclusion reason. Surface
families also record their discovery denominator, remaining frontier and
saturation rule.

Use `scripts/validate_coverage.py` and `schemas/coverage.schema.json` to enforce
the machine-readable contract and produce release inventory counts.

## Termination statuses

~~~text
complete
complete_with_limitations
inconclusive
blocked
aborted
~~~

Use complete only when all material coverage items have evidence and no
unresolved high-impact blocker remains. Use complete_with_limitations when
remaining gaps are low-impact and clearly listed.

`complete` requires every item to be tested, verified, refuted or explicitly
excluded. `complete_with_limitations` cannot contain a critical, high or medium
gap. Stale coverage is incompatible with either complete status.

## Mandatory final inventory

The release package includes counts of:

- assets and entry points discovered;
- graph nodes and edges;
- coverage items tested, blocked and uncovered;
- hypotheses, refuted items and verified findings;
- snapshots and tool capabilities;
- independent verifier assignments;
- stale or reopened claims.

## Anti-loop rule

The controller may stop a feedback loop after a budget is reached only if it
emits the remaining frontier, reasons for stopping and coverage debt. A budget
stop is not convergence.
