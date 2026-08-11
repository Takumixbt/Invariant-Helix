# Model-aware orchestration

Use one model instance as the controller and bounded child sessions as actors.
The controller owns case gates, scope, snapshots, graph merges, finding status,
verification assignment and release. Actors discover, model, test or verify only
the job in their branch artifact. A model profile changes who performs a job; it
never changes authorization or permits a broader test.

Read `adapters/model-profiles.json` before dispatch. Select exactly one provider
profile at session start and record the selected model and effort in every branch
artifact. Do not silently fall back to the current model, a smaller model, or a
different provider when a requested model is unavailable.

## Codex profile

Start the controller in `gpt-5.6-sol` with reasoning effort `high`. Dispatch
actors with `gpt-5.6-luna` and reasoning effort `max`:

```text
multi_agent_v1.spawn_agent(
  model="gpt-5.6-luna",
  reasoning_effort="max",
  fork_context=false,
  message=<bounded branch assignment>
)
```

The parent model cannot be changed in the middle of an existing session. If the
current controller is not `gpt-5.6-sol`/`high`, report the profile as inactive
and restart the controller under that profile before claiming strict Codex
orchestration. Actors may be parallelized only after their inputs, scope and
output contract are fixed.

## Claude Code profile

Start the controller with `claude-opus-5` at effort `high`. Dispatch background
actors with `claude-sonnet-5` at effort `max`. The adapter may use environment
variables or equivalent CLI configuration:

```text
claude --model claude-opus-5 --effort high
claude agents --model claude-sonnet-5 --effort max
```

The installed CLI or gateway is authoritative for the exact model identifier.
If it exposes a different full identifier, set that identifier explicitly in the
profile; do not silently downgrade to `opus`, `sonnet`, or another model. A
subscription tier named “Max” is not the same thing as the `--effort max`
setting; confirm both access and effort independently.

## Actor contract

Give each actor a separate job, immutable input bundle and branch identifier. The
assignment must include:

```text
job_id, role, case_id, snapshot_id, scope_checked, capabilities,
input_digests, questions, allowed_actions, output_schema, deadline
```

Require the actor to return facts, graph deltas, hypotheses, tests, negative
controls, evidence references, refutations, coverage delta and blockers. An
actor must not merge into canonical state, change scope, adjudicate its own
material finding or treat a knowledge-base match as proof.

Use distinct actor sessions for discovery and verification even when both use
the same configured actor model. The verifier receives evidence and questions,
not the discoverer's verdict. If the model, effort, tool or branch identity is
not verifiable, mark the branch blocked and preserve the coverage debt.

## Runtime recording

Record provider, model, effort, session/job identifier, prompt/input bundle
digest, tools used, start/end time, and any fallback refusal in the branch
artifact. Model selection is audit metadata, not evidence of a vulnerability.
