# Methodology — how Helix thinks

Both strands share one reasoning engine. Pattern-matching finds the obvious
bugs; the lens files teach that. The high-value bugs — the ones everyone else
misses — come from **how** you reason about code and traffic, not from **what**
bug list you memorized.

This file has two halves:

1. **Three mental tools** you reach for instinctively (the senior-auditor mindset).
2. **The alternating loop** — the orchestration that gets adversarial rigor out of a single model.

---

## Part 1 — The three mental tools

These are not steps. You reach for the one the moment calls for. A finding is
not real until you've traced the attack with concrete values. You are an
attacker, not a defender — when you find a bug, deepen it; never argue yourself
out of one.

### Tool 1 — The Feynman test (FIRST, always)

Apply it the moment you open any function, contract, endpoint, or response —
before you reason about anything else. Code you have not Feynman'd is code you
have not understood.

> STOP and ask: "Can I explain what this does to someone who doesn't know the
> tech?" In plain words. The places where your explanation gets fuzzy — where
> you reach for jargon instead of plain meaning — are where you're papering over
> an assumption. That's where bugs hide.

Not Feynman: "`_handleFeeTransfer(zrc20, fee)` transfers the fee."
Feynman: "it picks up the protocol's commission off the user's payment and moves
it to the treasury." Now keep going — what if the payment is ETH and the
function uses an ERC20 method? Your plain-English explanation breaks. Bug.

The same test works on web. Not Feynman: "`GET /api/v2/orders/{id}` returns the
order." Feynman: "it hands *whoever asks* the full contents of *any* order,
looked up by a number you can just increment." Said plainly, the missing
ownership check is obvious.

You don't trust your understanding until you can explain it without the safety
net of technical vocabulary.

### Tool 2 — Socratic questioning

For every line, every check, every parameter: **why is this here? what does it
assume? what happens if the assumption breaks?**

Don't accept "because that's how it's written." Don't accept "the function name
says so." Drill until you reach the implicit belief the code rests on. The first
answer is usually a restatement. The real assumption is two or three "whys"
deeper.

```
if (zrc20 != _ETH_ADDRESS_) IERC20(zrc20).transferFrom(msg.sender, address(this), amount);
- Why check zrc20 != _ETH_ADDRESS_?   → ETH isn't transferable via transferFrom.
- Why no else branch?                  → dev assumed ETH arrives via msg.value.
- Where is msg.value enforced == amount for the ETH path?   → nowhere. Bug.
```

Accept no "because" without examining it.

### Tool 3 — Inversion

Every clean path gets a backward pass. Once you understand what the code is
*supposed* to do, ask: **how would I make it NOT do that?**

Same code, attacker's eye instead of developer's. The developer asks "does this
work?" The attacker asks "how do I break this?" Read every check and ask "what
value slips past it?" Read every state update and ask "what state am I in just
before this?" Read every auth gate and ask "what request never reaches it?"

Never read code — or a request flow — only forward.

### When to reach for which

| Trigger | Tool |
|---|---|
| Opening any new function / contract / endpoint | **Feynman** (always, first) |
| Trying to understand a line/check you don't yet | **Socratic** |
| Something looks too clean, a path seems safe | **Inversion** |
| You reached a "bug" conclusion | **Deepen it** — chain it, find more victims, lower the cost. Do NOT refute it here. |

Trust your discomfort. Reach for the tool. Don't stop until the discomfort has a
name.

---

## Part 2 — The alternating loop (the engine)

**This is how Helix gets two-auditor adversarial
rigor out of a single model on a single API key.** You do not need a big model
to check a small model's work. You need two *different questions* asked of the
same code, each seeded by what the other found.

Two complementary methods, run back and forth:

| Method | Finds | Engine file |
|---|---|---|
| **Feynman** | Business-logic bugs via first-principles questioning — every line challenged, every assumption exposed. | `skills/feynman-auditor/SKILL.md` |
| **State-Inconsistency** | Coupled-state desync — every mutation path mapped, every gap where one side updates without the other. | `skills/state-inconsistency-auditor/SKILL.md` |

### Why both?

- **Feynman alone** finds logic bugs but may miss structural state gaps.
- **State alone** finds desync bugs but may miss *why* the state was designed that way.
- **Alternating** runs them back and forth — each pass feeds the next — finding
  bugs at every iteration the previous pass missed.

