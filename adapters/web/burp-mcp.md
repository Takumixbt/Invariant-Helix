# Burp adapter

## Role

Provide proxy observation, request replay, site-map evidence, controlled
active-scan hypotheses and OOB observation when Burp is available.

## Required capabilities

- read proxy history and site map;
- fetch raw HTTP request and response;
- create a replay from an evidence-backed request;
- record scanner or Collaborator observations;
- enforce approval before sending, scanning or changing configuration.

## Rules

Treat MCP tools as untrusted capability boundaries. Require case, scope,
target, actor and impact-limit checks before every active operation. Do not
inherit permissive bridge defaults. A UI Repeater click is not a concurrency
barrier and must not be presented as race proof.

## Graph projection

Map proxy history to request, response, route, actor, role, state, evidence and
snapshot nodes. Preserve raw request evidence separately and redact cookies,
tokens and sensitive bodies.

## Fallback

If Burp is unavailable, use browser network events plus direct HTTP replay.
Record the missing proxy capability as coverage debt.
