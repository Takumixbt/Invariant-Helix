# memory/ — the learning loop store

Helix's cross-engagement memory. Append-only JSONL, read at the start of every
run and written at the end. No framework, no database, no network — just files
the agent reads and appends with its own tools. Full protocol:
`references/learning-loop.md`.

| File | Holds | Written when |
|---|---|---|
| `patterns.jsonl` | confirmed finding-patterns (your anti-pattern library) | at close, per CONFIRMED finding |
| `false-positives.jsonl` | hypotheses killed at the gate (don't re-raise) | at close, per killed hypothesis |
| `engagements.jsonl` | one index line per engagement | at close |

**Rules:** learn only from proof (confirmed findings, never suspects); false
positives are as valuable as patterns; a memory match is a *lead*, never a
finding; append, never rewrite; never store a raw secret, key, token, or PII —
patterns and shapes only.

The lines marked `"seed":true` are format examples, not real history. Real
engagements build the rest. You can delete the seed lines once you have your own.
