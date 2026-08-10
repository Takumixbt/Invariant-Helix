# Reporting and severity

Release output (gate G9) is platform-aware but never relaxes a gate. Only verified or
explicitly downgraded findings are releasable; everything else is coverage debt.

## CVSS 3.1

`ih-cvss` builds and scores a base vector `CVSS:3.1/AV/AC/PR/UI/S/C/I/A`. A finding may
carry a `cvss` field; `validate_findings` checks the vector is well-formed and its
severity band matches the finding `severity`. Common anchors: unprotected initializer
→ 10.0 (Critical); flash-loan price manipulation → ~7.5 (High); reflected XSS with
scope change → High. Cross-chain, XSS, and SSRF-to-internal often set `S:C`.

## Kill chains

`ih-chain` composes findings whose `reachable_path` spans multiple components into a
single chain finding, built **only** from graph edges that already exist and parent
findings that are themselves releasable (`chain_of`). A proven A→B chain outranks two
isolated bugs. IH never invents an edge to complete a chain.

## Platform templates

`knowledge/report-templates/` provides release layouts:

- **hackerone** — title, CVSS 3.1 vector, steps, impact, remediation.
- **immunefi** — adds chain/asset context, deployed addresses, and a runnable PoC.
- **bugcrowd** / **intigriti** — VRT/CVSS severity, PoC, remediation.

Select with `--platform` on the release step. Templates consume released findings
(`references/method/evidence-and-triage.md` release template) and add platform framing
only — never new claims.

## Boundaries

Never include secrets, unnecessary PII, destructive instructions, or unverified
claims. A clean report is verified findings plus a separate coverage-debt and
limitations inventory. Keep the methodology vendor-neutral; do not embed program or
contest framing in the finding body.
