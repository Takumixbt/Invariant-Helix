# TON adapter

## Native semantics

Model cells, slices, bags of cells, messages, contracts, bounce behavior,
internal/external messages, gas/value forwarding, wallets and jettons.

## Required checks

- message sender and replay assumptions;
- bounce and bounced-message handling;
- value forwarding and gas reserve;
- cell parsing and bounds;
- query IDs and idempotency;
- wallet, jetton and callback authority;
- asynchronous state transitions;
- message ordering and failure recovery.

## Execution

Use FunC/Tact-compatible local fixtures and message traces. Record code hash,
workchain, logical time and message sequence.

## Limits

TON is asynchronous and message-driven. A synchronous call mental model is
not sufficient.
