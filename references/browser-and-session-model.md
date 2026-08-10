# Browser and session model

Modern applications are state machines. A browser audit must model identities,
storage and workflow transitions rather than merely click pages.

## Context model

Create one isolated context per actor or deliberately shared session:

~~~text
context = browser + cookies + local storage + session storage + permissions
page    = UI surface inside the context
network = requests, responses, WebSockets and service-worker activity
state   = server state plus client-visible state
~~~

Use named contexts such as user_a, user_b, tenant_a, tenant_b, admin_test and
unauthenticated. Never copy credentials between contexts accidentally.

## Authentication capture

Record:

- login and logout transitions;
- recovery and enrollment flows;
- token issuance, refresh and revocation;
- cookie flags and scope;
- session rotation;
- device, origin and MFA assumptions;
- server-side identity observed in responses.

Store only redacted token fingerprints in the graph. Keep sensitive browser
artifacts in a restricted evidence location.

## Workflow recording

A workflow step contains:

- actor/context;
- precondition;
- UI action or direct request;
- expected state transition;
- observed network calls;
- response and UI result;
- cleanup;
- negative control.

Convert recorded workflows into deterministic replay plans. A screenshot alone
is not a proof of the underlying server action.

## Differential identities

For authorization testing, compare:

- same object, different actor;
- same actor, different tenant;
- same action, authenticated versus anonymous;
- same request, UI-generated versus direct;
- same operation, old versus refreshed token;
- same state transition, normal versus alternate route.

Change one variable at a time. Record both allowed and denied controls.

## Client/server separation

Treat client-side hiding, disabled buttons and route guards as observations, not
authorization. The server response and state change decide the security claim.

## Browser safety

Block destructive UI actions by default. Use test data and disposable
accounts. Redact screenshots, traces, downloads, local storage and console
output before placing them in a shareable report.
