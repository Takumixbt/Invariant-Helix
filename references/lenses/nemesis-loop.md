# Nemesis loop

The concrete branch protocol for the `first-principles` and `invariant-state` lenses.
Ported from nemesis-auditor: an alternating Feynman ↔ State loop that finds bugs
neither pass finds alone. Multi-language (Solidity, Move, Rust, Cairo, Go, TS).

## The two passes

- **Pass 1 — Feynman (first-principles):** challenge every guard, order, and
  conversion. Why does it exist? What is assumed about caller, time, state, external
  data? What breaks at first / last / repeated / partial / empty / maximum operations?
- **Pass 2 — State (invariant-state):** map base and derived values, every direct,
  indirect, batch, and external mutation path, aggregates vs components, caches vs the
  values they summarize.

## The loop (dependency-aware)

1. Feynman suspects expand the state map.
2. State gaps become Feynman questions.
3. Masking code becomes a joint invariant-and-intent investigation.
4. New paths are traced through callers, callees, hooks, and external actors.
5. Multi-step journeys are generated.
6. A delta is produced against all previous passes.
7. Cleared items whose dependencies changed are reopened.

Bound the loop by a time and evidence budget, not a fixed pass count. A six-pass cap
is operational, not a completeness proof.

## Anti-confirmation rules (critical)

- The next branch receives evidence and questions, never the prior branch's verdict.
- "Both agents agree" is not independent verification if they share a mistaken premise
  (this is why `converge_findings` caps shared-premise agreement below high confidence).
- A repeated finding is new only if it adds a path, consequence, proof, or root cause.
- A no-new-finding pass reduces uncertainty only when coverage is complete.

## Generalized claim model

State coupling is one security claim. The loop also handles authorization, freshness,
replay/domain-separation, ordering/atomicity, external-call, economic/solvency, web
identity/tenant, and cross-chain authenticity claims. For a non-state finding,
substitute the applicable claim for the coupled-state pair.

If the real nemesis-auditor skill is installed, `adapters/audit/nemesis.md` ingests its
markdown output as observations; otherwise IH runs this loop natively.
