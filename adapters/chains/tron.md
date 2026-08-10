# TRON and TVM adapter

## Native semantics

Model TVM contracts, ABI, energy/bandwidth, resource delegation, TRX/TRC
assets, permissions, proxies, event logs and chain-specific precompiles.

## Required checks

- owner, active and permission-account controls;
- proxy and upgrade authority;
- TRX/TRC value and resource accounting;
- TVM call, delegatecall and callback behavior;
- ABI and address encoding;
- energy exhaustion and denial of service;
- oracle, exchange and bridge integrations;
- event/indexer consistency.

## Limits

TRON may resemble EVM tooling but must not inherit EVM conclusions without
TVM-specific execution and deployment evidence.
