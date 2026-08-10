# Case manifest

The case manifest is the explicit authorization and safety contract between the
operator and controller. Its machine-readable definition is
`case-manifest.schema.json`; `scripts/inventory.py` enforces its semantic rules.

## Required case fields

```text
case_id
operator
authorization_reference
authorization_expires_at (timezone-aware ISO-8601)
snapshot_id
target_kind (web, chain, combined, infrastructure)
targets
rules_of_engagement
allowed_capabilities
redaction_policy
```

Each target records type, raw value, explicit `in_scope` boolean and environment.
Contract/program/RPC targets also record chain and network. An out-of-scope
target remains in the manifest with `in_scope:false` and an exclusion reason.
Chain-native identifiers are never URL-normalized or case-folded.

## Rules of engagement

```text
active_testing
max_requests
max_concurrency
test_identities
oob_allowed
real_funds_allowed
impact_limit
prohibited_effects
stop_conditions
emergency_contact
data_retention
```

`real_funds_allowed:true` additionally requires an asset and positive maximum
test amount. A tool that cannot enforce the monetary ceiling is not admitted;
the bundled race runner always refuses this mode.

## Semantics

- missing or empty authorization, snapshot or safety limits fail validation;
- at least one target must be explicitly in scope;
- exclusions are deny-dominant over discovered links or redirects;
- active operations require both the corresponding capability and tool-specific
  admission checks;
- environment, chain and network participate in target identity;
- authorization references and restricted details must not be copied into
  public reports.

Changing scope, exclusions, target version, identity, environment, rates,
capabilities or impact limits creates a new snapshot and reopens dependencies.
