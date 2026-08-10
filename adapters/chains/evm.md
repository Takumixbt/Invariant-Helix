# EVM adapter

## Native semantics

Model Solidity/Vyper/Yul source, ABI, bytecode, storage layout, delegatecall,
call/delegatecall/staticcall, fallback/receive, revert behavior, gas,
signatures, logs, proxies and upgrade slots.

## Authority and state

Map msg.sender, msg.value, tx.origin, signatures, permit domains, roles,
ownership, proxy admin and timelock controls. Map storage slots, mappings,
packed values, balances, allowances, indexes, checkpoints and cached prices.

## Required checks

- external call ordering and reentrancy state;
- authorization and initializer reachability;
- arithmetic, units, precision and rounding;
- oracle and price freshness;
- accounting conservation and solvency;
- proxy implementation and storage compatibility;
- callback, flash-loan and composability paths;
- denial of service and gas-bound paths;
- events, off-chain consumers and failed-call handling.

## Execution

Prefer compiler-pinned unit, fork and invariant tests with traces and state
diffs. Record chain ID, block, compiler, optimizer and dependency versions.

## Limits

EVM-like syntax does not guarantee EVM-identical semantics. Use a separate
adapter for TRON or other VM variants.
