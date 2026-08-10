# Immunefi release template

For smart-contract findings. Adds chain/asset context and a runnable PoC to the base
release template. Populate from the finding bundle.

```
# {title}

**Severity:** {severity} — CVSS 3.1 {cvss.base_score} ({cvss.vector})
**Chain / addresses:** {scope_and_version}  (deployed: <address(es)>)
**Affected components:** {affected_components}

## Vulnerability
Root cause: {root_cause}
Violated invariant / trust assumption: {violated_invariant_or_trust_assumption}

## Attack scenario
Preconditions: {preconditions}
Reachable path: {reachable_path}
Minimal trigger: {minimal_trigger_sequence}

## Proof of concept
<Foundry/Anchor/native repro — deterministic, references hashed evidence artifact>

## Impact
{impact}  (observed: {observable_consequence})
Funds at risk / affected assets: <scope>

## Verification
{verification_method}; falsification: {falsification_result.verdict}

## Recommendation
{fix_guidance}

## Coverage & limitations
{coverage_impact}
```

Kill chains (`chain_of`) list each composed parent finding. No real-fund PoCs.
