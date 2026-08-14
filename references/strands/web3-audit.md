# Strand B — Smart Contract / Web3 full audit

The orchestrator's flow for an on-chain target: understand the system, run the
alternating loop as the deep-logic core, dispatch the web3 lens actors in
parallel, ground every hypothesis in real incidents, then converge and gate.
Language-agnostic: Solidity, Vyper, Move (Sui/Aptos), Rust (Solana), Cairo. Logic
bugs live in the reasoning, not the syntax.

This file is the **orchestration** for the web3 strand. The lens depth lives in
the actor files (`agents/*.md`) and the two engines (`skills/*/SKILL.md`); this
file says who runs, in what order, over what.

```
   X-RAY ─────► THE LOOP ──────► LENS ACTORS ──────► GROUND ─────► GATE
   understand   feynman ↔ state   economic · math ·   match vs      orchestrator
   the system   (deep logic)      access-upgrade ·    DeFi incident  judges
   (strong)     (deep-logic tier) integration (fast)  corpus         (strong)
```

---

## Phase 0 — X-ray (orchestrator, strong tier)

You cannot audit what you cannot explain. Before dispatching anyone, build the
pre-audit map (the x-ray). Output `.audit/xray/system.md`.

- **Entry points:** every attacker-callable function — the attack surface.
- **Value stores:** every place the protocol holds funds, shares, debt, rewards,
  collateral, accounting. Follow the money.
- **Trust & roles:** owner, admin, minter, upgrader, pauser, keeper, oracle — who
  holds them, how granted/transferred/renounced, what each can do.
- **Novelty:** fork of battle-tested code vs hand-rolled. Custom math, custom state
  machines, novel incentives = highest bug density.
- **Invariants (seven scans, each verified before you trust it):** conservation
  (sum balances == supply), guard (only-X-can-Y, applied at *every* write site),
  ratio (what bounds share price / collateral ratio), state-machine (valid
  transitions, one-shot actions), temporal (deadlines, freshness), cross-contract
  (what it assumes about callees), economic (what makes an attack unprofitable —
  if the answer is "gas", it isn't protected).

Prime from history: pull the DeFi incident corpus and learned patterns for this
protocol type (`knowledge.md`, `learning-loop.md`) into each actor's bundle. A
lending protocol → liquidation/oracle/donation precedents; an AMM → K-invariant/
precision/callback precedents. **A historical match is a lead, never a finding.**

---

## Phase 1 — The alternating loop (deep-logic tier)

The engine (`methodology.md` Part 2). Run the two methods back and forth until
convergence — **this is where single-model rigor comes from**, and where tiered
rigor gets a second axis (the loop runs on the deep-logic tier; the gate on the
orchestrator).

```
PASS 1  feynman (FULL)   skills/feynman-auditor/SKILL.md   → feynman-pass1-raw.md
PASS 2  state (FULL)     skills/state-inconsistency-auditor/SKILL.md → state-pass2-raw.md
PASS 3+ alternate, TARGETED — feynman re-interrogates state's gaps; state re-checks
        feynman's new findings. Until no new findings (max 6 passes).
```

Rules: **FULL FIRST, TARGETED AFTER** · **EVERY PASS FEEDS THE NEXT** ·
**CONVERGENCE OR CAP**. On DeepSeek these engines route to **v4-pro**, not flash
(`model-profiles.md`); on Claude, Sonnet 5 max handles them.

---

## Phase 2 — The web3 lens actors (dispatch in parallel, fast tier)

The loop finds logic and state bugs; these actors cover the web3-specific classes
it doesn't fully target. The orchestrator fans them out over the x-ray map, each
grounded in a real DeFi incident category.

| Actor | Owns | File | Mode |
|---|---|---|---|
| `economic-agent` | oracle, flash-loan, price manipulation, MEV | `agents/economic-agent.md` | core |
| `math-agent` | precision, overflow, donation-inflation, rounding | `agents/math-agent.md` | core |
| `access-upgrade-agent` | access control, initializer, upgrade, delegatecall, storage | `agents/access-upgrade-agent.md` | core |
| `integration-agent` | reentrancy, callbacks, weird tokens, signatures, replay | `agents/integration-agent.md` | core |
| `invariant-agent` | breaks every x-ray invariant; escalates to property fuzzing | `agents/invariant-agent.md` | deep |
| `execution-trace-agent` | end-to-end attack-path tracing, cross-contract | `agents/execution-trace-agent.md` | deep |
| `periphery-agent` | libraries, hooks, init/upgrade/migration/emergency, non-obvious | `agents/periphery-agent.md` | deep |
| `gap-hunter-agent` | hunts what's MISSING — numerical/trust/flow (×3 parallel) | `agents/gap-hunter-agent.md` | deep |

**Deep verification:** the `invariant-agent` escalates trace-unsettled invariants
to **property fuzzing** (`references/property-fuzzing.md`) — Echidna/Medusa/Foundry
invariant runs that turn a REACHABLE invariant into a CONFIRMED one via a shrunk
counterexample PoC.

The actors and the loop cross-signal continuously: an economic oracle finding asks
the state engine "does this desync a coupled accumulator?"; an integration
reentrancy window asks "does this sit between two coupled writes?"; the gap-hunter's
flow-gap corroborates the state auditor's parallel-path analysis;
`execution-trace-agent` assembles everyone's findings into complete attack paths;
`access-upgrade-agent` and `periphery-agent` signal `crossover` the moment a role
is web2-operated. This dense cross-signalling is the point of running deep — the
same critical function gets hit from four angles, and `convergence.md` turns that
into confirmed rigor rather than duplicate noise.

---

## Phase 3 — Ground every hypothesis (orchestrator)

Before a raw finding becomes verified, check it against history (`knowledge.md`):
is there a **real incident** with this root cause on this protocol type? Cite it in
`source_ref:`. Use the "what changed" method — find the incident's fix, extract the
anti-pattern, confirm the target has the same shape (the *pattern*, not a copied
PoC). A ground match calibrates severity and strengthens the report; it is never
proof by itself.

---

## Phase 4 — Converge, gate, verify, report (orchestrator, strong tier)

Run the **convergence pipeline** (`convergence.md`): merge the many overlapping
findings the deep roster produces, isolate one bug per finding, preserve fixes,
confirm every x-ray entry point is accounted for, promote cross-corroborated leads.
Then every surviving finding → `judging.md` (refutation → reachability → trigger →
impact). Every C/H/M → verified with a **Foundry/Hardhat PoC** (or the language's
native test, or a property-fuzz counterexample) demonstrating the exact scenario
with concrete numbers — the engines' verification gates are mandatory here. Score
with CVSS (`cvss-guide.md`), write into `verified.md`.

Then, if strand A also ran, the **crossover** pass hunts the web2↔web3 seam
(`strands/crossover.md`). Report in the operator's format or the Notion peak format
(`report-formatting.md`).

**Do not report** (full list in `judging.md`): centralization risk with no exploit
path, admin functioning as designed, gas micro-optimizations, missing events,
implausible preconditions requiring the protocol already compromised, "reentrancy"
on a working `nonReentrant` guard.
