# Web and API reconnaissance

Web recon is an evidence-producing inventory process, not a race to run every
scanner. Expand breadth, then map stateful behavior and prioritize paths that
cross identity, tenant, trust or value boundaries.

## Recon order

### Passive surface

Collect only within scope:

- supplied domains and subdomains;
- certificate transparency and DNS observations;
- public code, package, documentation and deployment references;
- historical URLs and archived scripts;
- known APIs, mobile clients, partner integrations and callback domains.

Record source, time, confidence and whether the asset is currently live.

### Controlled validation

Resolve and fingerprint candidate hosts with low-rate requests. Record:

- origin, IP/ASN when permitted, port and service;
- TLS identity, redirects, status, title and headers;
- technology/version indicators;
- authentication boundary and program scope;
- whether the host is a third-party dependency or an in-scope asset.

Do not treat a DNS result, certificate or search result as authorization.

### Content and route discovery

Use a layered order:

1. robots, sitemaps, links and documented APIs;
2. historical URLs and public client code;
3. HTTP crawling;
4. browser-assisted discovery for JavaScript routes;
5. authenticated workflows with approved accounts;
6. narrowly targeted path/parameter discovery.

Deduplicate without discarding method, role, body shape or state.

### Client and API mapping

For every route or browser action, capture:

- request method, path, query, body, headers and content type;
- response status, schema, state changes and side effects;
- cookies, storage keys and token type in redacted form;
- user, role, tenant and workflow state;
- XHR/fetch, WebSocket and background requests;
- error behavior and alternate methods.

Build a route-state matrix rather than a flat URL list.

## Web graph nodes

At minimum, create nodes for origin, host, service, route, parameter, request,
response, script, browser action, workflow, identity, role, tenant, token
fingerprint, state and sink.

Useful edges include serves, redirects_to, calls, requires, authenticates,
authorizes, sets, reads, changes, reflects, crosses and reaches.

## Coverage families

Every application receives an explicit coverage decision for:

- authentication, session and account recovery;
- authorization, object ownership and tenant isolation;
- business logic and workflow state;
- request methods, parameter locations and content types;
- CSRF, CORS, caching and origin boundaries;
- server-side fetch, file processing and deserialization;
- injection and output encoding;
- GraphQL, WebSockets and asynchronous jobs;
- uploads, exports, notifications and webhooks;
- rate limits, idempotency and concurrency;
- infrastructure, secrets and dependency exposure.

The family is marked tested, blocked, not applicable or uncovered with a reason.

## Stop conditions

Stop active recon when the target leaves scope, a third-party service is
encountered without authorization, a test could change real data, or rate and
impact limits are unclear. Preserve the discovery as an observation and
escalate rather than guessing.
