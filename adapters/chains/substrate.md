# Substrate and Polkadot adapter

## Native semantics

Model runtime metadata, pallets, extrinsics, origins, dispatchables, storage
maps, events, weights, fees, runtime upgrades and XCM messages.

## Required checks

- origin and dispatch authorization;
- storage key and migration compatibility;
- weight, proof-size and boundedness;
- arithmetic and balance conservation;
- event and indexer consistency;
- XCM origin, location, asset and barrier checks;
- proxy, multisig and governance authority;
- runtime upgrade and metadata changes;
- era, nonce and replay behavior.

## Execution

Use metadata-aware tests, local nodes, try-runtime-style migration checks and
XCM fixtures when available.

## Limits

Runtime and parachain behavior changes with metadata and configuration. Bind
findings to the exact runtime version.
