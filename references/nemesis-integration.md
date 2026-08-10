# Nemesis integration

Nemesis contributes an alternating loop between first-principles interrogation
and state/invariant cross-checking. It is a feedback mechanism, not a complete
audit platform.

## Initial pass

The first-principles branch asks:

- why does each guard, order and conversion exist?
- what assumption is implicit about caller, time, state or external data?
- what breaks at first, last, repeated, partial, empty and maximum operations?
- what changes if an external call or callback occurs at a different point?
- what differs between parallel, inverse, wrapper, batch and emergency paths?

The state branch maps:

- base values and derived values;
- all direct, indirect, implicit, batch and external mutation paths;
- aggregates and their components;
- indexes and per-actor snapshots;
- caches and the values they summarize;
- resources, accounts, capabilities and message state.

## Feedback loop

Run the following dependency-aware cycle:

1. Feynman suspects expand the state map.
2. State gaps become Feynman questions.
3. Masking code becomes a joint invariant and intent investigation.
4. New paths are traced through callers, callees, hooks and external actors.
5. Multi-step journeys are generated.
6. A delta is produced against all previous passes.
7. Dependent cleared items are reopened when the delta touches them.

Limit repeated passes by a time and evidence budget, not only a fixed number.
A six-pass cap may be useful operationally, but it is not a completeness proof.

## Generalized invariant model

State coupling is one form of a security claim. The loop must also handle:

- authorization and capability claims;
- freshness and oracle claims;
- replay and domain-separation claims;
- ordering and atomicity claims;
- external-call and callback claims;
- economic and solvency claims;
- web identity, tenant and workflow claims;
- cross-chain message authenticity and finality claims.

For a non-state finding, substitute the applicable security claim for the
coupled-state pair.

## Anti-confirmation rules

- The next branch receives evidence and questions, not the prior branch's
  verdict.
- “Both agents agree” is not independent verification if they share the same
  mistaken premise.
- A repeated finding is not a new finding unless it adds a path, consequence,
  proof or root cause.
- A cleared item can be reopened by changed dependencies.
- A no-new-finding pass reduces uncertainty only when coverage is complete.

## Output

Each pass emits:

- new facts;
- new hypotheses;
- refuted hypotheses;
- changed graph dependencies;
- reopened items;
- test requests;
- verification state;
- coverage delta.

The final release consumes the accumulated evidence, not the last pass's
markdown.
