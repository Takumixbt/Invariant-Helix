# Graph engineering

The graph is the shared reasoning surface for web, infrastructure and chain
audits. It prevents each specialist from seeing only a flat file list or an
isolated request.

## Construction

Build the graph in layers:

1. scope and snapshot;
2. assets and boundaries;
3. actors, identities and authorities;
4. routes, entry points and messages;
5. state, values and dependencies;
6. events, traces and outcomes;
7. invariants, hypotheses, tests and findings.

Every edge must answer “how do we know this?” through a locator or evidence
reference.

## Web projection

Capture:

~~~text
origin → host → route → method → parameter → session/role → state change
     → response/event → downstream workflow → impact sink
~~~

Normalize browser requests, proxy history, crawl results and direct HTTP
observations into one endpoint identity while preserving method, actor, state,
body shape and snapshot.

## Chain projection

Capture:

~~~text
actor → authority → program → entry point → instruction/call
     → account/resource/storage mutation → event/receipt
     → asset or external dependency → next reachable operation
~~~

Do not flatten account ownership, resource types, PDA derivation, async
receipts, UTXOs or message domains into generic “storage” when the adapter can
preserve the semantics.

## Attack-path queries

Prioritize graph paths that:

- cross a trust boundary;
- reach custody, upgrade or authority sinks;
- use a value derived from an untrusted or stale source;
- pass through a check before a later act;
- mutate one member of a derived relationship;
- use a privileged capability through an unprivileged wrapper;
- cross a chain, bridge, oracle or asynchronous boundary;
- have no negative control or independent verifier.

## Coverage graph

A coverage item is a graph object with:

- target nodes and path;
- specialist owner;
- planned observation;
- planned negative control;
- proof method;
- verifier;
- status;
- blocker or exclusion reason.

This makes “we looked at it” testable. A file read without a path analysis is
not equivalent to coverage.

## Branch merge

Branches may propose nodes and edges. The merge controller:

1. validates schema;
2. resolves snapshot and case;
3. normalizes identities;
4. detects duplicate candidates;
5. preserves conflicting observations;
6. updates coverage;
7. creates dependency links;
8. records the merge event.

No branch may mark a finding verified. Verification is a separate capability.
