---
name: invariant-helix
description: "Run evidence-gated, graph-driven security audits across authorized web applications, APIs, infrastructure, and smart contracts. Use for bug-bounty review, business-logic testing, chain-aware invariant analysis, safe race testing, independent verification, coverage accounting, and report preparation."
---

# Invariant Helix

Invariant Helix is a portable security-audit operating procedure. Use it only
on assets for which the operator has explicit authorization. Treat every result
as a hypothesis until its proof and adjudication gates pass.

## Operating contract

1. Establish a machine-valid case manifest before target interaction.
2. Bind authorization, expiry, targets, exclusions, identities, capabilities,
   impact limits, and a target snapshot to the case.
3. Build inventory and a case/snapshot-scoped graph before conclusions.
4. Keep facts, inferences, hypotheses, tests, findings, and refutations distinct.
5. Give every high-impact path an owner, negative control, and verifier.
6. Never let a discoverer adjudicate their own material finding.
7. Prefer minimal, reversible, low-impact proof.
8. Treat unknown as unverified, never safe.
9. Reopen claims when their snapshot or dependencies change.
10. Release findings only after evidence resolution, digest verification,
    independent falsification, positive adjudication, and coverage accounting.

## Select an operating profile

- Web/API: read web-recon, web-toolchain, browser-and-session-model, and
  auth-and-business-logic.
- Infrastructure: read infrastructure-audit plus the relevant web/session and
  safety references.
- Smart contract/program: read smart-contract-audit, chain-neutral-ir,
  chain-adapters, and the detected native adapter.
- Combined protocol: run applicable branches and add cross-boundary analysis.
- Unknown chain: use generic-rpc, mark semantics limited, and do not claim native
  chain assurance.

Select roles from the target graph and expected coverage gain. Do not create a
fixed number of agents merely to satisfy a roster.

## Mandatory gates

The controller must not silently skip a gate. A gate may be not-applicable only
with a recorded reason.

### G0 — Bound

Validate the case manifest. Record authorization and expiry; in-scope targets;
deny-dominant exclusions; rules of engagement; request/concurrency/impact
limits; identities; allowed capabilities; data handling; stop conditions; and
emergency contact. Unknown limits block active execution.

### G1 — Snapshot

Capture source/deployment/browser/API/infrastructure/chain baselines. Bind every
later artifact to the case and snapshot. A changed target creates a new snapshot
and stales dependent claims.

### G2 — Inventory

Enumerate assets, entry points, actors, authorities, state, dependencies, value
stores, external boundaries, and every high-impact outflow or privilege path.
Preserve chain-native, case-sensitive identifiers.

### G3 — Model

Build the money map first (`references/method/money-map.md`): assets, tracked totals,
invariants as equations, and actor cohorts. Most high-severity findings are a tracked
total diverging from reality, so model the value before hunting the code.

Create the typed graph and any native intermediate representation. Every node
and edge needs a locator or evidence reference. Reject dangling endpoints,
mixed cases/snapshots, and silent identity conflicts.

### G4 — Coverage

Create coverage items with target path, impact class, owner, hypothesis
families, planned observations, negative controls, verifier, dependencies,
status, evidence, and blocker/exclusion reasons. Record a discovery denominator
and remaining frontier for each relevant surface family.

### G5 — Hypotheses

Generate hypotheses from specialist lenses, graph queries, differential paths,
incidents, deployment differences, CVE candidates, invariant gaps, and trust
boundaries. State both expected proof and precommitted disproof criteria.

### G6 — Execution

Perform only tests admitted by G0. Record actor, environment, inputs, controls,
timing, traces, results, cleanup, and authoritative post-state. Prefer static or
read-only proof, then local/fork/sandbox, then explicitly permitted production
program activity.

### G7 — Proof

Trace actor → precondition → entry point → guard or missing guard → state or
message transition → external dependency → authoritative consequence → impact.
Label inferred links; severity cannot fill an evidence gap.

### G8 — Falsification and adjudication

Assign a verifier distinct from the discoverer. The verifier independently
traces the mechanism, tries disproof criteria and strongest negative control,
searches mitigations/reconciliation, and records their own evidence.

Failure to disprove is not itself positive verification. Record separately:

- independent reproduction;
- falsification attempted and outcome;
- verifier independence class;
- adjudicated status and actor.

### G9 — Release

Before release, validate legal status transitions, case/snapshot consistency,
evidence-manifest structure and digests, evidence-reference resolution,
discoverer/verifier separation, proof obligations, deduplication, and coverage
termination. Only verified or explicitly downgraded findings are releasable.

## Role catalog

Use only the roles justified by the current graph:

- discovery: scope, source/deployment, web surface, infrastructure, chain, and
  intelligence;
