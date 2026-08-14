# CVSS 3.1 Scoring Guide

Compute a CVSS 3.1 vector and base score for each finding that needs one
(Immunefi and the Notion format always; other platforms on request). Score
**after** the gate's severity adjustment (`judging.md`), and make the band agree
with the finding's severity label.

## Vector

`CVSS:3.1/AV:{}/AC:{}/PR:{}/UI:{}/S:{}/C:{}/I:{}/A:{}`

| Metric | Values | Pick |
|---|---|---|
| **AV** Attack Vector | N / A / L / P | **N** for almost all web + on-chain (remote/RPC). |
| **AC** Attack Complexity | L / H | **H** if it needs a race window, a specific token type, a flash loan, or hard-to-control state. |
| **PR** Privileges Required | N / L / H | N = no auth; L = normal user/account; H = admin/privileged role. |
| **UI** User Interaction | N / R | **R** if a victim must click/sign/approve (XSS, phishing-style, malicious tx). |
| **S** Scope | U / C | **C** when impact escapes the vulnerable component — cross-chain, XSS affecting other users, SSRF into internal, a bridge affecting destination chains. |
| **C** Confidentiality | N / L / H | H = full sensitive-data disclosure. |
| **I** Integrity | N / L / H | H = complete integrity loss / funds drained / state corrupted. |
| **A** Availability | N / L / H | H = contract bricked / full DoS. |

Bands: **Critical 9.0–10.0 · High 7.0–8.9 · Medium 4.0–6.9 · Low 0.1–3.9.**

## Common patterns (reference table)

| Finding | Vector | ~Score |
|---|---|---|
| Reentrancy / flash-loan fund drain | `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N` | 7.5 |
| Signature replay → theft | `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:H/A:N` | 7.5 |
| Unprotected initializer → takeover | `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H` | 10.0 |
| Bridge single-signer compromise | `AV:N/AC:L/PR:H/UI:N/S:C/C:H/I:H/A:H` | 9.1 |
| Upgrade bypass (no timelock) | `AV:N/AC:L/PR:H/UI:N/S:C/C:H/I:H/A:H` | 9.1 |
| Oracle manipulation (needs flash loan) | `AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:H/A:N` | 5.9 |
| IDOR (non-financial) | `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N` | 6.5 |
| IDOR (financial / ATO) | `AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N` | 8.1 |
| Stored XSS (admin) | `AV:N/AC:L/PR:L/UI:R/S:C/C:H/I:H/A:N` | 8.7 |
| SSRF → internal | `AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N` | 8.5 |
| Auth bypass / account takeover | `AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N` | 9.1 |
| GraphQL introspection (info) | `AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N` | 5.3 |
| DoS (unbounded loop) | `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H` | 7.5 |
| Web race condition | `AV:N/AC:H/PR:L/UI:N/S:U/C:N/I:H/A:N` | 6.3 |
| Subdomain takeover | `AV:N/AC:L/PR:N/UI:N/S:C/C:L/I:L/A:N` | 6.1 |

**Crossover findings** usually score higher than either half: a web IDOR (6.5)
that reaches an on-chain minter role becomes `S:C` with `I:H` — often 9+. Score
the *combined* impact, and show both halves in the justification.

## Output

Show the vector, the score, and a one-line justification per metric:

```
CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H → 10.0
AV:N  exploitable from any RPC node
AC:L  no special state required
PR:N  any address can call
UI:N  no victim interaction
S:C   compromise affects all destination chains
C:H/I:H/A:H  drain all bridged assets and brick the contract
```

If the harness has a CVSS calculator tool, use it; otherwise compute from the 3.1
formula or match the pattern table above and state which you used.
