# agents/ — the actor roster

These are Helix's **actors**: the specialty hunters the orchestrator dispatches
in parallel to the fast tier (Sonnet 5 max / DeepSeek-V4-Flash-0731). Each owns a
cluster of bug classes, hunts only its lens over only the scoped surface, and
returns **raw findings** — hypotheses, never verdicts. The orchestrator (strong
tier) converges, gates, verifies, and reports. The pattern: one specialty file
per agent, bundled with shared context, fanned out in parallel, then judged.

## The roster

Helix runs **deep by default** — the full roster below. `--quick` runs only the
`★` core actors for a fast first pass. The orchestrator always scopes to the
target: a pure-contract target skips the web actors, a static site skips the web3
actors. Depth is the default; it is never *all actors on every target regardless*.

### Web strand
| Actor | Owns | Mode |
|---|---|---|
| `recon-agent` ★ | surface mapping, subdomains, JS, secrets, fingerprint | fast |
| `access-control-agent` ★ | IDOR, auth, JWT, OAuth/SSO, privilege escalation | fast |
| `injection-agent` ★ | SSRF, SQLi, RCE, SSTI, XXE, path traversal | fast |
| `client-side-agent` ★ | XSS, CORS, open redirect, cache poisoning, smuggling | fast |
| `business-logic-agent` ★ | workflow abuse, race, mass-assignment, limits | fast |
| `graphql-agent` | GraphQL introspection, field-auth, aliasing/batching, nested DoS | fast (deep) |
| `supply-chain-agent` | dep confusion, CI/CD, subresource, leaked pipeline secrets | fast (deep) |

### Web3 strand
| Actor | Owns | Mode |
|---|---|---|
| `economic-agent` ★ | oracle, flash-loan, price manipulation, MEV | fast |
| `math-agent` ★ | precision, overflow, donation-inflation, rounding | fast |
| `access-upgrade-agent` ★ | access control, initializer, upgrade, delegatecall, storage | fast |
| `integration-agent` ★ | reentrancy, callbacks, weird tokens, signatures, replay | fast |
| `invariant-agent` | breaks every stated invariant; escalates to property fuzzing | deep |
| `execution-trace-agent` | end-to-end attack-path tracing, cross-contract | deep ² |
| `periphery-agent` | libraries, hooks, init/upgrade/migration/emergency, non-obvious | deep |
| `gap-hunter-agent` | hunts what's MISSING — 3 modes (numerical/trust/flow) | deep ³ |
| `binding-matrix-agent` | enumerates, doesn't hunt: who authenticated each value, do asset branches agree | deep ⁴ |
| `skills/feynman-auditor` ★ | first-principles deep logic (any language) | deep-logic ¹ |
| `skills/state-inconsistency-auditor` ★ | coupled-state desync (any language) | deep-logic ¹ |

⁴ `binding-matrix-agent` is the **coverage** actor, not a hunter — it fills the
six-axis grid in `references/binding-matrix.md` over every instruction and reports
the empty cells. Run it alongside the hunters, never instead of them: hunters find
depth, the matrix finds what nobody looked at. It is the forcing function
`convergence.md` says Helix lacks, and it emits before it filters, so expect a
large raw pile and gate it hard.

¹ The two deep-logic engines live in `skills/` (also standalone-invokable via
`/feynman` and `/state-audit`) but dispatch exactly like actors. On a capable fast
tier they run there; on DeepSeek-V4-Flash-0731 they route **up to DeepSeek-V4-Pro-0813** —
flash under-performs on first-principles logic (`references/model-profiles.md`).
They run on **web backend logic too** when source is in scope, not just contracts.

² `execution-trace-agent` runs on the deep-logic tier — it's heavy composition
reasoning, and it's the biggest producer of cross-actor `chain` signals.

³ `gap-hunter-agent` is dispatched **three times in parallel**, once per mode
(numerical-gap, trust-gap, flow-gap) — three angles on absence.

**Not actors:** the **crossover** (`references/strands/crossover.md`), the
**convergence/dedup pipeline** (`references/convergence.md`), and the **gate**
(`references/judging.md`) run on the strong tier — synthesis and judgment, not
discovery. Convergence is mandatory when running deep: many actors overlap, and
convergence is what turns that redundancy into rigor instead of noise.

## The bundle every actor reads

The orchestrator hands each actor a bundle when it dispatches:

```
1. .audit/case.md                    the scope card (THE FENCE)
2. the in-scope source / surface     what to hunt
3. references/methodology.md          the three mental tools
4. references/shared-rules.md         finding format · CWE map · anti-hallucination
5. agents/<name>.md                   this actor's lens (the file you're reading a sibling of)
6. the primed hit list                learned patterns + precedents for this actor's classes
```

## The contract every actor obeys

```
HUNT ONE LENS        only your classes, only the scoped surface. Don't re-report
                     another actor's class — signal it across instead.
RAW ONLY             emit findings in shared-rules.md format at status SUSPECT or
                     REACHABLE. You do NOT gate, dedup, verify, or decide truth.
EVIDENCE OR SILENCE  file:line / request-response / a concrete trace, or it's a LEAD.
SIGNAL CHAINS        the moment your finding touches another lens or the other
                     strand, emit a `chain` signal (shared-rules.md §7). Crossover
                     bugs are built from these.
STAY IN THE FENCE    the case card is the only authority on scope. Never widen it.
```

Each actor file below adds its lens detail, its tells, its anti-pattern library,
and its common false-positive traps (so it doesn't hand the gate obvious noise).
