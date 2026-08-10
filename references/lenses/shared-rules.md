# Shared lens rules

Every lens obeys these rules. They port the pashov/bountyforge mental-tool protocol
into Invariant Helix and bind its output to the gate system.

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
