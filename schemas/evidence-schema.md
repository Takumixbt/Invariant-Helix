# Evidence and finding contract

Evidence is the bridge between reasoning and a report. The repository uses
small structured records so Codex, Claude Code and a generic CLI can exchange
results without sharing hidden conversation state.

Machine-readable finding and manifest contracts are in
`finding-bundle.schema.json` and `evidence-manifest.schema.json`.

## Case record

Required case properties:

~~~text
case_id
operator
authorization_reference
authorization_expires_at
snapshot_id
target_kind
rules_of_engagement
targets
allowed_capabilities
redaction_policy
~~~

The authorization reference may point to a private document. Never place
secrets, tokens or private customer data in a public artifact.

## Observation record

An observation records what happened, not what it means.

~~~text
observation_id
case_id
snapshot_id
observed_at
capability
tool
tool_version
actor_context
input_summary
output_summary
locator
artifact_refs
negative_control_refs
status
~~~

Output summaries must redact credentials, authorization headers, session
cookies, seed phrases, private keys and personal data. Store sensitive material
outside the public evidence bundle and refer to it by restricted identifier.

## Graph projection record

Raw observations remain evidence records. Before graph normalization, an adapter
projects them into JSONL records with:

~~~text
case_id, snapshot_id
id or type-specific identity
kind, label, status, confidence, sensitivity
properties
locators and evidence_refs
edges with relation, target, status, confidence, locator/evidence
~~~

`normalize_observations.py` validates this projection, applies centralized
redaction, includes case/snapshot in generated identity, rejects branch-issued
`verified` status and refuses dangling edges. It does not silently reinterpret a
raw observation record as a graph node.

## Test record

~~~text
test_id
hypothesis_id
preconditions
steps
controls
expected_signal
observed_signal
environment
reproducibility
impact_limit
result
evidence_refs
~~~

Allowed results:

~~~text
planned, blocked, executed, reproduced, not_reproduced, inconclusive,
refuted, needs_review
~~~

## Finding record

A finding is not a scanner result. It is an evidence-backed claim:

~~~text
finding_id
case_id
snapshot_id
title
severity
confidence
status
status_history
proof_level
discoverer_id
verifier_id
root_cause
security_claim
violated_invariant_or_trust_assumption
affected_components
preconditions
reachable_path
minimal_trigger_sequence
observable_consequence
impact
scope_and_version
verification_method
falsification_result
fix_guidance
evidence_refs
coverage_impact
dedup_key
~~~

Allowed finding statuses:

~~~text
hypothesis, under_verification, verified, refuted, downgraded, duplicate,
inconclusive, released
~~~

Only verified or downgraded findings may enter the pre-release report. The
validator enforces legal status history, distinct discoverer/verifier identity,
case/snapshot matching, falsification verdict consistency and resolvable
evidence. `released` is the post-publication terminal status, not a self-declared
way to bypass the pre-release gate. Inconclusive items remain coverage debt.

## Proof levels

- P0: untested idea.
- P1: code or graph mechanism identified.
- P2: reachable path traced with mitigations checked.
- P3: safe runtime, simulator, browser or API reproduction.
- P4: independent reproduction plus falsification attempt and impact evidence.

Critical and high-impact reports normally require P3 or P4. If runtime proof is
impossible, a P2 release needs a structured reason, limitation and independent
adjudicator rather than a label alone.

## Evidence manifest

Each artifact in an evidence manifest includes:

~~~text
artifact_id
relative_path
media_type
size
content_digest
created_at
producer
snapshot_id
redaction_status
~~~

The digest detects accidental alteration and supports reproducibility. It is
not a trust substitute: a malicious or wrong artifact can still be hashed.
Use `scripts/evidence_manifest.py --verify` to detect missing, untracked,
tampered or case/snapshot-mismatched artifacts before release.
