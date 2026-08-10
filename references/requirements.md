# Runtime requirements

Invariant Helix is designed to degrade honestly when capabilities are absent.
The core skill and deterministic scripts require no network-specific product.

## Baseline

- Python 3.10 or newer for the bundled scripts;
- Git and a persistent case workspace;
- a harness capable of running commands and preserving artifacts;
- a scope and authorization manifest;
- machine-readable case, graph, evidence, finding and coverage contracts;
- enough concurrency control to serialize gates and parallelize branches.

## Web capability tiers

### Minimum

Direct HTTP client, URL/source input, redaction and evidence storage. Suitable
for static/API targets with limited browser coverage.

### Standard

Playwright or equivalent browser, Scrapling or equivalent crawler, and a
scriptable HTTP client. Suitable for modern authenticated applications.

### Extended

Burp or equivalent proxy, OOB observer, fuzzing workers, race runner and
authenticated test identities. Suitable for high-depth web assessment when
explicitly permitted.

## Chain capability tiers

### Minimum

Chain identity, RPC/indexer access, source or bytecode, deployment version and
read-only trace.

### Standard

Native parser/IDL, local simulator or fork, test framework, state snapshots
and property testing.

### Extended

Multi-program fixtures, cross-chain/testnet environment, event/indexer
reconciliation and independent runtime verifier.

Shipped chain adapters are methodology-only/Tier 3 until an external native
harness supplies and records the executable obligations in
`adapters/chains/registry.json`.

## Infrastructure capability tiers

### Minimum

Authorized target/account/project inventory, passive DNS/certificate/provider
metadata, IaC/configuration source, redaction and evidence storage.

### Standard

Read-only cloud/provider APIs, container/Kubernetes and CI/CD configuration,
identity/policy analyzers, protocol-aware HTTP clients and audit logs.

### Extended

Isolated parser/proxy labs, provider-native policy simulation, local clusters,
supply-chain provenance verification, and independent runtime verification.

## Missing capability behavior

The controller must write a blocked coverage item naming:

- missing capability;
- affected paths;
- safe fallback attempted;
- confidence reduction;
- exact next requirement.

Do not fabricate tool output or silently downgrade a blocked test into a pass.
