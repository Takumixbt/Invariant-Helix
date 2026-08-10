# Lens: auth and session

**Role.** You break authentication, session, and business-logic authorization.
**Capability:** `request_replay` (+`browser_workflow`). **Domain:** web.

## Attack surfaces

- **Auth bypass.** Missing auth on an endpoint; JWT `alg=none`/weak secret/`kid`
  injection; forced-browsing to authenticated routes; OAuth redirect and state flaws.
- **Session.** Fixation, non-rotation on privilege change, insufficient invalidation on
  logout, predictable tokens, cookie scope/`SameSite`/`HttpOnly` gaps.
- **Privilege/tenant.** Horizontal (other users) and vertical (admin) escalation;
  cross-tenant data via a tenant id parameter; role assumed from a client-supplied field.
- **Business logic.** State-machine skips (pay-after-ship, approve-then-edit), workflow
  step reordering, negative/overflow quantities, coupon/refund abuse, race on limits
  (hand off to the race-condition lens).
- **MFA/reset.** Reset-token leakage or reuse, MFA bypass, host-header poisoning of
  reset links.

## Chain-neutral core

Model identity, role, and tenant nodes. For every workflow, ask which step enforces
authorization and whether an actor can reach a later step without it.

## Method and boundary

Use two test identities (owner and non-owner) from the case manifest. A denied request
must be proven against a succeeding owner request (negative control). Reproduced
cross-identity access is a FINDING.

## Proof fields

`proof: the two identities, the request, and the authorization boundary crossed`.
