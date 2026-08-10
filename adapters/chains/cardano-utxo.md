# Cardano and UTXO adapter

## Native semantics

Model UTXOs, addresses, values, datums, redeemers, script context, transaction
balancing, reference inputs, minting policies and validity intervals.

## Required checks

- datum/redeemer validation and datum authenticity;
- input ownership and output value conservation;
- minting and burning policy authority;
- reference input and datum freshness;
- validity interval and slot assumptions;
- token bundle and minimum-ADA accounting;
- script execution cost and denial of service;
- double-spend, replay and change-output assumptions.

## Execution

Use a ledger emulator or testnet fixture with complete transaction body,
redeemer, datum, script context and resulting UTXO set.

## Limits

Do not apply account-balance or reentrancy reasoning without translating it
into UTXO and script-context semantics.