- modeling: asset/trust, identity/authority, state/invariant, value flow,
  external dependency, coverage, and snapshot diff;
- web: surface, browser/session, authentication, API/input, business logic,
  server/client boundary, race/replay, and downstream workflow;
- infrastructure: cloud/IAM/storage, network/TLS/DNS, protocol parsing,
  container/orchestration, CI/CD/supply chain, and email/federated identity;
- chain: x-ray, access control, math/precision, economic, execution, invariant,
  integration, first-principles, asymmetry, boundary, trust/numerical gaps, and
  cross-system flow;
- synthesis: cross-branch composition, pattern correlation, and risk-driven
  prioritization;
- verification: code trace, runtime reproduction, falsification, impact, and
  adjudication;
- release: root-cause deduplication and evidence/coverage review.

Parallelize independent passive discovery and unrelated specialist work.
Serialize scope/snapshot changes, graph merges, status transitions,
adjudication, and release.

## Capability routing

Request capabilities rather than a product name:

```text
surface_inventory, http_crawl, browser_workflow, proxy_observation,
request_replay, input_mutation, synchronized_requests, oob_observation,
source_analysis, chain_simulation, execution_trace, property_fuzzing,
evidence_manifest
```

Adapters map capabilities to an available harness. Missing capabilities create
blocked coverage; they never silently become passes.

## Stop rules

Stop active testing when authorization, scope, identity, target version, impact
limit, or cleanup is ambiguous; when unexpected state changes; when unrelated
users or third parties are touched; or when funds exceed an explicitly approved
and enforceable operator-owned test limit. The bundled race runner refuses any
real-fund mode because it cannot enforce a monetary ceiling.

Do not convert incomplete coverage into a clean bill of health. Release verified
findings alongside a separate coverage-debt and limitations inventory.

## Lens dispatch and grounding (G5)

Generate hypotheses with the attacker lenses in `references/lenses/`. `ih-lens-dispatch`
selects only the lenses the graph justifies, binds each to an available capability, and
assigns an independent verifier at plan time (discoverer ≠ verifier). `ih-lens-bundle`
builds each lens a deterministic bundle; `ih-evidence` hashes it so a lens finding's
`bundle_digest` resolves to the exact input its agent read. Ground every hypothesis with
`ih-kb-match` against the knowledge base — a match is a lead, never a finding. Convergence
(`ih-converge`) raises priority and confidence, never status.

## Iterate until convergence, not until bored (G5–G8)

Audit in alternating passes with `ih-loop`: a first-principles branch and a
state/invariant branch, each receiving the other's **evidence and questions but never
its verdict**. Every pass emits a delta (new facts, hypotheses, refutations); a cleared
coverage item whose dependencies the delta touched is reopened automatically.

The loop stops on a reasoned condition, never a fixed count. Two quiet passes with no
open material gap converge to `complete`; two quiet passes while a critical/high gap is
still open terminate **`inconclusive`** — silence is not coverage. An exhausted pass
budget while still producing new material is also `inconclusive`, not success.

## Scoring and release (G9)

Score released findings with `ih-cvss` (the band must match `severity`). Compose
gate-passed findings into kill chains with `ih-chain` (only from existing graph edges).
Frame the release with `knowledge/report-templates/` per platform. Run
`ih-check-capabilities` to record any missing tool as blocked coverage.

## References

Load the base safety, core methodology, coverage, evidence, graph, coordination,
and verification references for every case. Then load only relevant mode files:

- method/core-methodology.md, method/safety-and-scope.md,
  method/coverage-and-termination.md, method/evidence-and-triage.md,
  method/graph-engineering.md, method/agent-coordination.md,
  method/verification-and-falsification.md, method/requirements.md,
  method/reporting.md, method/xray.md, method/money-map.md,
  method/infrastructure-audit.md
- lenses/shared-rules.md, lenses/auditor-sop.md, lenses/nemesis-loop.md, and the
  22 lens profiles (access-control, math-precision, economic, execution-trace,
  invariant-state, periphery-integration, first-principles, asymmetry, boundary,
  numerical-gap, trust-gap, flow-gap, share-exchange-rate, temporal-cohort,
  liquidation-solvency, cross-chain-state, zk-circuit, web-api, auth-session,
  recon-infra, credential-leak, race-condition)
- web/web-recon.md, web/web-toolchain.md, web/browser-and-session-model.md,
  web/auth-and-business-logic.md, web/race-testing.md
- chains/smart-contract-audit.md, chains/chain-neutral-ir.md, chains/chain-adapters.md,
  chains/invariant-taxonomy.md, chains/property-fuzzing.md
- knowledge/incident-patterns.md, knowledge/cve-intelligence.md,
  knowledge/knowledge-base.md, knowledge/pashov-integration.md,
  knowledge/nemesis-integration.md
