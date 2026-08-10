# Incident and finding pattern use

Historical incidents, public findings and audit reports are pattern
intelligence. They improve hypothesis generation but never establish that a
current target is vulnerable.

## Pattern card

Represent each pattern with:

~~~text
pattern_id
title
domain
preconditions
root_cause
violated_invariant
attack_path_shape
affected_chain_or_web_semantics
observable_signal
negative_controls
safe_reproduction
common_mitigations
known_false_positives
source_references
~~~

## Use procedure

1. Match the target's graph nodes, code shapes, versions and trust boundaries.
2. Create a hypothesis with the matched preconditions.
3. Check whether the target has the same semantics, not merely similar names.
4. Build a safe negative control.
5. Trace reachability and impact.
6. Verify independently.

## Common protocol patterns

- accounting state updated on one path but not another;
- stale price, index or checkpoint;
- authorization separated from object or amount;
- callback or external call observes an intermediate state;
- initializer, upgrade or emergency path bypasses normal invariants;
- batch and single-item paths diverge;
- bridge message replay or incorrect asset mapping;
- fee, reward or debt accumulator uses inconsistent units;
- oracle, relayer or keeper trust exceeds the actual validation.

## Common web patterns

- object authorization missing on an alternate route;
- tenant or role state inferred from client input;
- workflow transition skipped, repeated or reordered;
- retry or idempotency key not bound to actor and operation;
- session, cache or token state crossing identities;
- webhook, export, notification or background-job authorization gap;
- browser-visible restriction without server enforcement;
- server-side fetch or file action crosses an unintended boundary.

## Quality controls

Do not use a pattern as a payload list. Preserve source attribution, version
context and false-positive notes. Patterns that cannot be translated into a
testable claim are background reading, not active hypotheses.
