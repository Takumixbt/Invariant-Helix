# Chain adapters

Adapters are small semantic contracts. They tell the controller how to
inventory, model, execute, trace and reproduce a chain-specific claim.

## Required adapter interface

Each adapter has a document plus a versioned entry in
`adapters/chains/registry.json`, validated by
`scripts/validate_adapters.py`. The entry defines the equivalent of:

~~~text
detect(target)
enumerate(source_or_deployment)
parse(entry_point_or_message)
map_authority()
map_state_and_assets()
trace(execution)
simulate_or_fork()
property_test()
reproduce(hypothesis)
known_gaps()
~~~

Each operation emits evidence and a coverage status.

The registry also records detection markers, status, maturity tier,
enumeration/authority/state/trace/simulation/property strategies, reproduction
format and known gaps. A methodology-only entry must remain Tier 3; prose alone
cannot claim native executable assurance.

## Adapter selection

Use the most specific adapter detected by source, deployment metadata, chain
ID, RPC behavior and framework markers. If evidence conflicts, preserve both
observations and lower confidence.

## Maturity tiers

- Tier 1: native parser, authority model, execution trace, simulator and
  property-testing path.
- Tier 2: native source/entry/state model and constrained runtime reproduction.
- Tier 3: generic inventory and trace only; semantic coverage explicitly
  limited.

Do not use a Tier 3 result to claim a complete audit.

The shipped adapters are intentionally marked methodology-only/Tier 3 until a
native executable harness and regression fixtures satisfy the registry
contract. External harnesses may promote an adapter only in their case artifact
with tool/version evidence and the missing obligations supplied.

## Adapter maintenance

Pin tool versions and compiler/runtime versions in case artifacts. Add a
regression fixture when a chain-specific bug class or semantic edge is found.
When an adapter cannot express a security property, add a coverage-debt item
instead of silently approximating it.
