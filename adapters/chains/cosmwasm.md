# CosmWasm and IBC adapter

## Native semantics

Model Rust contracts, instantiate/execute/query/migrate messages, JSON schemas,
storage, funds, submessages, replies, contracts, module permissions and IBC
packets.

## Required checks

- sender and contract-admin authorization;
- funds denomination, amount and refund accounting;
- submessage reply and error behavior;
- migration and version compatibility;
- storage key and serialization assumptions;
- IBC channel, port, timeout, acknowledgement and replay behavior;
- relayer and light-client trust;
- gas and unbounded data paths;
- event correctness for off-chain accounting.

## Execution

Use schema-aware tests, multi-contract simulation and IBC fixtures. Record
chain, height, channel and contract code versions.

## Limits

A local contract test does not prove the full IBC or chain-module security
model. Mark unavailable module and relayer behavior as coverage debt.
