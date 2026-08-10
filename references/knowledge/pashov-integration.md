# Integration contract: pashov, bountyforge, nemesis

This file records what was ported from the external audit skills into Invariant Helix,
and how each maps onto the gate system. Nothing external is vendored; code tools are
referenced by install command (`INSTALL.md`) and corpora are fetched on demand.

## What was ported

| Upstream | Ported into IH | Form |
|---|---|---|
| pashov 12 hacking agents | `references/lenses/{access-control,math-precision,economic,execution-trace,invariant-state,periphery-integration,first-principles,asymmetry,boundary,numerical-gap,trust-gap,flow-gap}.md` | chain-neutral lens profiles |
| pashov x-ray | `references/method/xray.md`, `scripts/xray_enumerate.py`, `scripts/xray_git.py` | observation producer |
| pashov fizz | `references/chains/property-fuzzing.md`, `adapters/fuzzing/*` | property-fuzzing methodology |
| pashov shared-rules / SOP / judging | `references/lenses/shared-rules.md`, `auditor-sop.md` | mental-tool protocol + gates |
| bountyforge orchestrator | `scripts/lens_dispatch.py`, `scripts/converge_findings.py` | dispatch + convergence |
| bountyforge CVSS / reporting | `scripts/cvss.py`, `scripts/chain_findings.py`, `references/method/reporting.md`, `knowledge/report-templates/*` | scoring + release |
| bountyforge recon tooling | `adapters/web/recon-cli.md` | capability adapter |
| nemesis-auditor loop | `references/lenses/nemesis-loop.md`, `adapters/audit/nemesis.md` | branch protocol |

## Gate mapping

The upstream **four validation gates** become IH gates:

1. execution + 2. reachability + 3. trigger → **G6 (execution)** and **G7 (proof)**;
4. impact → **G7**; then IH's **G8 falsification** with an independent verifier.

An auditor finding that passes its own trace but fails independent falsification is not
released. The mental-tool markers (Feynman/Socratic/Inversion) are required inside G5.

## The one deliberate divergence: convergence

Upstream promotes a lead to a finding on multi-agent agreement. IH does **not** let
agreement change status. `converge_findings` sets `priority` and `confidence` only; a
promoted lead enters at `hypothesis` and must still pass G8. Shared-premise agreement
is capped below high confidence because agreement on a shared mistaken premise is not
independent verification. This is enforced in code and tested.

## Uncertainty ladder (kept)

```
UNKNOWN    → needs evidence
PLAUSIBLE  → hypothesis
REACHABLE  → execution gate passed
REPRODUCED → proof gate passed
VERIFIED   → positive proof + falsification attempt + independent adjudication
```

## Attribution

Invariant Helix is MIT. pashov/skills, bountyforge, nemesis-auditor, Burp-MCP-Unrestricted
(GPLv3), Scrapling (BSD-3), and the incident/CVE corpora remain under their own
licenses with their upstream authors; IH references them and reuses methodology, not code.
