# Changelog

All notable changes to Invariant Helix are documented here. Versioning follows
[Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-08-14

Initial release. A complete, dual-strand bug-hunting skill for web, web3, and the
seam between them.

### Architecture
- **Two strands + one crossover.** Strand A (web/API recon-to-exploit), Strand B
  (smart-contract/Web3 audit), and the crossover pass that hunts the web2↔web3
  seam neither strand sees alone.
- **Orchestrator/actor model.** A strong-tier orchestrator (intake, dispatch,
  crossover, convergence, gate, verify, report) fans out fast-tier actors that
  hunt each lens in parallel. Discoverer ≠ verifier. Tier mapping per harness in
  `references/model-profiles.md`; collapses cleanly to a single model.
- **The alternating loop.** Feynman ↔ State-Inconsistency, run to convergence, as
  the deep-logic engine — language-agnostic, on contracts and web backend logic
  alike.

### Actors
- Web core: recon, access-control, injection, client-side, business-logic.
- Web deep: graphql, supply-chain.
- Web3 core: economic, math, access-upgrade, integration.
- Web3 deep: invariant, execution-trace, periphery, gap-hunter (×3 modes).
- Deep-logic engines: feynman-auditor, state-inconsistency-auditor (also
  standalone via `/feynman`, `/state-audit`).

### Discipline
- The uncertainty ladder (SUSPECT → REACHABLE → CONFIRMED) with a one-way
  raw→verified boundary.
- The 4-gate judge (refutation → reachability → trigger → impact) and the
  Do-Not-Report list.
- A mandatory convergence/dedup pipeline that turns swarm redundancy into rigor.
- Property fuzzing for invariant proof.
- A cross-engagement learning loop (append-only JSONL memory).
- **A self-audit** (`references/failure-modes.md`) enumerating the skill's own
  failure modes with a failsafe for each, plus preflight and release checklists.

### Operability
- Link-drop scope intake (X post / bounty program / repo / domain / contract).
- Platform report templates (HackerOne, Immunefi, Bugcrowd, Intigriti, contest)
  plus a Notion peak audit format for in-house reports.
- Capability-based tooling with coverage-debt fallback; PowerShell→WSL routing.
- Agent-readiness contract (`AGENTS.md`) and tiered install (`INSTALL.md`).
- Runs deep by default; `--quick` for a fast first pass.

### Requirements
- Core: file read (the one hard requirement). Everything else — sub-agent
  dispatch, shell, web fetch, MCP tools — scales depth and proof and degrades to
  coverage-debt when absent. No runtime dependency for the core; external tools
  are the operator's own install.
