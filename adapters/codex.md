# Codex adapter

## Harness contract

Expose the skill as a local directory with shell access, a persistent case
workspace and the ability to run approved scripts. Map tool capabilities to
available connectors or subprocesses.

## Coordination

Use the controller's gate state and graph artifacts as the source of truth.
Parallelize independent discovery and specialist branches; serialize merges,
scope changes, verification and release.

## Model profile

Start the controller as `gpt-5.6-sol` with reasoning effort `high`. Use
`multi_agent_v1.spawn_agent` for bounded actors with the explicit overrides
`model="gpt-5.6-luna"` and `reasoning_effort="max"`. Set `fork_context=false`
when the actor should receive only its hashed branch bundle. The controller
cannot hot-switch its own model after a session starts; restart under the
profile if strict model compliance is required.

Do not dispatch an actor if the host cannot confirm the requested model and
effort. Record the model profile in the branch artifact and keep the fallback
policy set to `none`.

## Missing capabilities

If browser, proxy, RPC, source, simulator or network access is unavailable,
mark the corresponding coverage items blocked. Do not silently substitute a
language-model guess.
