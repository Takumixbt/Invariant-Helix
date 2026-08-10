# Starknet and Cairo adapter

## Native semantics

Model Cairo contracts, entry points, storage variables, components, account
abstraction, calldata encoding, selectors, class declarations and upgrade
permissions.

## Required checks

- account validation and signature scheme;
- class hash, upgrade and deployment authority;
- storage layout and component composition;
- felt/integer range, casts and arithmetic constraints;
- selector and calldata decoding;
- message and L1/L2 bridge authentication;
- nonce, replay and finality assumptions;
- event and off-chain indexer consistency.

## Execution

Use Cairo-aware tests and local network/fork fixtures with trace and storage
diff evidence.

## Limits

Do not assume EVM ABI, gas or revert semantics. Preserve Cairo and Starknet
execution details in the evidence.
