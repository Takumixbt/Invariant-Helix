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

## FINDING vs LEAD

- **FINDING** — a concrete exploitable path with a proof field: specific values, a
  trace, or arithmetic. Enters IH as a `hypothesis` finding with `lens` set.
- **LEAD** — a code smell or partial path with no proof. Enters IH as a `hypothesized`
  observation, or a coverage item, never a finding.

A knowledge-base match (`kb_match`) is always a LEAD until a lens proves reachability.

## Output contract

Each finding maps to the IH finding schema. Use the dedup key `Component | entrypoint
| bug_class`. Do not report: admin-only legitimate actions, standard DeFi tradeoffs,
self-harm-only bugs, gas micro-optimizations, or naming. Convergence across lenses
raises priority and confidence — never status. Status advances only through the gates.
