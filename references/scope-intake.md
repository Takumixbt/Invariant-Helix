# Scope Intake — turn a dropped link into a scope card

The operator is lazy on purpose. They will mostly drop **one link** — an X
(Twitter) post, a bounty-program page, a repo, a domain, or a contract address —
and expect Helix to figure out the rest. This file is how Helix goes from a link
to a `case.md` scope card that every later phase reads.

**The prime directive of intake:** resolve, don't interrogate. Pull everything
you can from the link itself and the pages it points at. Ask the operator **at
most one** question, and only when a genuine scope boundary is unresolvable. Then
proceed.

---

## Step 1 — Classify the link

```
x.com / twitter.com /…/status/…   → an X post. Resolve what it POINTS AT (Step 2).
immunefi.com/bug-bounty/…         → Immunefi program page.
hackerone.com/<handle>            → HackerOne program.
bugcrowd.com/<handle>             → Bugcrowd program.
intigriti.com/…/programs/…        → Intigriti program.
cantina.xyz/… · code4rena.com/… · sherlock.xyz/…  → audit contest.
github.com/<org>/<repo>           → source repo (likely web3, maybe web).
<bare domain> (acme.com)          → web target.
0x… + chain name                  → deployed contract (web3).
```

If the drop is not a URL (a pasted contract, a Swagger blob, an endpoint list),
skip to Step 3 with what you were given.

## Step 2 — Resolve an X (Twitter) link

An X post is almost never the scope itself — it's a pointer. Fetch it (WebFetch
if available; otherwise ask the operator to paste the text) and extract:

- **The real target** — most posts announcing a bounty/contest link to the
  program or repo. Follow that link and treat it as the true drop (back to Step 1).
- **A contest/launch announcement** — "X protocol audit contest live on Cantina,
  $Y pool" → the linked contest page is the scope.
- **A contract address / protocol name** — if the post only names a protocol,
  search for its official bounty program or verified contracts (WebSearch), then
  confirm the canonical source before scoping.
- **A disclosed bug / writeup** — if the operator dropped a post *about a bug*,
  they likely want that pattern hunted on a related target; ask which target.

If the post points at multiple things, pick the one that is a program/repo/target
and note the others in the scope card as `related:`.

## Step 3 — Extract the scope facts

From the resolved target page(s), pull as much of this as exists. Use WebFetch on
the program page; for a repo, read its README, `README`/`SECURITY.md`, and the
contracts/src tree.

```
target_name        the protocol / app / org
platform           immunefi | hackerone | bugcrowd | intigriti | cantina |
                   code4rena | sherlock | private | in-house
strand             web | web3 | both        (decides which strand runs)
assets_in_scope    exact list — domains, repos, contract addresses, files,
                   API base URLs. THIS IS THE FENCE.
assets_out_scope   explicitly excluded — subdomains, third-party, test envs
active_allowed     is active/intrusive testing permitted? (sqlmap, active scan,
                   brute force, on-chain state changes) — default NO unless stated
chain / network    ethereum | bsc | arbitrum | solana | sui | aptos | … (web3)
tech_stack         framework/language tells (web); solidity/vyper/move/rust (web3)
severity_scale     the program's payout tiers + what each severity means to THEM
known_exclusions   the program's "won't pay for" list (mirror into Do-Not-Report)
poc_requirements   does the program require a testnet/fork PoC? a specific format?
credentials        test accounts / cookies / tokens the operator supplied (web)
```

**Deciding the strand:**
- Contract addresses / a Solidity-Move-Rust repo → **web3** (Strand B).
- A domain / API / web app → **web** (Strand A).
- Both present (a protocol *with* a dApp, an app *with* on-chain settlement) →
  **both**, and the crossover pass will run. When unsure, prefer **both** and let
  each strand's Phase 0 quickly confirm whether its surface exists.

## Step 4 — Write the scope card (`case.md`)

Write `.audit/case.md`. This is the authority on scope for the whole engagement.

```markdown
# Case: <target_name>

- **Platform:** <platform>
- **Strand(s):** <web | web3 | both>
- **Chain/Network:** <if web3>
- **Active testing allowed:** <yes/no — and what specifically>
- **Source of scope:** <the resolved link(s)>
- **Date:** <date>

## In scope (THE FENCE — nothing outside this is touched)
- <asset>
- <asset>

## Out of scope
- <asset>

## Severity scale (this program's language)
| Severity | This program pays for | Payout |
|---|---|---|
| Critical | … | … |

## Known exclusions → fold into Do-Not-Report
- <the program's won't-pay list>

## PoC requirements
- <testnet/fork? format? platform template?>

## Credentials / test accounts (web)
- <redacted refs — never paste raw secrets into findings>

## Related (noted, not in scope)
- <other links from the drop>

## Open question (if any)
- <the ONE thing you need the operator to confirm>
```

## Step 5 — The one-question rule

Ask the operator a single question **only** if a scope boundary is genuinely
unresolvable from the link — e.g.:

- the drop names a protocol with **no discoverable** official program/scope;
- **two** plausible targets and no signal which (a monorepo with app + contracts,
  operator said "the new one");
- active testing is central to the bug class but the program's stance is unstated.

Phrase it concretely, offer the most likely answer as the default, and **proceed
on the default if the operator doesn't answer** — never stall an engagement on a
question you can reasonably default. Everything else, infer and note in `case.md`.

---

## What intake does NOT do

- It does not widen scope. If the program lists three contracts, the fence is
  three contracts — not the whole repo, not the dependencies, not the deployer's
  other protocols.
- It does not fetch behind auth walls. If a program page needs login, ask the
  operator to paste the scope text.
- It does not begin hunting. Intake ends when `case.md` is written; the strands
  read it and start.

Once `case.md` exists, hand control to the priming phase (`learning-loop.md` +
`knowledge.md` build the hit list) and then the strand(s).
