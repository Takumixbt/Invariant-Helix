# HackerOne release template

Consumes a released (verified/downgraded) finding. Adds platform framing only — no new
claims. Populate from the finding bundle.

```
# {title}

**Severity:** {severity} — CVSS 3.1 {cvss.base_score} ({cvss.vector})
**Asset / version:** {scope_and_version}
**Affected components:** {affected_components}

## Summary
{root_cause} — {security_claim}

## Steps to reproduce
{minimal_trigger_sequence}
Preconditions: {preconditions}
Reachable path: {reachable_path}

## Impact
{impact}  (observed: {observable_consequence})

## Verification
Method: {verification_method}
Falsification: {falsification_result.verdict}, independent reproduction:
{falsification_result.independent_reproduction}

## Remediation
{fix_guidance}

## Coverage & limitations
{coverage_impact}
```

Evidence references resolve to hashed manifest artifacts; never paste secrets or PII.
