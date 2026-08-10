# Solana adapter

## Native semantics

Model programs, instructions, account metas, signer and writable flags,
program-derived addresses, seeds, owners, rent, sysvars, CPI and transaction
account ordering.

## Required checks

- signer and authority constraints on every account;
- PDA seed, bump, owner and canonical-address validation;
- writable and executable account assumptions;
- account initialization, closing and lamport/token conservation;
- CPI target and privilege propagation;
- duplicate or aliased account metas;
- token program and extension semantics;
- instruction ordering, replay and durable nonce assumptions;
- rent, compute and account-size denial of service.

## Execution

Use program-native tests or a local validator/simulator with account snapshots,
instruction traces and negative controls.

## Limits

Do not translate Solidity storage or reentrancy assumptions directly into
account/CPI behavior. Preserve account ownership and transaction ordering.
