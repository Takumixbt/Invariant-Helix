# Generic RPC adapter

## Role

Provide Tier 3 coverage for an unknown or unsupported chain. It is a safe
fallback, not a claim of full semantic understanding.

## Collect

- chain identity, network and finality indicators;
- RPC and indexer methods;
- accounts, programs/contracts, code hashes and metadata;
- transactions, messages, events, receipts and state diffs;
- visible authority and asset movements;
- bridge, oracle, relayer and external-service endpoints.

## Rules

Do not assume account-based state, synchronous calls, Solidity arithmetic,
EVM revert behavior, universal finality or standard replay domains. Record
unknown semantics as coverage debt and request a native adapter.

## Minimal output

Emit a normalized graph with evidence, a list of unsupported concepts, safe
read-only observations and a prioritized adapter-development backlog.
