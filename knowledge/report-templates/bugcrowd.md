# Bugcrowd / Intigriti release template

For web/API findings on VRT-based platforms. Adds VRT/CVSS framing to the base release
template. Populate from the finding bundle.

```
# {title}

**Severity:** {severity} — CVSS 3.1 {cvss.base_score} ({cvss.vector})
**VRT category:** <map bug_class to the platform VRT>
**Target / version:** {scope_and_version}
**Endpoint(s):** {affected_components}

## Description
{root_cause} — {security_claim}

## Steps to reproduce
Preconditions / identities: {preconditions}
Reachable path: {reachable_path}
Requests: {minimal_trigger_sequence}

## Impact
{impact}  (observed: {observable_consequence})

## Verification
{verification_method}; falsification: {falsification_result.verdict}

## Remediation
{fix_guidance}

## Coverage & limitations
{coverage_impact}
```

Intigriti uses the same layout; swap the category taxonomy for the Intigriti CVD scale.
Negative controls (owner succeeds / non-owner denied) belong in Steps to reproduce.
