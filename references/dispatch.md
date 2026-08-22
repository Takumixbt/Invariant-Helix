# Dispatch — the scope decides, nothing else

Two failures kill audits, and they are opposites:

- **Under-scope:** you ran the wrong methodology (web recon on a Solidity repo,
  Solana checks on an EVM target) and wasted the engagement.
- **Over-scope:** you reported things the program excluded. A commercial engine
  on a fund-loss-only bounty rated *centralization-as-designed* as High and led
  with a bootstrap race whose window **closed at deployment**. Both were
  perfectly true statements about the code, and both were worthless.

This file removes both. It converts a scope card into an **exact run plan**, and
nothing outside that plan runs or ships.

> **The rule:** nothing runs that the scope does not authorise, and nothing is
> reported that the scope excludes. If you cannot point at the line of the scope
> that authorises an actor, do not dispatch it.

---

## Step 1 — classify the target

From `scope-intake.md`'s scope card. Detect, do not assume: look at the actual
tree, not the project's self-description.

```
DETECT                          → CLASS
*.sol, foundry.toml, hardhat    → EVM
Anchor.toml, declare_id!, *.rs  → SOLANA
Move.toml, sources/*.move       → MOVE      (Aptos | Sui — check the framework import)
Cargo.toml + cosmwasm_std       → COSMWASM
Scarb.toml, *.cairo             → CAIRO
*.vy                            → VYPER
live host, OpenAPI, JS bundle   → WEB              (a running target you probe)
backend repo (Django/Express/   → BACKEND-SOURCE   (application code you read, no live host)
  Rails/Spring/Go/Flask/FastAPI)
two or more of the above        → HYBRID → run each class's plan, then CROSSOVER
```

A repo containing contracts **and** a frontend is HYBRID only if the scope names
both. A contract repo with an unscoped demo UI is EVM, full stop.

## Step 2 — dispatch by class

Each class gets: one **gate** (mechanical, grep-verifiable, runs before any actor
opens a file), a **core roster**, and the **binding-matrix axes** that actually
apply. Axes that do not apply are not "skipped", they are **not in the grid** —
an empty cell you never had to fill is not coverage debt.

| Class | Gate | Core actors | Matrix axes |
|---|---|---|---|
| EVM | `vm-gates.md` §EVM (+ `x-ray` if installed) | economic · math · access-upgrade · integration | 1,3,4,5,6 |
| SOLANA | `solana-scan.md` (6 checks) | access-upgrade · integration · math · economic | **all 6** (axis 2 is native/WSOL/SPL/T22) |
| MOVE | `vm-gates.md` §MOVE | access-upgrade · integration · math | 1,3,4,5 |
| COSMWASM | `vm-gates.md` §COSMWASM | access-upgrade · integration · economic | 1,3,4,6 |
| CAIRO | `vm-gates.md` §CAIRO | math · access-upgrade · integration | 1,4,5 |
| VYPER | `vm-gates.md` §EVM (shared semantics) | economic · math · access-upgrade | 1,3,4,5 |
| WEB | `web-gates.md` (the endpoint grid) + `strands/web-recon.md` | recon · access-control · injection · client-side · business-logic | web grid: authz · authn · input-sink · race |
| BACKEND-SOURCE | `vm-gates.md` §BACKEND (route+guard+sink scan) | access-control · injection · business-logic | web grid, recovered from source |

**Deep tier** adds `invariant` · `execution-trace` · `periphery` · `gap-hunter`
· **`binding-matrix`** on any contract class, and `graphql` · `supply-chain` on
WEB when the surface exists.

`binding-matrix` is not optional on a deep contract run. It is the coverage
actor, and coverage is the thing hunters structurally miss.

## Step 3 — build the kill-list *before* hunting

Read the program's own exclusions and write them down as a list you will apply at
SCOPE-GATE. Do this **first**, not at report time, so nobody spends a day on a
class that was never payable.

```
KILL-LIST (typical; take the program's actual words over these)
  centralization-as-designed        admin can rug / pause / rotate — trusted role
  pure liveness / DoS               when the program pays for fund loss only
  already-fixed on the deployed artifact
  preconditions closed at deploy    bootstrap races, first-caller-wins, init front-run
  theoretical-only / no actor       no profitable or motivated party exists
  informational / best-practice     unless the program explicitly buys hardening
  self-harm                         the "attack" costs the attacker more than it yields
```

And write the **fence** — the assets explicitly in scope, by address, repo, and
commit. Anything outside the fence is context, never a finding.

## Step 4 — pin the artifact

For any deployed target, before reading a line of code:

```
1. resolve the DEPLOYED artifact (address → implementation → commit)
2. hash it, and match the hash to the source you are about to read
3. if they differ, STOP and re-clone. Auditing HEAD when mainnet runs an older
   commit invalidates every finding you are about to write.
```

This has burned a real engagement: two verified findings were already fixed
on-chain. One command up front prevents it.

## Step 5 — severity comes from the program

Use the program's scale, not a generic one. When the program is binary
(Critical/High only), say which of the two and argue it. When it is CVSS, produce
a vector. **Argue every severity in one clause**, and prefer a calibrated
downgrade — a defended Medium buys more credibility than an inflated High costs,
and triagers read inflation as a signal to discount everything else.

## Step 6 — feed the scope to any external engine

If part of the run uses a third-party engine, upload the scope, threat model, and
kill-list as **context documents** (v12: `v12 context upload` then
`--context-doc`). An engine that has not been told the rules will produce
out-of-scope criticals, and that is an operator error, not a tool defect.

---

## The run plan artifact

Write `.audit/plan.md` before dispatching anything. It is the contract:

```
TARGET      <name>            CLASS  <detected, with the evidence that detected it>
FENCE       <assets, addresses, repo@commit — exactly what is in>
ARTIFACT    <deployed hash == source hash?  yes/no>
GATE        <which gate ran, coverage numbers printed>
ACTORS      <dispatched, with the scope line authorising each>
AXES        <which binding-matrix axes are in the grid, and why the others are not>
KILL-LIST   <the program's exclusions, verbatim>
SEVERITY    <the program's scale>
```

If a finding cannot be traced back to a line of this plan, it does not ship.
