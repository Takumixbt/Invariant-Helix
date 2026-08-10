# Playwright adapter

## Role

Provide deterministic browser workflows, JavaScript execution, isolated actor
contexts, network events, screenshots and trace evidence.

## Required workflow

1. Create a fresh context for each identity unless sharing is intentional.
2. Load only an in-scope origin.
3. Record UI action, network request, response and state transition.
4. Redact storage, cookies, headers, downloads and screenshots.
5. Save a replayable workflow with preconditions and cleanup.
6. Emit observations to the graph; do not label them vulnerabilities.

## Multi-actor testing

Use separate contexts for user A, user B, tenant A, tenant B and privileged
test roles. Test the same object and workflow through differential controls.
For concurrency, use Playwright only to prepare state; release requests from
the dedicated race runner.

## Requirements

The harness needs Node or Python Playwright, a browser binary or remote CDP
endpoint, a case-scoped profile and a redaction policy. Browser availability
does not imply target authorization.
