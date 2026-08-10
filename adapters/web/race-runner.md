# Race-runner adapter

## Role

Provide bounded client-side request release for an approved race hypothesis.
It does not prove simultaneous server execution and does not perform the final
authoritative reconciliation itself.

## Input contract

```text
case_id
snapshot_id
actor_context
url
target_allowlist
method, headers, body
concurrency and timeout_seconds
barrier_policy = thread-release
sequential_control {status, evidence_ref, summary}
negative_control {status, evidence_ref, summary}
impact_limit
reconciliation_plan
authorization_confirmed (execution only)
```

Live execution additionally requires the validated case manifest plus a
digest-verified evidence manifest/root resolving both control references. The runner
intersects canonical spec URLs with in-scope case targets and enforces case
expiry, capability, identity, request/concurrency and impact limits. It rejects
userinfo, routing override headers, ambiguous encoded path separators, external
execution without the explicit CLI gate, and real-fund mode.

## Output contract

Output contains case/snapshot and case-manifest digest; redacted URL; client
ready/release/finish timing; HTTP response/error; redacted headers/body prefix;
available server correlation identifiers; controls; and reconciliation status.

The controller must append final authoritative state, side-effect counts,
cleanup and impact calculation before a race finding can pass proof.

## Timing limit

The thread barrier coordinates client release requests, but DNS, TLS, socket,
proxy and server scheduling remain variable. Use a more precise last-byte or
multiplexed transport in an isolated fixture when the hypothesis requires it.
