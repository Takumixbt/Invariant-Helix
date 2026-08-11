# External skill bridge (optional)

If you already run another auditor skill, feed its output into IH as **hypotheses**.

## Rule

External tools generate leads only. They never adjudicate. Status still requires G7 proof + G8 independent falsification.

## Ingest patterns

| External output | IH treatment |
|---|---|
| Static analyzer SARIF/JSON | `ih-slither-ingest` → hypothesized leads |
| Markdown agent findings | map each to a finding at `hypothesis` |
| Fuzz crash | coverage evidence + hypothesis lead |
| Pre-audit report | observations / invariants (inferred) |

When no external tool is present, use native lenses + `ih-solidity-analyze` + `ih-audit`.
