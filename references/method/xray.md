# X-ray: executable pre-audit modeling

X-ray is the model-building phase (gates G2/G3). Unlike the pashov original it emits
**Invariant Helix observations JSONL**, not markdown, so `scripts/normalize_observations.py`
turns it directly into the case/snapshot-scoped graph. It is a producer, not a verdict.

## Pipeline

1. **Enumerate & measure** — `ih-xray-enumerate` detects the chain family (registry
   `detection_markers`), the source root (`foundry.toml`, `hardhat.config.*`,
   `Anchor.toml`, `Move.toml`, `Cargo.toml`, `Scarb.toml`), counts files/nSLOC, and
   emits `component`/`contract`/`program`/`entrypoint` observation nodes with real
   locators. Entry points are extracted per family via the POSIX-ERE patterns in each
   registry adapter's `entry_point_patterns`.
2. **Git security analysis** — `ih-xray-git` emits `inferred` observations: repo shape,
   fix candidates, dangerous-area changes, late changes, forked deps, tech debt,
   test-co-change rate — scoped to HEAD only.
3. **Invariant synthesis** — a reasoning pass (below) landing as coverage items with
   `hypothesis_families`.

## Invariant synthesis (reasoning pass)

Walk the taxonomy over the extracted deltas, guards, and transitions:

- **Conservation** — delta pairs `Δ(A)=+e, Δ(B)=−e` ⇒ `A+B=const` / `scalar==Σ map`.
  Check every write site; a one-sided write is a gap (On-chain=No).
- **Guard lift** — lift a per-call guard to a global property, then grep all write
  sites. Any unguarded write ⇒ On-chain=No — simultaneously an invariant and a bug lead.
- **Ratio**, **state-machine/one-shot**, **temporal**, **cross-contract**, and
  **economic** scans as in `references/chains/invariant-taxonomy.md`.

Verification gate: every inferred invariant cites a concrete Δ-pair, guard-lift +
write-sites, edge, temporal predicate, or NatSpec claim, or it is dropped. "Could not
verify" is not a row.

## Hard rules (kept from upstream, now enforceable)

- Test **existence** comes from enumeration, never from coverage-tool success.
- A failed `forge coverage` (or equivalent) is recorded as coverage debt, never as
  "no tests."
- Anything unverifiable is dropped, not hedged.
- A chain family's registry `known_gaps` propagate into lens coverage debt.

## Output

Observations JSONL → `ih-normalize` → graph (G3). Coverage items → G4. The x-ray never
emits findings; it builds the model the lenses attack.
