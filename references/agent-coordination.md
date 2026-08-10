# Agent coordination

The controller schedules logical jobs over a dependency graph. It does not
ask every agent to scan everything and then vote.

## Role selection

Jobs are logical responsibilities selected from the role catalog, not a fixed
agent count. Start with scope/snapshot, discovery, graph and coverage. Add web,
infrastructure, chain, synthesis and verification roles only when the target
graph, capability boundary or expected coverage gain justifies them.

Every critical/high path still needs a specialist owner and a distinct verifier.
One process may perform unrelated roles sequentially, but that does not by
itself satisfy the strongest verifier-independence class.

## Scheduling

Parallelize:

- independent passive discovery;
- source inventory and deployment metadata collection;
- specialist branches after the graph snapshot;
- independent verification of unrelated hypotheses.

Serialize:

- scope changes;
- snapshot creation;
- graph merge;
- gate transitions;
- finding status changes;
- remediation and release.

Do not let a branch read another branch's unverified narrative as truth.
Provide the branch's evidence and questions, then require the branch to form
its own conclusion.

## Branch artifact

Every branch writes one artifact containing:

~~~text
branch_id
parent_snapshot
owner_role
capabilities_used
scope_checked
facts
graph_delta
hypotheses
tests
negative_controls
evidence_refs
refutations
coverage_delta
blockers
~~~

The merge controller validates the artifact, resolves conflicts and appends a
merge event. A branch cannot modify or remove prior evidence.

## Failure handling

- tool unavailable: mark capability blocked and route to fallback;
- timeout: preserve partial output and reschedule within budget;
- scope mismatch: stop the branch;
- target changed: create a new snapshot and stale dependent claims;
- conflicting observations: retain both and schedule a resolver;
- verifier disagreement: status inconclusive until resolved.

## Dynamic expansion

Do not create one agent for every tool or chain. Expand only when:

- a new chain family is detected;
- a high-impact graph path needs a specialist not in the default roster;
- independent falsification is required for a material finding;
- a blocked capability becomes available.

Record why the job was created and its expected coverage gain.

Retire or combine a role when its marginal coverage delta is repeatedly zero,
provided its remaining frontier and dependencies are transferred to a named
owner. Efficiency never turns an uncovered path into a pass.
