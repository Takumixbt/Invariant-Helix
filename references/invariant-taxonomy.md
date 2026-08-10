# Invariant taxonomy

Use invariants to turn vague suspicion into a checkable claim. An invariant
may hold per transaction, across a sequence, at finality, or only after a
reconciliation event.

## Accounting and conservation

- total assets equal accounted components;
- debits equal credits plus approved fees;
- shares, debt, collateral and rewards use consistent units;
- no operation creates value without an authorized source;
- rounding and dust are bounded and assigned intentionally.

## Authorization

- only the intended actor or capability can invoke an operation;
- authority is bound to the object, tenant, message and amount;
- delegated authority cannot outlive revocation or expiry;
- upgrade and emergency powers are constrained and observable.

## State consistency

- derived values reconcile with current inputs or have a defined lazy update;
- every mutation path updates or invalidates its dependents;
- partial and full paths preserve the same relationships;
- aggregate totals equal the sum of valid components.

## Freshness and ordering

- checks use state and price data within the promised freshness window;
- a check cannot be separated from its act by an unprotected mutation;
- messages and callbacks respect intended order;
- stale retries cannot overwrite newer state.

## Uniqueness and idempotency

- a request, nonce, message or settlement is processed at most once;
- retries produce the same final effect;
- batch and single-item paths do not double count;
- replay across chains, contracts or epochs is rejected.

## Solvency and economics

- obligations remain covered under documented conditions;
- fees, incentives and liquidation rules do not create profitable leakage;
- attacker cost, capital, liquidity and timing are realistic;
- price impact and oracle assumptions are explicit.

## Liveness and resource safety

- valid users can progress;
- queues, loops, storage and gas remain bounded;
- one actor cannot permanently block unrelated actors;
- failure and recovery paths preserve assets and authority.

## Web and service invariants

- tenant and object isolation;
- server-side authorization agrees with UI intent;
- session and token transitions are valid;
- state-changing requests have intended origin and replay properties;
- asynchronous jobs, webhooks and retries are idempotent;
- caches do not cross identities or authorization contexts.

## Cross-domain invariants

- source and destination messages authenticate the same intent;
- asset amounts and decimals map correctly;
- nonce and replay domains are unique;
- finality and reorg assumptions are respected;
- failures, refunds and duplicate deliveries reconcile.
