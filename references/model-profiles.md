# Model Profiles — who plays which role

Helix runs an **orchestrator/actor** split. When the harness has two real model
tiers, this is where rigor gets cheaper *and* stronger: the fast tier discovers
in parallel, the strong tier judges. That's the **discoverer ≠ verifier**
principle — a strong model refuting a weaker model's findings kills far more
false positives than any model checking its own work.

**This is a declaration, not an engine.** There is no Python enforcing it, no
JSON schema validating it. Helix declares the role→model mapping; the harness's
own dispatch mechanism (env vars on DeepSeek, sub-agent model on Claude Code)
does the actual routing. If the harness has only one model, the mapping collapses
to that one model and Helix falls back on the alternating loop for rigor — no
behavior breaks.

---

## The roles

```
STRONG TIER ─ Orchestrator / Judge
   intake · build the attacker's hit list · dispatch the actors · run the
   convergence loop · CROSSOVER synthesis · THE GATE (judging.md) · adjudicate
   verification · write the report.
   → this is the senior auditor. it decides WHAT to hunt and WHAT IS REAL.
   → the strong model's value is the GATE and verification, not coordination.
     Dispatching is cheap; judging is the hard reasoning that earns the tier.

FAST TIER ─ Actors (sub-agents)
   run each specialty lens / pass in parallel → RAW findings only.
   → these are the hunters. they produce hypotheses; they never decide truth.
   → they read a bundle (below), hunt their lens, emit findings in the
     shared-rules.md format, and signal cross-lens leads. That's it.

DEEP-LOGIC ACTORS ─ the two engines (feynman, state)
   discovery, but the reasoning is harder than a mechanical lens sweep.
   → on a capable fast tier (Sonnet 5 max) they run as normal actors.
   → on a weak fast tier (deepseek-v4-flash) they route UP to the strong
     model, because flash under-performs on first-principles logic. Recon and
     mechanical lenses stay on flash; the loop does not.
```

---

## The mapping (both harnesses)

| Role | Claude Code | DeepSeek / Hermes |
|---|---|---|
| **Orchestrator / Judge** (intake, dispatch, crossover, convergence, gate, verify, report) | **Opus 4.8** | **deepseek-v4-pro** |
| **Deep-logic actors** (feynman, state, execution-trace, invariant) | Sonnet 5 (max effort) | **deepseek-v4-pro** ¹ |
| **Fast actors** — web (recon, access-control, injection, client-side, business-logic, graphql, supply-chain) + web3 (economic, math, access-upgrade, integration, periphery, gap-hunter×3) | Sonnet 5 (max effort) | **deepseek-v4-flash** |

¹ On DeepSeek, the deep-logic engines route to **pro**, not flash — flash is fine
for breadth, weak for first-principles logic. On Claude, Sonnet 5 max handles
deep logic on the fast tier, so no third routing is needed. If you're cost-
sensitive on DeepSeek, run the loop on pro only for the priority targets from the
hit list and let flash sweep the rest.

**Crossover runs on the strong tier**, always. It's cross-strand synthesis and
judgment — the same class of work as the gate — so it belongs with the
orchestrator, not the fast actors.

---

## How each harness actually sets it

### Hermes Agent (the native path)

Hermes has a first-class **delegation model** for sub-agents, so the split is a
few lines of `~/.hermes/config.yaml`: the main model is the orchestrator, the
delegation model is the actors.

```yaml
model:
  default: "deepseek/deepseek-v4-pro"      # ORCHESTRATOR / judge — strong tier
  provider: "nous"                          # your provider (nous Portal / openrouter / direct key)

delegation:
  model: "deepseek/deepseek-v4-flash"      # ACTORS / sub-agents — fast tier
  provider: "nous"

auxiliary:                                  # side tasks (summarize/compress)
  compression: { provider: "auto", model: "" }   # "auto" = main; set flash to save credits
```

Or from the CLI: `hermes config set model deepseek/deepseek-v4-pro` and
`hermes config set delegation.model deepseek/deepseek-v4-flash`. Secrets route to
`~/.hermes/.env`, the rest to `config.yaml`. Use the exact model IDs your
provider/Portal exposes (`hermes models`).

**Keep the deep-logic loop on the main (pro) model, not the delegation (flash)
tier.** The orchestrator runs Feynman/State, `invariant-agent`, and
`execution-trace-agent` itself (or dispatches them at main-model tier); the flash
delegation model carries the breadth actors. Flash is fine for recon and
mechanical lens sweeps, weak for first-principles logic.

### Claude Code

- The **orchestrator** is the main session model — set it to Opus 4.8 (`/model opus`).
- **Actors** are dispatched via the harness's sub-agent mechanism (the Task
  tool). Set the sub-agent model to Sonnet 5:
  - per-dispatch: pass the model when spawning the agent, or
  - session-wide: `export CLAUDE_CODE_SUBAGENT_MODEL=<sonnet-5-id>` before launch.
- Each actor reads its `agents/<name>.md` file as its instructions. Sonnet 5 max
  handles both the breadth lenses and the deep-logic engines, so no third tier
  is needed here.

---

## The bundle every actor reads

When the orchestrator dispatches an actor, it hands it a **bundle** — shared
context + the one specialty file:

```
BUNDLE for actor <name>:
  1. .audit/case.md                      the scope card (the fence)
  2. the in-scope source / surface map   what this actor hunts
  3. references/methodology.md            the three mental tools
  4. references/shared-rules.md           the finding format + anti-hallucination
  5. agents/<name>.md                     THIS actor's specialty lens
  6. the primed hit list                  learned patterns + historical precedents
                                          relevant to this actor's classes
```

The actor hunts only its lens, over only the scoped surface, and returns raw
findings in the shared-rules format plus any cross-lens `chain` signals. It does
**not** gate, dedup, or verify — that's the orchestrator's job on the strong
tier.

---

## The full lifecycle, with tiers

```
[STRONG]  intake → case.md → hit list (learning-loop + knowledge)
[STRONG]  dispatch actors in parallel, each with its bundle
[FAST]      recon-agent · access-control-agent · injection-agent ·
            client-side-agent · business-logic-agent          (web strand)
[FAST/pro]  economic · math · access-upgrade · integration ·
            feynman · state                                   (web3 strand)
              → each returns raw findings to .audit/findings/*-raw.md
[STRONG]  converge: dedup by (target|location|bug-class), alternate passes to
          convergence (max 6)
[STRONG]  CROSSOVER synthesis: read both strands' output, hunt the 7 seams
[STRONG]  GATE every finding: refutation → reachability → trigger → impact
[STRONG]  verify C/H/M with PoC/trace; write verified.md
[STRONG]  report (platform or Notion) + LEARN (append to memory/)
```

Everything the fast tier produces is a hypothesis. Everything the strong tier
signs off on is a result. The tier boundary **is** the raw→verified boundary of
the uncertainty ladder (`methodology.md`).

---

## When you have only one model

If the harness is single-model (one key, one model), this whole file collapses to
"everything runs on that model." Nothing breaks — you lose the discoverer≠verifier
axis, but you keep the **alternating loop** (two discovery angles) and the **gate**
(deliberate falsification), which are model-agnostic. That was Helix's original
design and it still holds. The tiers are a rigor *upgrade* when you have them, not
a *requirement*.
