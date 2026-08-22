# Changelog

All notable changes to Invariant Helix are documented here. Versioning follows
[Semantic Versioning](https://semver.org/).

## [1.2.0] — 2026-08-21

### Added
- **`references/dispatch.md`** — scope-driven dispatch, read immediately after
  intake. Classifies the target from its *real tree* (not its self-description),
  then selects the VM gate + actor roster + which binding-matrix axes are even in
  the grid. Writes `.audit/plan.md` as a contract: fence, deployed-artifact
  hash-pin, the program's kill-list *written before hunting*, severity scale from
  the program. Rule: nothing runs that the scope does not authorise, nothing ships
  that the scope excludes.
- **`references/vm-gates.md`** — the `solana-scan.md` treatment for every other
  VM: EVM/Vyper, Move (Aptos/Sui), CosmWasm, Cairo/Starknet, **and §BACKEND**
  (Python/Node/Go/Rails/Spring/PHP route+guard+sink scan for source reviews). This
  is the coverage pashov's Solidity-only skills cannot provide. Carries
  VM-specific traps generic auditing misses: Move `generic-type-confusion`,
  CosmWasm `reply-id-unbound`, Cairo `felt-overflow-on-value` (felt252 is not
  bounded) and `l1-handler-sender-unchecked`, and per-framework authz nuances
  (Django default permission, Express middleware order, Spring `@EnableMethodSecurity`).
- **`references/web-gates.md`** — the binding matrix for HTTP surfaces. Enumerate
  `(endpoint × method × auth-state × object)` and read the empty cells, the same
  forcing function `binding-matrix.md` gives contracts. Makes Strand A enumerate
  instead of only hunt, and puts OOB confirmation (`interactsh`) on the critical
  path so blind bugs are provable, not dropped.
- **BACKEND-SOURCE target class** — application source review as a first-class
  path, distinct from WEB (live host) and the contract classes.
- **`/helix --matrix`** — coverage-only pass (binding matrix, no hunting).

### Tooling
- Verified the operator's real toolchain and rewired `local-tooling.md` to it:
  `interactsh-client` (OOB), `mitmproxy`, `ffuf`, `nmap`, `slither`, `echidna`,
  `medusa`, Foundry are all present, so those capabilities are adapters, not debt.
  Installed **`semgrep`** (SAST engine for the §BACKEND gate) and **`nuclei`**
  (active_scan). Burp is not required — every capability it would serve has a
  present fallback.

## [1.1.0] — 2026-08-21

### Added
- **`binding-matrix-agent` + `references/binding-matrix.md`** — the coverage
  actor. Every other web3 actor hunts a hypothesis; this one fills a six-axis
  grid (authentication, representation, lifecycle, authority, arithmetic, CPI
  roles) over every instruction and reports the empty cells. This is the forcing
  function `convergence.md` admits Helix lacked: *"the same discipline pashov's
  solidity-auditor enforces mechanically; Helix has no script to force it."*
- **The five-phase order** — ENUMERATE → EMIT EVERYTHING → VERIFY → SCOPE-GATE →
  CONSOLIDATE. Emitting before filtering is deliberate: on the engagement this was
  derived from, three items that strengthened the final report came out of the
  low/medium pile a hunting actor suppresses.
- **`SELF-REFERENTIAL` cell type** — a check that tests a value the same caller
  supplies. Highest-yield cell in the grid, and the easiest to read past, because
  the code looks defended.
- **Mechanical sibling sweep** — grep every guard's identifier and mark each
  handler that should carry it and does not.

### Derivation
Reverse-engineered from a commercial audit engine's output on a 14.5k-LOC Solana
protocol (275 raw findings → 92 → 50 canonical groups). Its whole taxonomy
collapses into the six axes, and **26% of everything it found sat on axis 1
alone**. Where that engine is weaker, the agent's guardrails are explicit: it
never verifies (all findings ship `unreviewed`, and two of six criticals were
false — one disproved by a single RPC call, one by a guard in the same function
with a comment explaining it), it emits no `file:line`, and it is scope-blind.
Hence VERIFY and SCOPE-GATE are mandatory phases here, and
**a second engine's finding is a LEAD at the same trust level as your own first draft.**

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
