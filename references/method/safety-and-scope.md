# Safety and scope

Aggressive means exhaustive within authorization, not permissionless,
stealthy or destructive.

## Required scope fields

- target identifiers and exclusions;
- authorization reference and expiry;
- authorized operations;
- authorized identities and test data;
- rate, concurrency and request-volume limits;
- prohibited payloads and side effects;
- allowed OOB endpoints;
- approved chain, RPC, fork and testnet environments;
- data handling and retention rules;
- stop condition and contact.
- allowed capabilities, impact limit and snapshot identifier.

## Default controls

- passive discovery before active collection;
- read-only and low-rate by default;
- dry-run mode for new adapters;
- loopback, local fork or testnet preferred;
- disposable identities and balances;
- no secrets in logs;
- no arbitrary public PoC execution;
- no automatic database dumping or real-fund movement;
- no bypass of bot controls, rate limits or access restrictions unless the
  program explicitly authorizes that exact test;
- stop on unexpected state change or scope ambiguity.

## Tool admission

Before a tool runs, check:

~~~text
tool capability
target allowlist
operation type
rate and concurrency
identity
expected signal
impact ceiling
cleanup
evidence destination
~~~

An adapter that cannot enforce these controls is not admitted to active mode.

When a program explicitly permits operator-owned test funds, record asset and
maximum amount and use only a tool that can enforce that ceiling. The bundled
race runner cannot enforce monetary limits and therefore refuses real-fund
mode. Any unrelated-user, third-party or unexpected fund movement is an
immediate stop.

## Data handling

Apply centralized key- and value-aware redaction to labels, locators, URLs,
headers, bodies and summaries. Redact tokens, cookies, private keys,
credentials, personal data and non-public customer records. Store restricted
evidence separately and record only a case-bound artifact reference and
redacted fingerprint in the graph.

## Stop and escalate

Stop when a test exceeds an enforceable operator-owned test-fund limit or
affects unrelated users, third-party services, production data, availability
or legal boundaries. Preserve the observation, document the blocker and ask
the program owner how to proceed.
