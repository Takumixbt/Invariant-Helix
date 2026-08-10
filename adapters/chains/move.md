# Move adapter

## Native semantics

Support Move modules, entry functions, resources, objects, abilities,
capabilities, signer references, tables, resource accounts, shared objects and
transaction/block execution.

## Required checks

- capability creation, storage, delegation and revocation;
- signer and object ownership;
- resource type and ability constraints;
- shared-object sequencing and conflict behavior;
- resource conservation and coin type safety;
- friend/visibility boundaries;
- package upgrade and compatibility rules;
- abort paths, atomicity and event correctness;
- cross-module and cross-transaction state coupling.

## Execution

Use Aptos or Sui native tests, prover support where available, local execution,
transaction traces and state snapshots.

## Limits

Aptos and Sui have different object, consensus and execution semantics. Record
the exact chain family instead of treating Move as one runtime.
