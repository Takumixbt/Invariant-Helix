# Auditor standard operating procedure

The senior-auditor procedure, expressed against Invariant Helix gates G4–G8. Every
lens follows it.

## 1. Model before hunting (G4)

Read the x-ray (`references/method/xray.md`) first: purpose, actors, trust
boundaries, entry points, custody paths, invariants. Do not attack a system you
cannot describe in plain language.

## 2. Own a coverage item (G4)

Take a coverage item with a target path, an impact class, hypothesis families, planned
observations, and a negative control. You own it end to end; an independent verifier
adjudicates it.

## 3. Generate hypotheses (G5)

Apply your lens's attack surfaces to the graph. Ground each hypothesis against the
knowledge base — if history shows this pattern, cite it as a lead. State both the
expected proof and the precommitted disproof criteria.

## 4. Prove the cheapest way (G6/G7)

Source and graph trace first, then unit counterexample, then stateful fuzzing, then
fork/simulator, then approved live. Trace actor → precondition → entry point → guard
or missing guard → state transition → external dependency → authoritative consequence
→ impact. Label every inferred link. Severity never fills an evidence gap.

## 5. Survive falsification (G8)

Your finding is not yours to verify. The independent verifier retraces the mechanism,
runs your disproof criteria and the strongest negative control, and searches for a
mitigation. "Could not disprove" and "reproduced" are two separate recorded facts.

## Four validation gates (per finding, inside G6–G8)

1. **Execution** — the claimed operation is actually performed.
2. **Reachability** — an allowed actor reaches it from a valid initial state.
3. **Trigger** — the exact conditions and sequence are reproducible.
4. **Impact** — the consequence is real, scoped, and correctly rated.

Then IH's falsification gate. An auditor finding that passes its own trace but fails
independent falsification is not released.

## Confidence scoring

Start at 100. Deduct: incomplete path −20, bounded non-compounding impact −15, merely
specific-achievable-state −10. A finding at ≥80 gets a full write-up with a fix;
below 80 gets a description only. This scores confidence, not status.
