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
