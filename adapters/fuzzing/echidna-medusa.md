# Echidna / Medusa adapter

EVM stateful/property fuzzing backend for the `property_fuzzing` capability. Selected
when the registry `property_strategy` is EVM and echidna/medusa are on PATH.

## Install

```bash
# echidna: download release binary or `brew install echidna`
# medusa:  go install github.com/crytic/medusa@latest
```

## Use

- Harness in `test/` with handlers, ghosts, and clamped inputs
  (`references/chains/property-fuzzing.md`).
- `echidna . --config echidna.yaml` or `medusa fuzz --config medusa.json`.
- Compensate for `via_ir` coverage deflation when set.

## Discipline

Tag properties `SHOULD-HOLD` vs `EXPLORATORY`. A violation is minimized and turned into
a deterministic Foundry repro recorded as an evidence artifact, then filed as a
`hypothesis` finding. A green campaign is coverage evidence with the property set and
seed/iteration budget — never a pass. Absent = `property_fuzzing` blocked coverage.
