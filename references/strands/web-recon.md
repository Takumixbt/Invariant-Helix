# Strand A — Web / API full recon audit

The orchestrator's flow for a web target: map the whole surface, then dispatch the
web actors to hunt it in parallel, then converge, chain, gate, and report. Recon
without a hunt is a sitemap; a hunt without recon is guessing. Helix does both, in
order, and never skips the map.

This file is the **orchestration** for the web strand. The lens depth lives in the
actor files (`agents/*.md`); this file says who runs, in what order, over what.

**The one rule that pays most on web:** *developer inconsistency is the strongest
evidence.* The same operation implemented two ways — auth on `/v2/` but not `/v1/`,
ownership on `GET` but not `DELETE`, validation in the UI but not the mobile API —
is where the paid bugs are. The **sibling rule** explains ~30% of paid IDOR/auth
findings. Recon exists to surface every sibling so the hunt can compare them.

```
   RECON ──────────────► HUNT (parallel actors) ──────────► CHAIN ──► GATE
   recon-agent maps      access-control · injection ·        orchestrator
   the surface           client-side · business-logic        synthesizes + judges
        ▲                        │
        └────────────────────────┘  a finding sends an actor back to recon:
                                     "is there a sibling endpoint with this shape?"
```

---

## Phase 0 — Prime (orchestrator, strong tier)

From the scope card (`scope-intake.md`), the knowledge corpus (`knowledge.md`),
and learned memory (`learning-loop.md`), build the attacker's hit list **before**
dispatching anyone:

1. **Worst outcome here?** Account takeover, fund movement, mass PII, admin RCE —
   these become the actors' goals.
2. **What's novel/custom?** Custom auth, hand-rolled session logic, bespoke
   workflows. First-time code = first-time bugs; framework defaults rarely are.
3. **Where does value/trust sit?** Money movement, role changes, data exports,
   third-party integrations — 10× scrutiny.
4. **What has this program/stack paid for before?** Load matching disclosed
   reports and learned patterns; they seed each actor's bundle.

---

## Phase 1 — Recon (dispatch `recon-agent` first)

`recon-agent` (`agents/recon-agent.md`) runs before the hunters and produces
`.audit/recon/surface.md`: subdomains, routes, parameters, inputs, auth contexts,
secrets, fingerprint. It emits its own recon-native findings
(`subdomain-takeover`, `api-key-exposure`, `info-disclosure`) and hands the
surface map to the hunters via `discovery` signals. Everything downstream works
this map.

Tools bind to capability names (`local-tooling.md`); a missing tool is
coverage-debt, never a silent skip.

---

## Phase 2 — Hunt (dispatch the web actors in parallel)

The orchestrator fans these out to the fast tier, each with its bundle
(`agents/README.md`). They hunt concurrently and return raw findings.

| Actor | Owns | File | Mode |
|---|---|---|---|
| `access-control-agent` | IDOR, auth, JWT, OAuth/SSO, privilege escalation | `agents/access-control-agent.md` | core |
| `injection-agent` | SSRF, SQLi, RCE, SSTI, XXE, path traversal | `agents/injection-agent.md` | core |
| `client-side-agent` | XSS, CORS, open redirect, cache poisoning, smuggling | `agents/client-side-agent.md` | core |
| `business-logic-agent` | workflow abuse, race, mass-assignment, limits | `agents/business-logic-agent.md` | core |
| `graphql-agent` | introspection, field-auth, aliasing/batching, nested DoS | `agents/graphql-agent.md` | deep (if GraphQL) |
| `supply-chain-agent` | dep confusion, CI/CD, subresource, pipeline secrets | `agents/supply-chain-agent.md` | deep |

**Deep web logic:** when the target's **backend source is in scope**,
`business-logic-agent` escalates non-trivial logic to the alternating loop
(`skills/feynman-auditor` ↔ `skills/state-inconsistency-auditor`) — the same
deep-logic engine strand B uses, run on the web backend (Python/Go/TS/…). Business
logic is logic; it gets the loop, not just a breadth pass (`methodology.md`).

### The six universal patterns (every web actor applies these)

These cut across all lenses — the orchestrator puts them in every web actor's
bundle:

```
1  Feature complexity = bug surface — import/export, multi-step, integrations, batch.
2  Developer inconsistency = strongest evidence (THE SIBLING RULE) — same op two
   ways → one is wrong. auth on /v2 not /v1 · ownership on GET not DELETE.
3  The "else branch" bug — gateway/proxy code with a dangerous fallthrough.
4  Import/export = SSRF — every "fetch from URL" feature has had it.
5  Secondary/legacy endpoints = no auth — /v1, /internal, ?format=csv, GraphQL fields.
6  Race windows in financial ops — every "check then act".
```

---

## Phase 3 — Chain (orchestrator, strong tier)

Single bugs pay; chains pay more. The orchestrator reads the actors' raw findings
and their `chain` signals, and builds combinations (from real disclosed chains):

| Chain | A + B | Result |
|---|---|---|
| Open redirect → OAuth ATO | open-redirect + oauth-bypass | account takeover |
| IDOR read → IDOR write | idor(GET) + idor(PUT) | full record control |
| SSRF → cloud metadata → creds | ssrf + info-disclosure | infra compromise |
| XSS → session/token theft | xss-stored + broken-auth | admin ATO |
| Cache poison → stored XSS | cache-poisoning + xss | mass client compromise |
| GraphQL introspection → field-auth gap | graphql-introspection + idor | mass PII exfil |
| Subdomain takeover → auth bypass | subdomain-takeover + broken-auth | session theft |

A chain is a `finding` with `chain_with:` set and severity raised to the combined
impact. It never invents a link — both halves must be real findings or reachable
leads.

---

## Phase 4 — Converge, gate, verify, report (orchestrator, strong tier)

Run the **convergence pipeline** (`convergence.md`): merge duplicates, isolate one
bug per finding, preserve fixes, confirm every endpoint is accounted for, promote
cross-corroborated leads. Then every surviving finding → `judging.md` (refutation →
reachability → trigger → impact). Verify with a runnable PoC (`curl` sequence,
Burp/Repeater trace, or script), score with CVSS (`cvss-guide.md`), write into
`verified.md`. Then the **crossover** pass runs if strand B also ran
(`strands/crossover.md`) — the strong tier reads both strands' output and hunts
the web2↔web3 seam. Report in the operator's format or the Notion peak format
(`report-formatting.md`).

**Do not report** (full list in `judging.md`): self-XSS with no escalation,
logout CSRF, rate-limiting that genuinely blocks exploitation, missing headers
with no impact, theoretical issues with no reachable path.
