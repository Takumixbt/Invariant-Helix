# Chain-neutral reasoning

Chain neutrality means stable reasoning contracts with adapter-specific
semantics. It does not mean pretending that all chains have contracts,
accounts, finality or calls with the same behavior.

## Common questions

For every chain, answer:

- Who can initiate an action?
- How is authority represented and proven?
- What is the public entry surface?
- Which state is owned, shared, global or derived?
- What counts as a successful commit?
- How do failures roll back?
- What can execute before, during or after the operation?
- How are assets valued and conserved?
- How are messages authenticated, ordered and replay-protected?
- What is asynchronous or eventually consistent?
- Which assumptions depend on validators, relayers, oracles or bridges?

## Semantic translation

Translate native concepts into the common model while retaining the original
terminology in properties and evidence:

~~~text
authority      signer/origin/capability/PDA/admin/role
entry point    function/instruction/message/entrypoint/extrinsic/script
state          storage/account/resource/object/UTXO/receipt
external call  call/CPI/IBC/async receipt/bridge message/host function
commit         transaction receipt/finalized block/accepted UTXO/state version
~~~

Never erase differences in account mutability, object ownership, resource
types, gas, callback timing or finality.

## Cross-chain composition

Model each domain separately, then create explicit message edges:

source authority → message construction → bridge/relayer → destination
verification → destination state change → receipt/finality → reconciliation.

Check authentication, replay domain, nonce, amount, asset mapping, finality,
failure recovery and duplicate delivery at every edge.

## Coverage maturity

Every adapter reports:

- native semantic coverage;
- generic coverage;
- unsupported behavior;
- unavailable simulator or trace;
- assumptions supplied by the operator;
- tests actually executed.

“Detected” is not “understood.” “Understood” is not “verified.”
