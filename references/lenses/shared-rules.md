# Shared lens rules

Every lens obeys these rules. Output is bound to the G0–G9 gate system.

## Bundle discipline

An agent receives a deterministic bundle: sources, the auditor SOP, its lens profile,
and these shared rules. Read the whole bundle before searching. The bundle is
SHA-256 hashed and registered as an evidence artifact; a finding produced by a lens
carries that digest in `bundle_digest`. In Solidity, always check both `name` and
`_name` variants of a function.

## Mental-tool protocol (mandatory)

Emit a marker each time a trigger fires. Skipping markers is an audit failure; the
controller counts them.

- **Feynman** — on opening any function or module, explain it in plain language with
  no jargon until the explanation is stable. A fuzzy spot is a probable bug site.
- **Socratic** — on any line whose purpose is unclear, drill past the surface reading
  to the implicit assumption. Vulnerabilities hide in unexamined assumptions.
- **Inversion** — whenever a path looks clean or a guard looks sufficient, produce
  **three concrete attacker moves** with specific addresses, values, and states that
  would defeat it. If you cannot, say why the guard holds.

## Cross-pattern weaponization

When you find a bug in one place, grep every sibling for the same function name and
code shape. Escalate each hit to its worst exploitable variant and revisit every
affected path. One bug class usually recurs.

## Fixed adversarial pass (mandatory for every lens)

For every owned coverage item, keep an assumption ledger. Do not let a plausible label,
historical match, or analyzer lead substitute for an entry in this ledger:

```text
assumption: the exact behavior the target relies on
evidence: the file/line, graph edge, deployment version, or route that supports it
attacker move: actor, state, input, ordering, and repetition
expected proof: the authoritative state, balance, message, or response that changes
negative control: the closest intended path that must remain clean
disproof: the guard, invariant, configuration, or version fact that would kill the claim
```

Run the pass in this order and record the marker in working notes:

1. **Feynman** — explain the entry point and its state transition in plain language.
2. **Socratic** — ask why each guard, conversion, external call, cache, and fallback is
   needed; continue until the hidden assumption is explicit.
3. **Inversion** — try three concrete attacker moves with values, actors, and states
   against every path that looks safe. “I could not break it” is a refutation candidate,
   not a silent skip.
4. **Boundary matrix** — vary zero/one/max, stale/fresh, first/repeated, success/failure,
   alternate actor, alternate token behavior, and inverse/batch/wrapper paths where they
   exist.
5. **Seam hunt** — inspect the hand-off to the next lens: oracle → solvency, share math →
   withdrawal, message → mint, auth → object, route → sink, or source → bytecode.
6. **Falsification** — run the strongest negative control and record what evidence would
   disprove the hypothesis before asking another actor to verify it.

## DeFi dependency and token-behavior matrix

When a graph contains value, an oracle, a vault, a swap, a bridge, or an external
dependency, explicitly check the following assumptions even if no analyzer lead names
them: exact transfer amount, return-value semantics, decimals, rebasing, callbacks,
blacklists/pauses, approvals, upgradeability, oracle freshness/deviation/liquidity,
finality, and failure/retry behavior. A clean local unit test with a standard token is a
negative control, not coverage of hostile token behavior.

For each dependency record version, trust owner, change mechanism, failure mode, and the
invariant that would reopen the claim if the dependency changes. Read the source-level
guard and, where the security property is compiler- or generator-dependent, inspect the
deployed artifact or a pinned local build.

## Handoff and proof discipline

Do not merge two mechanisms merely because they share a function or lens. Preserve
distinct fixes and distinct attack paths. A historical incident or KB match is a lead;
convergence increases priority only. A FINDING must name execution, reachability, trigger,
impact, negative control, and independent falsification evidence. If any one is missing,
emit a LEAD or a visible blocked/inconclusive coverage item.

## Start from the machine's leads

Before reading a line yourself, run the analyzers — they hand you concrete, located
starting points so you spend your effort on exploitation, not enumeration:

```bash
ih-solidity-analyze --scope case.json --root src --output leads.jsonl   # contract
ih-recon-normalize nmap.xml --scope case.json --output recon.jsonl      # infra
ih-scrapling-normalize crawl.har --scope case.json --output web.jsonl   # web
ih-kb-match --graph graph.json --index kb.json                          # history
```

Each lead arrives tagged with `bug_class`, `lens`, and a `file:line`. **Your job is not
to re-find them — it is to prove or kill each one, then go find what the analyzer
cannot see:** economic logic, cross-contract composition, business-workflow abuse, and
multi-step sequences. A lexical analyzer cannot reason; you can.

## Push past "looks fine"

The most common failure is stopping at a guard that appears sufficient. Do not
write off a path until you have written down three concrete attacker moves against it
with real addresses, values, and state (the Inversion marker). "I could not find a way"
is a recorded result with a reason, not a silent skip. Equally: never inflate. A path
you could not break is `refuted` or `inconclusive`, never quietly dropped.

## FINDING vs LEAD

- **FINDING** — a concrete exploitable path with a proof field: specific values, a
  trace, or arithmetic. Enters IH as a `hypothesis` finding with `lens` set.
- **LEAD** — a code smell or partial path with no proof. Enters IH as a `hypothesized`
  observation, or a coverage item, never a finding.

A knowledge-base match (`kb_match`) and an analyzer lead are always LEADs until a lens
proves reachability. Promotion is earned by proof, never by agreement or by volume.

## Output contract

Each finding maps to the IH finding schema. Use the dedup key `Component | entrypoint
| bug_class`. Do not report: admin-only legitimate actions, standard DeFi tradeoffs,
self-harm-only bugs, gas micro-optimizations, or naming. Convergence across lenses
raises priority and confidence — never status. Status advances only through the gates.
