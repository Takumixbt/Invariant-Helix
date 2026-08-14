# Report Formatting — ship it the way the operator wants

Helix emits findings in the format the operator names. If they name a platform,
use its template. If they say "in-house" / "project audit" / "Notion", use the
**Notion peak audit format**. If they name nothing, ask once — platform or
in-house? — and default to Generic.

**One finding per submission report** for bounty platforms (each finding is its
own submission). **One consolidated document** for in-house/Notion audits (all
findings in one report). Always: only CONFIRMED findings from `verified.md` ship;
CVSS band and severity label must agree (`cvss-guide.md`).

```
operator says…                     → use
"hackerone" / "h1"                 → HackerOne
"immunefi"                         → Immunefi
"bugcrowd"                         → Bugcrowd
"intigriti"                        → Intigriti
"cantina"/"code4rena"/"sherlock"   → Contest format
"in-house"/"project"/"notion"/"team" → Notion peak audit format
(nothing / "just a report")        → Generic
"<their own template>"             → follow it exactly; map our fields onto theirs
```

---

## The Notion peak audit format (in-house / project audits)

This is the flagship deliverable for the operator's own and client projects — a
complete, standalone audit report that pastes cleanly into a Notion page. It is
richer than a single-finding bounty submission: it opens with an executive
summary a non-engineer can read, carries a full findings table, then each finding
in depth, and closes with the methodology and coverage so the client trusts what
was and wasn't checked.

Paste-into-Notion notes: use `#`/`##`/`###` headings (Notion turns them into
toggle-friendly headers), `-` bullets, `|` tables (Notion renders them), and
fenced code blocks with a language tag (Notion syntax-highlights them). A
`> callout` line becomes a Notion callout. Keep one blank line between blocks so
Notion's importer splits them correctly.

````markdown
# 🔒 Security Audit — {Project Name}

> **Auditor:** {handle}  ·  **Date:** {date}  ·  **Commit/Deploy:** `{hash or address}`
> **Scope:** {contracts / domains / files reviewed}  ·  **Strands:** {web · web3 · crossover}

---

## Executive Summary

{3–5 sentences a founder can read: what was reviewed, the security posture, the
highest-severity issue, and the headline recommendation. No jargon in the first
two sentences.}

| Severity | Count | Resolved | Open |
|----------|-------|----------|------|
| 🔴 Critical | N | – | – |
| 🟠 High | N | – | – |
| 🟡 Medium | N | – | – |
| 🔵 Low | N | – | – |
| ⚪ Informational | N | – | – |
| **Total** | **N** | | |

---

## Scope & Methodology

**In scope:** {exact asset list from case.md}
**Out of scope:** {excluded}
**Strands run:** {Web recon · Web3 audit · Crossover — one line each on what ran}
**Approach:** Invariant Helix — dual-strand audit with the alternating
Feynman↔State loop, every finding gated (refutation → reachability → trigger →
impact) and PoC-verified. {N} passes to convergence.

---

## Findings Overview

| # | Severity | Title | Strand | Component | Status |
|---|----------|-------|--------|-----------|--------|
| HELIX-001 | 🔴 Critical | {title} | web3 | {contract} | Open |
| HELIX-002 | 🟠 High | {title} | crossover | {seam} | Open |

---

## Detailed Findings

### HELIX-001 · 🔴 Critical · {Title}

> **Component:** `{contract/endpoint}:{line}`  ·  **Class:** {bug_class} ({CWE})
> **CVSS:** `{vector}` → {score}  ·  **Status:** Open

