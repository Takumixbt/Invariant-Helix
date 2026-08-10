# Money map — model the value before hunting the bugs

The accounting-first posture. Before any lens runs, build an explicit model of where value
lives, what tracks it, and who is entitled to it. Most high-severity findings are not
exotic code patterns — they are a **tracked total diverging from reality**: value leaves
the contract but the variable tracking it is never decremented, or it is decremented in
one branch of an `if` and not in the sibling branch.

Hunting without this model means reading code and hoping. With it, you have a written
claim to falsify on every path.

## Build it in four parts (gate G3, feeds G4)

### 1. Assets — where value actually sits

Every token, native balance, NFT, position, and off-chain claim the system custodies.
For each: which contract or account holds it, and is the authoritative balance the
*internal ledger* or the *raw balance*? Mixing the two is itself a finding.

### 2. Tracked totals — what claims to know the balance

Every aggregate: `totalSupply`, `totalAssets`, `totalDeposits`, `totalBorrows`, reserve
counters, accumulators, per-actor debt. For each, list **every write site**. A total with
more mutation paths than its asset has movement paths is where desync lives.

### 3. Invariants — the equations that must hold

Write them as equations, not prose:

```text
totalDeposits        == Σ balances[user]
totalSupply * rate   == totalAssets            (± rounding direction)
Σ collateral_value   >= Σ debt_value
burned_on_A          == minted_on_B
```

Each becomes a coverage item with a hypothesis family. An invariant nobody wrote down is
an invariant nobody is checking.

### 4. Actor cohorts — who is entitled, and as of when

Depositors, borrowers, liquidators, LPs, keepers, admins. For each: how they enter, how
they exit, and what they are owed at each point. Distribution bugs live at the membership
boundary, not in the arithmetic (see `references/lenses/temporal-cohort.md`).

## The core question, asked per path

> For every path that moves value, is the tracked total updated in **every** branch,
> including revert, partial, zero-amount, and emergency paths?

Enumerate the branches explicitly. An `if` with an update in one arm and not the other is
the single most productive shape in DeFi auditing.

## Machine assistance

`ih-solidity-analyze` extracts state variables, delta writes (`+=`/`-=` pairs), and guard
predicates — the raw material for parts 2 and 3. It cannot infer intent, so the equations
in part 3 are yours to write. Conservation candidates it surfaces (matched `Δ(A)=+e`,
`Δ(B)=-e` pairs) are proposals, not conclusions.

## Output

The money map is a G3 artifact bound to the case and snapshot. It produces coverage items
before any lens is dispatched, so the hunt starts from a written model of value rather
than from the first file in the directory.
