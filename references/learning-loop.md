# The Learning Loop — Helix remembers across engagements

Most audit tools start every run from zero. Helix doesn't. It keeps a small,
structured memory of what it has confirmed and what it has wrongly suspected, and
it reads that memory back at the start of every engagement. Each run makes the
next run sharper.

**What this is, honestly:** not model training, not fine-tuning. It is
**retrieval-augmented memory** — append-only JSONL files the agent reads at
priming and writes at close, using its own file tools. No Python framework, no
database, no network. It works identically on Hermes and Claude Code. The
"learning" is that your priors get better: the patterns that actually paid on the
stacks *you* hunt rise to the top of the hit list, and the false positives you
already burned don't come back.

It is deliberately simple — JSONL pattern/audit logs, not a schema engine.

## Why this fits Hermes

The DeepSeek/Hermes runtime is strong at **structured output and tool-calling** —
the two things this loop needs. Hermes reliably emits clean JSONL records and
reliably reads them back, so the memory stays well-formed across many
engagements without a validator babysitting it. The loop leans on that strength:
it asks the model to do what it's good at (emit and consume structured records),
not what a single-key setup can't do (rank itself against a bigger model).

---

## The memory files

```
memory/
  patterns.jsonl          confirmed finding-patterns (the anti-pattern library)
  false-positives.jsonl   hypotheses killed at the gate (don't re-raise these)
  engagements.jsonl       one line per engagement — an index of what was hunted
  README.md               how it works (points here)
```

All three are append-only. Never rewrite history; only add lines. If a file
doesn't exist yet, create it empty on first write.

### `patterns.jsonl` — one confirmed pattern per line

```json
{"id":"PAT-001","date":"2026-08-13","strand":"web3","stack":"solidity/lending","bug_class":"oracle-manipulation","pattern":"reads spot price from AMM getReserves() for collateral valuation","tell":"price = reserve1*1e18/reserve0 with no TWAP","question_that_found_it":"can I move this price in one tx with a flash loan?","fix":"use a TWAP or Chainlink with staleness check","severity":"high","source_ref":"confirmed on <target>, echoes a well-known oracle-manipulation class","confidence":90}
{"id":"PAT-002","date":"2026-08-13","strand":"web","stack":"express/rest","bug_class":"idor","pattern":"req.params.id used in query with auth-but-no-ownership","tell":"findById(req.params.id) after only isAuthenticated middleware","question_that_found_it":"does account B's token work on account A's object?","fix":"scope the query to the caller's tenant/owner","severity":"high","source_ref":"sibling-rule; confirmed on <target>","confidence":88}
```

### `false-positives.jsonl` — one killed hypothesis per line

```json
{"id":"FP-001","date":"2026-08-13","strand":"web3","stack":"solidity","claimed":"reentrancy in withdraw()","why_false":"nonReentrant guard present and effective; gate 1 refutation","lesson":"check the modifier list before raising reentrancy","killed_at_gate":1}
{"id":"FP-002","date":"2026-08-13","strand":"web3","stack":"solidity/vault","claimed":"coupled-state desync stake vs rewardDebt","why_false":"_updateReward() modifier reconciles on entry (lazy eval)","lesson":"trace entry modifiers before claiming desync","killed_at_gate":1}
```

### `engagements.jsonl` — one line per run

```json
{"id":"ENG-001","date":"2026-08-13","target":"<name>","platform":"immunefi","strand":"both","chain":"ethereum","stack":"solidity/lending + react dApp","confirmed":3,"false_positives":5,"patterns_added":["PAT-001","PAT-002"],"notes":"crossover: admin panel controlled pauser role"}
```

---

## When the loop runs

### At PRIME (start of every engagement, after `case.md` is written)

```
1. Read all three memory files.
2. Filter to what matches THIS target:
   - same strand (web / web3 / both)
   - same or adjacent stack (solidity/lending ~ solidity/borrowing;
     express/rest ~ node/api)
   - same protocol type / framework
3. Inject the matches into the attacker's hit list:
   - each matching pattern → a prioritized thing to look for, with its `tell`
     and `question_that_found_it` ready to apply
   - each matching false-positive → a "don't waste time re-raising this; if you
     see this shape, check <lesson> first" note
4. Combine with the historical corpus (knowledge.md). Memory is YOUR history;
   the historical knowledge base is EVERYONE's. Both feed the hit list; both produce leads, never
   findings.
```

The effect: on your third lending-protocol audit, Helix already opens with "check
the oracle for spot-price reads, check reward accounting for stake/rewardDebt
desync, and don't bother raising reentrancy on the nonReentrant functions —
you've burned that twice."

### At LEARN (end of every engagement, after `verified.md` ships)

```
1. For each CONFIRMED finding, append a patterns.jsonl line:
   - the pattern (the code shape), the tell (the concrete signature to grep),
     the question that found it, the fix, the stack, the severity.
   - Only confirmed findings. Never learn from a hypothesis.
2. For each hypothesis KILLED at the gate, append a false-positives.jsonl line:
   - what was claimed, why it was false, the lesson, which gate killed it.
   - This is as valuable as the patterns — it stops repeated dead ends.
3. Append one engagements.jsonl line indexing the run.
4. Keep it lean: a pattern already in memory (same stack + bug_class + tell)
   isn't duplicated — bump its confidence instead by adding a fresh line that
   references the prior id. (Append-only; you're adding a corroboration, not
   editing.)
```

---

## Rules for the loop

```
LEARN ONLY FROM PROOF     patterns come from CONFIRMED findings, never suspects.
FALSE POSITIVES ARE GOLD  a burned dead-end remembered is a run saved next time.
MEMORY IS A LEAD ENGINE   a match raises priority and confidence; it is NEVER a
                          finding on its own. The gate still decides.
APPEND, NEVER REWRITE     history is immutable; corroborate by adding, not editing.
KEEP IT PORTABLE          plain JSONL, readable by any harness, no tool required.
STAY IN STACK             only inject matches relevant to the current target;
                          a web IDOR pattern doesn't belong in a Solidity hit list.
```

## Privacy

Memory records store *patterns and shapes*, not the operator's targets' secrets.
Never write a raw credential, a private key, a session token, or a customer's PII
into any memory file. Reference targets by name only when the operator's own
engagement notes are private to them; if in doubt, anonymize the target
(`<lending-protocol-A>`).

---

## Bootstrapping

On first ever run the files are empty — that's fine. Helix runs on the static
patterns in `knowledge.md` and the historical corpus, and starts filling memory
from engagement one. By a handful of engagements on a given stack, the loop is
carrying real weight. The seed file `memory/patterns.jsonl` ships with a couple
of illustrative lines (marked `"seed":true`) so the format is unambiguous — treat
those as examples, not as confirmed history, and let real engagements build the
rest.
