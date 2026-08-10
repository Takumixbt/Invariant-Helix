# Invariant Helix

Invariant Helix is an evidence-gated, graph-driven security-audit methodology and
standard-library safety harness for authorized web applications, APIs,
infrastructure, and smart-contract systems.

Its goal is not to promise omniscience. It makes tested paths, proof, independent
falsification, unresolved assumptions, and coverage debt explicit—and it fails
closed when scope, provenance, or execution limits are incomplete.

## Core properties

- authorization and target snapshots are established before active work;
- observations, hypotheses, tests, findings, and refutations remain distinct;
- a case/snapshot-scoped graph supports cross-path and cross-system reasoning;
- high-impact paths require a specialist owner, negative control, and verifier;
- material releases resolve every evidence reference and verify file digests;
- active race requests are bounded by both the request spec and case manifest;
- chain adapters preserve native semantics and disclose maturity gaps;
- incomplete work ends as coverage debt, not a clean bill of health.

## Repository map

```text
SKILL.md                         normative controller instructions
references/                      progressively loaded methodology
schemas/*.schema.json            machine-readable interchange contracts
schemas/*.md                     schema semantics and guidance
adapters/                        web, chain, infrastructure, and harness mappings
scripts/                         dependency-free validators and safe helpers
tests/                           adversarial regression tests
evals/                           synthetic end-to-end fixtures
```

## Quick start

Python 3.10 or newer is required. The runtime scripts use only the standard
library.

```bash
python scripts/inventory.py \
  --scope evals/web/sample-scope.json \
  --output /tmp/ih-inventory.json

python scripts/normalize_observations.py \
  evals/web/sample-observations.jsonl \
  --output /tmp/ih-graph.json

python scripts/evidence_manifest.py evals/web/evidence \
  --verify evals/web/evidence-manifest.json

python scripts/validate_findings.py evals/web/sample-findings.json \
  --release \
  --case-manifest evals/web/sample-scope.json \
  --manifest evals/web/evidence-manifest.json \
  --evidence-root evals/web/evidence

python scripts/validate_coverage.py evals/web/sample-coverage.json \
  --case-manifest evals/web/sample-scope.json \
  --manifest evals/web/evidence-manifest.json

python -m unittest discover -s tests -v
```

Installing the package exposes equivalent `ih-*` commands, including
`ih-inventory`, `ih-normalize`, `ih-validate-findings`, and
`ih-validate-coverage`.

## Operating profiles

Invariant Helix uses a role catalog rather than a fixed number of agents or
processes. Start with scope, snapshot, discovery, graph, and coverage roles;
activate web, infrastructure, or chain specialists only when the target graph
and expected coverage gain justify them. Every high-impact path still needs an
owner and an independent verifier, even when one operator performs roles
sequentially.

This risk-driven profile keeps small reviews efficient while allowing deeper
specialist expansion for custody, authority, accounting, cross-domain messages,
multi-tenant workflows, and other central paths.

## Active testing safety

Passive/local analysis is the default. Active scans, fuzzing, race tests, OOB
callbacks, and production-program reproductions require an explicit case
manifest and capability admission.

The bundled race runner:

- compares canonical scheme, host, port, and path boundaries;
- rejects userinfo, ambiguous encoded separators, routing override headers, and
  scope look-alikes;
- intersects its allowlist with validated case targets;
- enforces case identity, expiry, actor, request, concurrency, capability, and
  impact limits;
- refuses real-fund execution because it cannot enforce monetary ceilings;
- records client release timing without claiming simultaneous server execution;
- requires prior sequential/negative controls and post-run reconciliation.

No URL, RPC endpoint, repository, or source tree implies authorization.

## Project status

Version 0.2 hardens the executable gates and adds adversarial regression tests.
The repository remains a methodology and orchestration contract, not an exploit
kit or a guarantee that every vulnerability will be found. Native adapter
maturity and unavailable capabilities must remain visible in coverage debt.

See [SECURITY.md](SECURITY.md) for responsible use and security reports.
