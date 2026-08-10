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

## Tool boundary

MCP bridges, Burp integrations and local commands are optional adapters. Apply
case scope and approval checks before invoking them.
