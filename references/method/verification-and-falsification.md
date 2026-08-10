# Verification and falsification

Verification positively establishes that a claim is real. Falsification tries
to prove that it is wrong. Both are required because failure to disprove is not
positive reproduction and confirmation is cheap.

## Proof obligations

For each material hypothesis answer:

1. What exact security property is claimed?
2. What code, route, message or state creates the mechanism?
3. Can an allowed actor reach it?
4. What preconditions are required?
5. What is the smallest trigger sequence?
6. What authoritative state or response changes?
7. What is the measurable impact?
8. What control demonstrates the intended behavior?
9. What mitigation or reconciliation could invalidate it?
10. What evidence would disprove it?

## Independent verifier

The verifier receives:

- the target snapshot;
- source and runtime evidence;
- the proposed claim;
- reproduction and controls;
- impact calculation.

The verifier should not receive the auditor's confidence label or preferred
severity until after forming its own mechanism and verdict.

Record discoverer and verifier identities, model/tool versions, evidence made
available, prior-context exposure, precommitted disproof criteria and the
verifier's newly produced evidence. A second prompt in the same shared context
is an independent lens, not the strongest independence class. Critical claims
normally require a fresh reproduction or a second human/tool boundary.

## Falsification checklist

- re-read exact source locations;
- trace callers, callees, modifiers, middleware, hooks and callbacks;
- check configuration, deployment and feature flags;
- check language and VM safety rules;
- rerun the strongest negative control;
- vary actor, state, amount, timing and failure path;
- calculate attacker cost and benefit;
- search for the same root cause elsewhere;
- attempt a benign fix or invariant assertion to see whether the claim changes.

## Verdicts

~~~text
TRUE_POSITIVE
FALSE_POSITIVE
DOWNGRADED
DUPLICATE
INCONCLUSIVE
~~~

These are falsification outcomes. The controller separately records whether an
independent reproduction occurred and the adjudicated finding status. A
TRUE_POSITIVE verdict without required positive proof does not make a finding
verified.

Inconclusive is a valid result. It must include the missing evidence and
remain visible in coverage debt.

## Avoiding false closure

A finding is not cleared globally. It is cleared for:

- one snapshot;
- one environment;
- one path and actor model;
- the assumptions checked by the verifier.

New evidence touching a dependency reopens the item automatically.
