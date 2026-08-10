# Evidence, triage and reporting

Triage turns hypotheses into a defensible queue. It must minimize both false
positives and missed high-impact paths.

## Finding lifecycle

~~~text
candidate → scoped → mechanism-traced → reachable → reproduced
          → falsification-attempted → independently-adjudicated
          → verified-or-downgraded → deduplicated → released
~~~

Alternative outcomes are refuted, downgraded, duplicate, blocked or
inconclusive. Never hide them by deleting the branch artifact.

## Triage questions

For every candidate:

1. Is the exact target and version in scope?
2. Is the cited code, route or deployment real?
3. Can an allowed actor reach the path?
4. What is the minimal trigger?
5. What is the authoritative impact?
6. Is there a control or mitigation?
7. Is the result deterministic or only timing-sensitive?
8. Is the issue already represented by another root cause?
9. What would disprove the claim?
10. What remediation preserves the intended behavior?

## Severity discipline

Rate impact, reachability, attacker cost, prerequisites, affected users/assets,
repeatability and program rules separately. Do not use “critical” as a synonym
for “interesting.”

## Release template

~~~text
title
severity and confidence
affected version and components
root cause
security claim or violated invariant
preconditions
minimal reproduction
expected versus observed behavior
impact and limits
verification and falsification
evidence references
fix guidance
coverage and known limitations
~~~

## Deduplication

Merge findings that share the same root cause and impact even if discovered
through different paths. Keep the discovery paths as supporting evidence.
Separate issues that need independent fixes or have materially different
impact.

## Report boundaries

Never include secrets, unnecessary personal data, destructive instructions or
unverified claims. A clean report contains verified findings and a separate
coverage-debt section.

Before release, resolve every finding, falsification and status-history evidence
reference through the case manifest. Verify artifact digests, case and snapshot
identity, discoverer/verifier separation, legal state transitions and the
coverage termination summary.
