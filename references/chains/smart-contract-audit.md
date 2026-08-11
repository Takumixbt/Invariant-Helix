# Smart-contract and protocol audit

This is the chain-independent control procedure. Select the native adapter for
execution semantics and use the contract lenses for specialist depth.

## X-ray

Before hunting, identify:

- protocol purpose, actors and trust boundaries;
- all programs, modules, wrappers, routers and libraries;
- entry points and authority transitions;
- custody, accounting and outflow paths;
- upgrade, pause, emergency and recovery mechanisms;
- oracle, bridge, relayer, keeper and callback dependencies;
- asynchronous or cross-chain state;
- invariants, assumptions, tests and deployment differences;
- custom code versus inherited or standard code.

## Entry-point matrix

For every public or externally reachable entry point record:

~~~text
caller context
inputs and units
guards and authority proof
state read
state write
asset/value flow
external call or message
events and downstream consumers
failure and rollback behavior
reachable next operations
~~~

## Value-flow analysis

For every asset store, trace:

1. how value enters;
2. how ownership or accounting is represented;
3. what authorizes outflow;
4. what conversion, fee, price or rounding occurs;
5. what happens on partial, failed, repeated and emergency paths;
6. whether events and off-chain ledgers agree;
7. whether another program can alter the assumptions.

## State and invariant analysis

Map:

- totals and components;
- balances and checkpoints;
- positions and derived health;
- principal and indexes;
- collateral and obligations;
- shares and fee/reward trackers;
- authority and delegated capabilities;
- messages and replay domains;
- cached values and freshness boundaries.

For each mutation path ask whether reconciliation is immediate, lazy, event
driven, callback driven or intentionally absent.

## Adversarial sequences

Always consider:

- initialize → use → reinitialize;
- deposit → partial withdrawal → claim → final withdrawal;
- borrow → partial repay → borrow again;
- open → modify → liquidate or emergency close;
- approve/delegate → transfer/revoke → use;
- update oracle → transact → update again;
- bridge send → retry → receive → replay;
- upgrade → migrate → old entry point;
- batch path versus single-item path;
- direct entry point versus wrapper or router.

Adapt the sequence to the chain's native execution and finality model.

## Testing ladder

Use the cheapest sufficient proof:

1. source and graph trace;
2. unit test with a counterexample;
3. stateful/invariant fuzzing;
4. local deployment, fork or simulator;
5. testnet or approved live reproduction.

Record tool versions, compiler flags, chain ID, block and fixture state.

## Universal validation

Every material claim must pass execution, reachability, trigger and impact
gates, then independent falsification. A static warning, invariant failure or
fuzz seed is a lead until the actual security consequence is established.
