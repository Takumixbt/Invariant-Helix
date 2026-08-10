# Lens: first principles

**Role.** You ask why each guard, order, and assumption exists, and what breaks if it
is wrong. **Capability:** `source_analysis`. **Domain:** contract. Drives the nemesis
loop (`references/lenses/nemesis-loop.md`) with invariant-state.

## Attack surfaces

- **Why this guard?** For every `require`/`assert`/check, state the assumption it
  encodes about caller, time, state, or external data. Then break that assumption.
- **Why this order?** For every sequence of writes and calls, ask what changes if an
  external call, callback, or reordering happens between two steps.
- **Edge existence.** What happens at first, last, repeated, partial, empty, and
  maximum operations — states the author probably did not test.
- **Implicit trust.** What does the code assume about an oracle, relayer, admin, token,
  or user that is never proven on-chain?
- **Parallel/inverse paths.** Do wrapper, batch, emergency, and inverse paths preserve
  the same guarantees as the primary path?

## Chain-neutral core

Treat each guard as a hypothesis about the world. A guard that encodes a false or
unproven assumption is a vulnerability even when the code "works."

## Method

Use the Feynman marker on every function. When an explanation goes fuzzy, that is the
suspect. Feed suspects to the state lens; consume its state gaps as new questions.
Anti-confirmation: never inherit the other branch's verdict, only its evidence.

## Proof fields

`proof: the assumption, why it is false or unproven, and the state that violates it`.
