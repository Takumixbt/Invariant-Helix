# Web toolchain

No single web tool covers inventory, browser state, raw HTTP, proxy history and
concurrency. Use each tool for its strongest evidence and normalize the output
into the graph.

## Capability matrix

| Capability | Preferred | Evidence |
|---|---|---|
| Passive inventory | certificate/DNS/code sources and scope tools | asset observations |
| Broad crawl | Scrapling | routes, links, forms, scripts, XHR |
| Dynamic workflow | Playwright | browser trace, state transitions and network events |
| Proxy observation | Burp or equivalent | request/response history and site map |
| Direct replay | curl or Python HTTP client | deterministic request/response |
| Discovery fuzzing | ffuf, wfuzz, gobuster or equivalent | candidate differences |
| Specialized checks | ZAP, nuclei or product-specific tools | hypotheses only |
| OOB observation | Collaborator/interactsh/equivalent | callback evidence |
| Race testing | dedicated synchronized runner | barrier, timing and outcome set |
| Version intelligence | CVE and dependency corpus | candidate matches |

## Burp

Use Burp for proxy history, site map, manual request review, controlled
replay, scanner hypotheses and OOB integration where available. Treat the
Burp-MCP bridge as a capability adapter, not the controller.

Require explicit approval for active scans, data access, request sending and
configuration changes. Never inherit permissive defaults from a bridge simply
because they make automation easier.

## Playwright

Use Playwright for:

- JavaScript-heavy route discovery;
- authenticated workflow recording;
- isolated identities and tenant contexts;
- browser storage and token-state mapping;
- UI/API differential tests;
- screenshots, traces, console and network observations;
- two-user workflows and client-side race setup.

Use separate contexts for identities. Do not share cookies or storage between
roles unless the test explicitly examines session sharing.

## Scrapling

Use Scrapling for broad, resumable HTTP discovery and structured extraction.
Its dynamic browser path may use Playwright. Avoid running two independent
crawlers against the same target without a shared rate budget and merge key.

Scrapling's adaptive parsing and XHR capture help discover changing
applications. They do not prove that a route is vulnerable.

## Terminal clients and scanners

Use terminal tools as narrow workers:

- inventory tools discover candidates;
- crawlers collect routes;
- fuzzers compare controlled response dimensions;
- specialized scanners generate hypotheses;
- direct clients reproduce a specific claim.

Do not pipe every output into every scanner. Each job must have a reason,
scope, rate, expected signal, negative control and evidence destination.

## Normalization

Normalize requests by origin, method, path, parameter/body shape, identity,
state and snapshot. Preserve raw evidence separately. Two requests with the
same URL but different roles or bodies are not duplicates.
