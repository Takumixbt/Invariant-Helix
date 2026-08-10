# Generic infrastructure adapter

## Role

Map authorized infrastructure surfaces into the graph while preserving provider,
account/project, region, network, identity, protocol, and ownership boundaries.

## Capability mapping

- `surface_inventory`: passive DNS/certificate/provider metadata and
  operator-supplied cloud/network inventories;
- `source_analysis`: IaC, Kubernetes, CI/CD, policy, container, and deployment
  configuration review;
- `execution_trace`: provider audit events, proxy/backend traces, CI job logs,
  and workload/runtime evidence;
- `request_replay`: case-bound protocol differential checks;
- `input_mutation`: local/sandbox parser and policy testing;
- `evidence_manifest`: restricted configuration and trace artifacts.

## Admission

Require exact accounts/projects, regions, domains, IP/CIDR ranges, identities,
operations, rates, prohibited effects, and third-party exclusions. Discovery of
an adjacent asset never authorizes interaction.

## Output

Emit provider-native identifiers, graph nodes/edges, effective authority paths,
trust boundaries, configuration/runtime observations, tests and controls,
unsupported provider semantics, and coverage debt.

## Limits

This generic adapter is a Tier 3 inventory and evidence contract. Provider- or
platform-specific assurance requires a native adapter and regression fixtures.