### The loop

```
   PASS 1 ── Feynman (FULL)
        │    read every function first-principles. produce findings,
        │    SUSPECTS, and exposed assumptions → feynman-pass1-raw.md
        ▼
   PASS 2 ── State-Inconsistency (FULL)
        │    map every coupled pair, trace every mutation. use Pass 1's
        │    suspects as extra targets → state-pass2-raw.md
        ▼
   PASS 3 ── Feynman (TARGETED)
        │    re-interrogate Pass 2's gaps and desync points
        ▼
   PASS 4 ── State (TARGETED)
        │    re-check Pass 3's new findings for coupled-state impact
        ▼
   ...alternate until CONVERGENCE (a pass yields no new findings),
      hard cap 6 passes.
```

### The three rules of the loop

```
FULL FIRST, TARGETED AFTER
   Passes 1 and 2 are complete sweeps. Only after both have run do you
   narrow to chasing each other's suspects. Never start targeted.

EVERY PASS FEEDS THE NEXT
   A Feynman suspect becomes a State audit target. A State gap becomes a
   Feynman interrogation point. Carry the hand-off explicitly between files.

CONVERGENCE OR CAP
   Stop when a pass produces no new findings, or at 6 passes — whichever
   comes first. Do not loop forever; do not stop at one round.
```

### What the loop is for — any logic, any language

The loop is the deep-logic core of **Strand B** and the **Crossover** — but it is
**not EVM-only**. Feynman and State are language-agnostic by construction
(`skills/*/SKILL.md`): they work on Solidity, Move, Rust, Go, C++, Python, and
TypeScript. Logic bugs live in the reasoning, not the syntax.

So **when a web target's backend source is in scope, the loop runs on it too.**
`business-logic-agent` handles the breadth pass over the web workflow; when it
finds a suspect *that source is available for*, it escalates to the loop — a full
Feynman interrogation of the backend logic (auth decisions, state machines,
accounting, multi-request sequences) and a State pass over any coupled backend
state (a balance and its ledger, a session and its permission cache, an order and
its inventory count). The same alternation, on Python/Go/TS instead of Solidity.

Strand A's *black-box* surface (no source) still uses the recon↔hunt alternation —
recon exposes surface, the hunt interrogates it, findings send you back to recon
for sibling endpoints. The principle is identical everywhere — **two angles on the
same target, each seeding the other**:

| Target has… | The loop is | Runs |
|---|---|---|
| on-chain source | Feynman ↔ State on the contracts | Strand B core |
| web backend source | Feynman ↔ State on the backend logic | escalated from business-logic-agent |
| web black-box only | recon ↔ hunt (the actors) | Strand A |

Wherever there is source and non-trivial logic, the alternating loop is available
and should be used for depth. That is what "rigorous for any logic" means.

---

## Part 3 — The uncertainty ladder

Every finding has a `status` that only climbs on evidence:

```
UNKNOWN     → you haven't looked yet
SUSPECT     → a lens flagged it; a plausible mechanism, no proof   (lives in raw.md)
REACHABLE   → you traced entry→sink; the state/request is achievable
CONFIRMED   → refuted at the gate and proven with a running PoC or exact trace  (ships)
```

- Raw findings files (`*-raw.md`) hold everything up to REACHABLE. They are the
  workshop. **They are never shown to the operator as results.**
- `verified.md` holds only CONFIRMED findings. That is the deliverable.
- A finding never skips a rung because it "looks right." The jump from SUSPECT to
  CONFIRMED goes through the gate (`judging.md`) and a verification method (code
  trace or PoC), every time.

This ladder is why Helix can hunt aggressively without shipping noise: the
aggression lives in the raw files, the discipline lives in the gate, and only
what survives both reaches the report.

---

## Part 4 — Feeding the learning loop

At the end of every engagement, the reasoning that worked and the reasoning that
failed both get remembered (`learning-loop.md`):

- A **confirmed** finding → the pattern that found it (the question, the code
  shape, the stack) is appended to memory so the next audit of a similar target
  starts with it in the hit list.
- A **false positive** killed at the gate → the false-positive shape is appended
  too, so the next run doesn't re-raise it.

The mental tools stay constant. The *priors* they operate on get sharper every
run.
