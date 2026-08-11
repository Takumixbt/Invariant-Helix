# Claude Code adapter

## Harness contract

Install or copy the repository's skill directory into the project context and
make the controller, references and scripts available to the CLI. The core
methodology must not depend on Claude-specific command names.

## Coordination

Use isolated branch artifacts for subagents. The controller owns graph merge,
gate transitions, reopens, verification assignment and final report release.
Use the Nemesis alternating loop as a branch protocol, not as an unrestricted
recursive prompt.

## Model profile

Start the controller with `claude-opus-5` at effort `high`. Dispatch background
actors with `claude-sonnet-5` at effort `max`, for example:

```text
claude --model claude-opus-5 --effort high
claude agents --model claude-sonnet-5 --effort max
```

If the installed Claude Code build or gateway uses different full model IDs,
configure those IDs explicitly in `adapters/model-profiles.json` or its provider
equivalent. Verify that both IDs and effort levels are accepted before dispatch;
never silently fall back to `opus`, `sonnet`, or another model. “Max” effort and
a Max subscription are separate checks.

## Lens dispatch

Run `ih-lens-dispatch` to plan the lenses; execute each planned lens as a background
subagent reading its own hashed bundle (`ih-lens-bundle`). Keep bundles and branch
artifacts isolated per lens; the controller owns graph merge, gate transitions,
convergence (`ih-converge`), and release. Use the nemesis loop as a bounded branch
protocol, not an unrestricted recursive prompt.

## Tool boundary

MCP bridges, Burp integrations and local commands are optional adapters. Apply
case scope and approval checks before invoking them. The Burp-MCP adapter disables
approval prompts by default — re-impose case/scope/actor/impact checks per
`adapters/web/burp-mcp.md`.
