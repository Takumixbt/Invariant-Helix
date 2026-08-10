# Chain-neutral intermediate representation

The chain branch reasons over common security concepts while adapters provide
the semantics of each virtual machine, execution model or ledger.

## Core objects

### Actor and authority

Represent human users, programs, keepers, validators, relayers, signers,
origins, capabilities, roles and delegated authorities. Record how authority is
proved, scoped, revoked and propagated.

### Program and entry point

Represent contracts, modules, programs, pallets, scripts, validators and
public entry points. Record callable inputs, caller context, mutability,
expected abort behavior and external calls.

### State

Represent storage slots, account data, resources, objects, tables, UTXOs,
queues, caches, checkpoints and derived values. Record ownership, lifetime,
update paths and whether stale values are intentional.

### Value

Represent native currency, tokens, NFTs, positions, shares, debt, rewards,
fees, collateral and sensitive data. Record custody, units, decimals,
valuation source and outflows.

### Message and execution

Represent transactions, instructions, cross-program calls, callbacks, async
receipts, IBC packets, bridge messages, signatures, events, logs and state
diffs. Record ordering, finality, replay domain and failure semantics.

### Invariant and trust assumption

Represent conservation, authorization, solvency, uniqueness, freshness,
ordering, replay protection, liveness, bounded resource use, accounting
relationships and external trust assumptions.

## Adapter output obligations

Each chain family records these obligations and its honest maturity in
`adapters/chains/registry.json`, validated against
`chain-adapter.schema.json`. Methodology-only entries remain Tier 3.

Every native adapter must provide:

1. detection and confidence;
2. source, bytecode, ABI/IDL/schema or equivalent enumeration;
3. entry-point and authority extraction;
4. state and value mapping;
5. execution trace and state-diff extraction;
6. local, fork, testnet or simulator strategy;
7. property and invariant testing strategy;
8. minimal reproduction format;
9. known semantic gaps;
10. evidence references for each translated fact.

## Unknown-chain behavior

The generic adapter may model RPC/indexer-visible accounts, messages, events,
state changes and transactions. It must label unsupported semantics, avoid
VM-specific assumptions and lower coverage confidence. Generic coverage is
useful reconnaissance, not native-chain audit assurance.