**Summary**
{2–4 sentences: what's wrong and why it matters.}

**Root Cause**
{The precise mechanism. Quote the exact code.}

```{language}
{the vulnerable code, with the line that matters marked}
```

**Attack Scenario**
1. {concrete step with real values}
2. …
3. {attacker achieves impact}

**Proof of Concept**
```{language}
{runnable PoC — Foundry test for EVM, curl sequence for web, script otherwise}
```

**Impact**
{Who loses what. Quantify. Cite a precedent if one exists: "same root cause as
{incident}, ${X} loss."}

**Recommended Fix**
```{language}
{minimal, specific diff}
```

**References**
{prior incidents, EIPs, disclosed reports, standards}

---

{repeat per finding, severity-descending}

---

## Coverage & What We Did Not Test

{Honesty builds trust. State what was covered and — explicitly — any
coverage-debt: tools that weren't available, areas out of scope, assumptions
made. A client trusts an auditor who names the gaps.}

- ✅ {covered area}
- ⚠️ {coverage-debt: e.g., "property fuzzing not run — echidna not available"}
- ⛔ {out of scope}

---

## Appendix — Methodology Detail

{Optional: the x-ray system map, the invariant list, the function-state matrix,
the convergence pass log — for a technical client who wants to see the work.}
````

---

## Bounty platform templates

### Generic / Internal (default)

```markdown
# Bug Report — {Target}
**Severity:** {sev}  ·  **Class:** {bug_class} ({CWE})  ·  **CVSS:** `{vector}` → {score}
**Location:** {contract/endpoint}:{line/path}

## Description
{2–4 sentences: what the system does wrong and why it matters.}

## Attack Path
1. … 2. … 3. {impact}

## Proof of Concept
```{language}
{minimal runnable PoC}
```

## Impact
{Who is the victim; what do they lose; quantify.}

## Recommended Fix
{Specific remediation, line-level.}
```

### HackerOne

```markdown
## Summary
{1–2 sentences, no jargon in the first.}

## Vulnerability Details
**Type:** {CWE / class}  ·  **Severity:** {sev}  ·  **CVSS:** {score} `{vector}`
**Affected Asset:** {URL / address / path}  ·  **Component:** {function / endpoint}

## Steps to Reproduce
1. … 2. … 3. {impact}

## Proof of Concept
{code / curl / screenshot description / tx hash}

## Impact
{worst-case; who's affected; what's at risk}

## Supporting Material
{logs, diff, similar CVEs}
```

### Immunefi (web3 — CVSS always required)

```markdown
**Vulnerability Title:** {title}
**Severity:** {Critical/High/Medium/Low}
**Type:** {Smart Contract / Website-App / Blockchain-DLT}
**Classification:** {Immunefi class — e.g. "Direct theft of user funds"}
**Blockchain/Tech:** {chain}  ·  **Contract:** {address}  ·  **Protocol:** {name}

**Description**
{Detailed, technical. Exact functions, storage, call sequences. Immunefi
reviewers are technical — be specific.}

**Attack Scenario**
{Narrative from setup to impact.}

**Proof of Concept**
```solidity
{Foundry test preferred; concrete numbers}
```

**Impact**
{How much drainable? Which assets? Which users?}

**Recommended Fix**
{Specific, with a diff.}

**References**
{prior audits, EIPs, similar incidents}
```

### Bugcrowd

```markdown
**Title:** {impact-first title}
**VRT:** {category, e.g. "Server-Side Injection > SQLi"}  ·  **Priority:** P{1-5}
**Asset:** {target}

**Description:** {clear, no assumed deep expertise}
**Steps to Reproduce:** 1. … 2. … 3. …
**Expected vs Actual:** {secure behavior} vs {vulnerable behavior}
**PoC:** {embed}
**Impact:** {attacker capability + victim harm}
**CVSS:** `{vector}` ({score})
**Remediation:** {fix}
```

### Intigriti

```markdown
**Title:** {title}  ·  **Severity:** {Critical…Low / Best Practice}
**Affected URL/Asset:** {target}

**Description:** {clear, with context on why it's dangerous}
**Reproduction Steps:** 1. … 2. … 3. …
**PoC:** {link / screenshot / code}
**Impact:** {concrete}
**CVSS 3.1:** `{vector}` → {score}
**Suggested Fix:** {remediation}
```

### Contest (Code4rena / Sherlock / Cantina)

```markdown
## {Title}
**Severity:** {High / Medium}  ·  **Lines:** {github permalink to file#L}

### Summary
{one paragraph}

### Vulnerability Detail
{mechanism, quoted code}

### Impact
{who loses what}

### Proof of Concept
```solidity
{Foundry test}
```

### Recommended Mitigation
{fix}
```

---

## Formatting rules (all formats)

1. **Impact-first titles:** `[Critical] Attester key compromise enables unlimited USDC mint` — not "Access control issue".
2. **No vague impact.** "attacker can do bad things" is unacceptable. Name it: funds drained, account taken over, auth bypassed, {amount} at risk.
3. **PoC must be runnable** or clearly executable via the described steps. Never describe a PoC without providing it.
4. **CVSS**: always for Immunefi and the Notion format; for H1/Bugcrowd/Intigriti when the program or operator wants it.
5. **Severity self-consistency:** the CVSS band and the label agree (Critical 9.0–10.0, High 7.0–8.9, Medium 4.0–6.9, Low 0.1–3.9).
6. **Cite precedent** where one exists — it calibrates severity and builds trust.
7. **Only ship `verified.md`.** No raw findings, no unverified leads in a submission. Leads may appear in the Notion report's appendix, clearly labeled as unconfirmed, if the operator wants them tracked.
