# Knowledge — grounding hypotheses in what has actually paid

The highest-ROI pre-hunt activity is reading what other hackers already found and
got paid for. A hunter who reads real precedents before hunting finds several
times more bugs than one who starts blind. This file teaches Helix how to search
for, extract, and apply lessons from disclosed reports and real incidents — for
**both** strands.

**Design choice (deliberate):** Helix does **not** vendor a giant knowledge base
it has to keep in sync. It carries the *method* and a curated set of *links*, and
fetches live when a run needs specifics. A stored corpus drifts stale within
weeks (even the incident DBs undercount themselves); live search and direct links
don't. A historical match is always a **lead**, never a finding — the gate and a
PoC decide what's real on *this* target.

If the harness has no web-fetch tool wired in, this whole layer degrades
gracefully to the operator pasting a relevant writeup, or to the patterns below
(which are static and always available).

---

## The "What Changed" method (highest-ROI pattern, both strands)

The single most effective use of disclosed reports:

```
1. Find a disclosed report / incident for the SAME stack as your target
   (web: same framework — DRF, Express, Laravel, Rails.
    web3: same protocol type — lending, AMM, bridge, staking.)
2. Find the fix commit → read the diff.
3. Identify the anti-pattern in the vulnerable code.
4. Grep your target's source for that SAME anti-pattern.
5. Test every match.
```

It works because developers across different teams make the same mistakes with
the same frameworks and the same protocol shapes. You are not copying a PoC — you
are transplanting a *pattern* to a new target.

---

## Six universal web patterns

Check these everywhere on Strand A (they recur across all programs and stacks):

```
1  Feature complexity = bug surface — import/export, multi-step, integrations, batch.
2  Developer inconsistency = strongest evidence (SIBLING RULE) — same op two ways,
   one is wrong. Explains ~30% of paid IDOR/auth.
3  The "else branch" bug — gateway with a dangerous fallthrough.
4  Import/export = SSRF — every "fetch from URL" feature has had it.
5  Secondary/legacy endpoints = no auth — /v1, /internal, ?format=csv, GraphQL fields.
6  Race windows in financial ops — every "check then act".
```

## The web3 incident classes (grounding for Strand B)

Public incident databases catalog hundreds of real exploits by vulnerability
class, each with root cause, vulnerable-vs-fixed code, attack flow, and a runnable
PoC. Before hunting a protocol, load the classes that match its shape:

| If the target is… | Prioritize these incident classes |
|---|---|
| Lending / borrowing | oracle-price-manipulation, flash-loan, business-logic, donation-inflation, liquidation logic |
| AMM / DEX | slippage-amm (K-invariant), precision, unprotected-callback, reentrancy, price-manipulation |
| Staking / rewards | staking-reward, coupled-state (reward accounting), precision |
| Bridge / cross-chain | bridge-crosschain, signature-replay, access-control, off-chain-signer |
| Vault / yield | donation-inflation, precision, share accounting, business-logic |
| Governance | governance (flash-loan voting), access-control, upgrade |
| Token | defl-tax-token (fee-on-transfer), approval-abuse, self-balance |
| ZK / privacy pool | nullifier-reuse (double-spend the same note), merkle-root-staleness (proof verified against a root that's no longer current, or an unbounded root history that never expires), proof-malleability (a valid proof rewritten to a different valid proof for a different effect), under-constrained-circuit (a public input the circuit never actually constrains), verifying-key-mismatch (wrong/stale VK deployed vs the circuit that was audited) |

The largest historical loss categories are where to spend the most time:
**business-logic**, **flash-loan**, **oracle manipulation**, **access-control**,
**arbitrary-call**, and **reentrancy**. Logic and price beat low-level bugs —
audit accordingly.

---

## Report / finding sources (in priority order)

### Web / API
1. **Disclosed-report streams** — the program's own disclosed reports on its bounty platform (HackerOne Hacktivity, Bugcrowd Crowdstream); filter disclosed + bounty awarded.
2. **Public writeups** — search-engine dorks: `site:medium.com "<program>" bug bounty`, `site:infosecwriteups.com "<program>"`, `"<program>" IDOR bounty`.
3. **The org's own repos** — for leaked keys and *fix commits* (the "what changed" goldmine).

### Smart contract / Web3
1. **Public audit-finding search engines** — searchable aggregators of tens of thousands of audit findings across firms; query by protocol name, vuln class, or code pattern. The best web3 precedent search.
2. **Public incident databases** — the class links above, for real-exploit root causes and runnable PoCs.
3. **Top-researcher finding databases** — many leading researchers publish their
   findings with writeups (severity, protocol, root cause). Use them the "what
   changed" way: find a finding shaped like your target's code, read the root
   cause, confirm the pattern on your target.
4. **Published audit contest reports** — for the protocol type.

> Note: some sources may be unreachable from a sandboxed harness (egress policy).
> When a direct fetch is blocked, fall back to a public search aggregator or ask
> the operator to paste the relevant writeup. The method survives the block; only
> the fetch changes.

---

## Program-specific intel (run before hunting a named program)

```
1. What bug classes get paid MOST here?   → count disclosed reports by type.
2. What's the average bounty / severity floor?   → calibrate effort + severity.
3. What's the tech stack / protocol type?   → load the matching patterns above.
4. Who are the top hunters on this program?   → read ALL their disclosed reports.
5. What's the most recent disclosure?   → the anti-pattern may still exist elsewhere.
```

---

## Anti-pattern library (grow it via the learning loop)

As Helix confirms findings, the shapes are appended to `memory/` by the learning
loop (`learning-loop.md`). Over time this becomes a personal, target-relevant
anti-pattern library — the stored version of "what changed", specific to the
stacks the operator actually hunts. Seed examples:

```
## Django REST Framework
- get_object_or_404(Model, pk=id) with no ownership check → IDOR
- serializer.save() with a writable owner field → mass assignment
## Express
- req.params.id straight into a query with no tenant scope → IDOR
- app.use(cors({origin: true})) → credentialed CORS from any origin
## Solidity — lending
- price = pool.getReserves() ratio, read spot → flash-loan oracle manipulation
- shares = amount * totalShares / totalAssets, empty pool → donation inflation
## Solidity — staking
- unstake() updates balance but not rewardDebt → coupled-state desync
```

---

## Using knowledge in the hunt

- **At priming:** load the matching patterns/incidents for the target's stack;
  they become entries in the attacker's hit list (with `source_ref:`).
- **During the hunt:** when you find a lead, ask "has this shape been paid before
  on this stack?" A precedent raises confidence and tells you where the sibling
  bugs are.
- **At reporting:** cite the precedent in the finding's impact ("same root cause
  as <incident>, which caused $X loss") to calibrate severity and strengthen the
  report.

## Ethical note

Disclosed reports and incident writeups are public research material. Learn the
*pattern*; never copy-paste someone's PoC and submit it as your own, and never
re-test an already-fixed endpoint (it wastes triager time). Use the pattern to
find a *different* vulnerable target, and cite the precedent when relevant.
