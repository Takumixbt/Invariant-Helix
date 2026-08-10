# Pashov / bountyforge skill bridge

If the operator has the real pashov `solidity-auditor`/`x-ray`/`fizz` skills or
bountyforge installed, IH can ingest their output instead of running the ported lenses
natively. Either way, output lands in gated IH artifacts.

## Install (optional)

```bash
git clone https://github.com/pashov/skills ~/.claude/skills/pashov-skills
git clone https://github.com/Gabson0x/bountyforge ~/.claude/skills/bountyforge
```

## Bridge

- **x-ray output** (`x-ray/*.md`, `invariants.md`, `architecture.json`) → ingested as
  `component`/`entrypoint`/`invariant` observations and coverage items. Prefer the
  native `ih-xray-enumerate` when the skill is absent.
- **auditor findings** (per-agent markdown) → each becomes a `hypothesis` finding with
  `lens` set and the agent bundle hashed into `bundle_digest`. They do **not** enter as
  verified; IH's G8 falsification with an independent verifier still applies.
- **fizz suite** → consumed via the fuzzing adapters; violations become `hypothesis`
  leads.

## Rule

The external skill is a hypothesis generator, never an adjudicator. Convergence across
its agents raises priority/confidence only (`converge_findings`), never status. When the
skill is absent, IH runs `references/lenses/*` natively — no capability is lost.
