# Graph contract

Invariant Helix uses a typed property graph as the canonical semantic model.
The graph is rebuildable from branch artifacts and evidence. It is not a
permission ledger and it is not allowed to invent facts when an observation is
missing.

The machine-readable contract is `graph.schema.json`.

## Node record

Every node has:

| Field | Requirement |
|---|---|
| id | Stable case-local identifier |
| kind | Controlled node type |
| label | Human-readable name |
| case_id | Case that owns the node |
| snapshot_id | Source or deployment snapshot |
| status | observed, inferred, hypothesized, verified, refuted or stale |
| confidence | low, medium or high, with a reason |
| locators | File/line, URL/request, transaction, account or UI locator |
| evidence_refs | Evidence records supporting the node |
| properties | Type-specific values |
| sensitivity | public, internal, secret-redacted or restricted |

Recommended node kinds:

~~~text
case, snapshot, scope, asset, origin, host, service, route, endpoint,
parameter, request, response, browser_action, workflow, websocket, script,
cookie, token_redacted, actor, identity, role, tenant, boundary, component,
program, contract, module, entrypoint, instruction, state, storage,
resource, object, account, authority, capability, message, oracle,
external_dependency, event, receipt, invariant, hypothesis, test,
execution, evidence, finding, coverage_item, pattern, cve
~~~

## Edge record

Every edge has:

| Field | Requirement |
|---|---|
| id | Stable case-local identifier |
| from | Source node id |
| relation | Controlled relationship |
| to | Destination node id |
| status | Evidence status |
| confidence | Confidence and reason |
| evidence_refs | Evidence supporting the relationship |
| locator | Where the relationship was observed |
| valid_for | Snapshot or environment range |

Recommended relations:

~~~text
contains, hosts, serves, redirects_to, links_to, loads, calls, sends,
receives, emits, reads, writes, guards, requires, authenticates,
authorizes, impersonates, belongs_to, crosses, trusts, delegates,
owns, controls, upgrades, depends_on, prices, observes, mutates,
reconciles, derived_from, mirrors, replays_as, races_with, reaches,
violates, tests, supports, refutes, duplicates, supersedes
~~~

## Status discipline

- observed: directly captured in source, runtime output or authoritative
  documentation.
- inferred: derived from multiple observations and marked with the reasoning.
- hypothesized: proposed attack path or relationship not yet proven.
- verified: independently reproduced and passed the evidence gates.
- refuted: tested and disproven, with the negative evidence retained.
- stale: once valid but invalidated by a snapshot or configuration change.

Never upgrade a node or edge from inferred to verified merely because multiple
agents repeated the same inference.

## Graph invariants

1. Every verified finding has a path from an authorized actor to a concrete
   consequence.
2. Every path step has a locator or evidence reference.
3. A finding cannot rely only on a scanner label.
4. A stale snapshot cannot verify a current target.
5. Secrets are never graph properties; use redacted fingerprints and restricted
   evidence references.
6. Refuted hypotheses remain queryable so the same dead end is not rediscovered.
7. New evidence may reopen a cleared node or edge.
8. Every edge endpoint resolves inside the case/snapshot graph.
9. Node identity includes case/snapshot and type-specific logical identity;
   edge identity includes case/snapshot, source, relation and destination.

## High-value graph queries

- untrusted actor to high-impact sink within bounded path length;
- guard present on one parallel route and absent on another;
- state A mutated without reconciliation of a dependent state;
- check-then-act sequence with an external call or concurrent actor between
  the check and the act;
- public entry point reaching an admin or privileged capability;
- oracle, bridge or external dependency whose trust assumptions are not
  represented;
- graph difference between deployed and reviewed source;
- high-value node with no test, verifier or negative control;
- finding whose evidence is older than its source snapshot.

## Merge rules

Merge is append-oriented. Normalize a candidate before matching it to an
existing node. Do not use a filename or URL alone as identity. A route may
have multiple methods, identities, states and versions; a function may have
multiple callers and chain-specific execution contexts.

Compatible duplicates union evidence and locators. Conflicting records remain
separate merge alternatives with source provenance; input order must not turn a
previously seen canonical record into a new conflict.
