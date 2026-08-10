# Core methodology

This document is the operational playbook behind Invariant Helix. It defines
what happens, what each stage must produce and when a result is allowed to
advance.

## Case lifecycle

### G0 — Bound

Create a case only after recording:

- exact in-scope domains, APIs, repositories, deployments, contracts, chains
  and environments;
- authorization source, expiration and exclusions;
- permitted identities, test funds, rates, concurrency and impact limits;
- whether active scans, automated fuzzing, OOB callbacks and race testing are
  allowed;
- target version, deployment block or source commit;
- emergency stop contact and rollback expectations;
- prohibited effects, data handling and retention rules.

If any item is unknown, restrict the run to passive discovery and state the
blocker.

### G1 — Snapshot

Capture the baseline:

- source tree and dependency lockfiles;
- deployed addresses, chain IDs, block heights and verified source status;
- domains, DNS, TLS, HTTP status, headers and technology indicators;
- browser entry points, roles, sessions and workflows;
- existing tests, specs, threat models, audit reports and known limitations.

Bind every later artifact to this snapshot. A conclusion about a different
commit, deployment or account context is stale.

### G2 — Inventory

Enumerate broadly before prioritizing:

- web hosts, origins, services, routes, parameters, scripts and APIs;
- actors, roles, tenants, sessions, capabilities and trust boundaries;
- programs, modules, entry points, accounts, resources, authorities and assets;
- oracles, bridges, relayers, keepers, upgrade controls and external services;
- value stores and every path that moves value out.

Use passive sources first. Resolve duplicates and record provenance rather than
discarding historical or contradictory observations.

### G3 — Model

Translate inventory into the graph and the chain-neutral intermediate
representation. Create:

- function or route-state matrix;
- authority and trust map;
- state and mutation matrix;
- value-flow map;
- external-dependency map;
- workflow and multi-transaction journey map;
- coverage matrix linking paths to specialists and tests.

Do not generate a finding while the model is still missing high-impact nodes.

### G4 — Coverage

A coverage item is complete only when it has:

- an owner specialist;
- a target path or node;
- a hypothesis family;
- a planned observation or test;
- a negative control;
- a verifier;
- a status and reason for any exclusion.

Use breadth, depth, identity, time, differential, composition and dead-end
coverage dimensions. Count both exercised paths and intentionally unexercised
paths.

### G5 — Hypothesize

Generate hypotheses from:

- specialist questions;
- graph queries;
- code and deployment differences;
- incident and finding patterns;
- CVE/version matches;
- suspicious masking or defensive code;
- unexpected browser/API state transitions;
- invariant gaps and authority transitions.

A hypothesis must state what would be observed if it were true and what
observation would refute it.

### G6 — Execute

Run only tests admitted by G0. Prefer:

1. static trace;
2. read-only observation;
3. isolated local or fork simulation;
4. testnet or sandbox reproduction;
5. limited production-program reproduction only when explicitly allowed.

Record controls, timing, actor context, inputs, outputs and cleanup.

### G7 — Prove

Prove the complete chain:

actor → precondition → entry point → guard or missing guard → state/message
transition → external dependency → observable consequence → impact.

If one link is inferred, label the result accordingly. Do not use severity to
fill an evidence gap.

### G8 — Falsify

The verifier receives the evidence but not the original auditor's confidence.
It must:

- reread the exact source or runtime trace;
- search callers, callees, hooks, middleware, modifiers and reconciliation;
- try the strongest negative control;
- challenge reachability, trigger uniqueness, impact and severity;
- look for duplicate root causes.

If the verifier cannot decide, status is inconclusive.

Falsification and positive verification are separate records. Failure to
disprove a claim is not itself an independent reproduction. The adjudicator
records whether the mechanism was independently reproduced, what was tried to
disprove it, the verifier's independence class and evidence, and why the final
status follows.

### G9 — Release

Release only after:

- evidence references resolve;
- evidence manifests pass structure and digest verification;
- the target snapshot matches;
- reproduction is minimal and safe;
- independent falsification is recorded;
- duplicates are merged by root cause;
- remediation is proportional;
- coverage debt and limitations are included.

## Prioritization

Prioritize by risk and information gain, not scanner count or a multiplicative
score. Use lexicographic buckets:

1. program rules and safety constraints;
2. maximum plausible impact and exposed authority or value;
3. attacker reachability and precondition cost;
4. path centrality, composition and blast radius;
5. uncertainty reduction per unit of audit effort;
6. novelty only as a tie-breaker.

Low evidence confidence increases investigation need; it must not multiply a
critical path down to low priority. Known bug classes must not be penalized for
lacking novelty. High-priority paths usually include custody outflows,
authority changes, accounting transformations, external calls, upgrade
controls, cross-domain messages, multi-user workflows and new custom code.

## Reopening and convergence

An item is cleared only for a specific snapshot, path and assumption set. A
new finding or observation reopens dependent items. Convergence requires:

- no new dependency-relevant hypotheses;
- all high-impact coverage items exercised or explicitly blocked;
- no unresolved verifier queue;
- no stale snapshot references;
- remaining uncertainty recorded as coverage debt.

Each surface family also records its discovery denominator, evidence-backed
saturation rule, remaining frontier and why a path sample is representative.
“Important,” “material” and “high impact” are assigned explicitly on coverage
items rather than inferred during release.

The controller must not stop solely because the last language-model pass
produced no new prose.
