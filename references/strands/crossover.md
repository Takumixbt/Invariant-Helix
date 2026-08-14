# The Crossover — the seam where web2 drives web3

This is the intertwine of the helix, and it is where the peak bugs live.

Strand A audits the web surface. Strand B audits the on-chain code. Each is
blind to the other. But modern targets are not "a web app" or "a protocol" —
they are a web app *that controls* a protocol, or a protocol *fronted by* a web
app. The attacker's highest-value question is neither strand's alone:

> **What on strand A gives me power on strand B — and what on strand B gives me
> power on strand A?**

The crossover pass runs **after both strands have produced their raw findings**.
It reads both graphs at once and hunts the interface. Most auditors never look
here because most auditors do one strand. That is exactly why it pays.

```
        STRAND A (web)                          STRAND B (web3)
   ┌────────────────────┐                  ┌────────────────────┐
   │ admin panel        │───controls──────▶│ owner / minter     │
   │ API endpoint       │───triggers──────▶│ privileged action  │
   │ leaked secret      │═══is also═══════▶│ signer / validator │
   │ frontend JS        │───builds────────▶│ the signed tx      │
   │ price/oracle API   │───feeds─────────▶│ on-chain price read │
   │ session / JWT      │◀──authorizes────│ SIWE / EIP-712 id   │
   └────────────────────┘                  └────────────────────┘
              ▲                                      │
              └──────── the seam Helix hunts ────────┘
```

---

## The seven seams

Each seam is a real, paid bug class. For each, the crossover reads the relevant
finding/lead from *both* strands and asks the chaining question.

### Seam 1 — Web2 auth controls a web3 privileged role

The most common and most severe. A protocol's `owner`, `minter`, `pauser`,
`upgrader`, or `treasury` is operated from a web2 admin panel, an internal tool,
or a CI pipeline.

```
strand A finding: broken-auth / IDOR / privilege-escalation on the admin surface
strand B fact:    that surface's account holds a privileged on-chain role
CROSSOVER:        web2 auth bypass → on-chain owner takeover → mint / drain / upgrade
```

Hunt: from strand B's role map (`xray/system.md`), list every privileged role.
For each, find *how a human operates it* — a web dashboard, an API, a script
with a key. Then check strand A's findings against that surface. An IDOR that
looked medium on its own becomes critical when the object is "the multisig
proposal queue."

### Seam 2 — An API endpoint triggers a privileged on-chain action

The backend signs and submits transactions on the user's or protocol's behalf: a
"claim", a "withdraw", a bridge "release", a reward distribution.

```
strand A finding: business-logic / broken-auth / race on the triggering endpoint
strand B fact:    that endpoint causes the backend signer to submit a tx
CROSSOVER:        web2 logic flaw → attacker-controlled on-chain action
```

Real shape (corpus 2026): **off-chain-signing bridge drains** — the bridge
releases funds when it receives a signed message from an off-chain service; a
flaw in *how the web2 service decides to sign* (missing validation, replayable
request, race) drains the bridge on-chain. The on-chain contract is "correct" —
it verifies the signature. The bug is that the web2 signer signed something it
shouldn't have.

Hunt: for every backend-signed action, apply Feynman to the *decision to sign*.
What does the signer assume about the request? Is that enforced? Can the request
be replayed, raced, or forged?

### Seam 3 — A leaked web2 secret is also an on-chain key

```
strand A finding: api-key-exposure / info-disclosure (leaked .env, git, JS, S3)
strand B fact:    the leaked material is (or unlocks) a signer / deployer /
                  validator / oracle-updater key
CROSSOVER:        credential leak → direct key compromise → drain
```

Real shape (a recurring private-key-compromise class): keys leaked in a
GitHub repo, a `.env` served by the web app, a CI log, or a frontend bundle.
Helix's recon (`web-recon.md` Phase 1a) already sweeps for secrets — the
crossover asks the second question strand A never does: *is this secret an
on-chain key?* A leaked `PRIVATE_KEY=` or a mnemonic in a config is not "info
disclosure, low" — it is "protocol drain, critical."

Hunt: every secret from strand A recon → check if its address holds a role, is a
deployer, or is a configured signer/oracle in strand B's role map.

### Seam 4 — The frontend builds and signs the transaction

The dApp frontend constructs the calldata the user signs. If an attacker
controls what the frontend shows or builds, the user signs a malicious
transaction while believing they approved a benign one.

```
strand A finding: xss-stored / supply-chain (compromised JS) / dependency injection
                  on the dApp frontend
strand B fact:    that frontend builds the tx the user's wallet signs
CROSSOVER:        frontend injection → wallet drain (user signs attacker calldata)
```

Real shape (corpus, "frontend injection" 2021+ and multiple front-end
compromises): a stored XSS or a poisoned dependency rewrites the `to`/`data`/
`value` of the transaction, or swaps the approval target, so the user approves
`transfer(attacker, all)` or `approve(attacker, ∞)`. Strand A calls it XSS.
Strand B never sees it. The crossover calls it a wallet-drain critical.

Hunt: from strand A, take every finding that lets an attacker influence what the
frontend renders or the code it loads. From strand B, confirm the frontend is
the tx-builder. Chain them.

### Seam 5 — A web2 API feeds an on-chain price/oracle

```
strand A finding: the price/quote API is manipulable, cacheable, spoofable,
                  or lacks integrity
strand B fact:    a contract reads that API's value (via a keeper/relayer that
                  posts it on-chain)
CROSSOVER:        web2 price manipulation → on-chain liquidation / mint / mispricing
```

Hunt: strand B's oracle lens lists every off-chain price source that gets posted
on-chain. For each, audit the web2 side (strand A): can the API be manipulated,
its response cached/poisoned, its signature forged, its updater raced?

### Seam 6 — The web↔chain identity boundary (SIWE / EIP-712 / JWT)

Sign-In-With-Ethereum, EIP-712 typed-data logins, and JWTs that encode a wallet
address all sit exactly on the seam between a web session and an on-chain
identity.

```
strand A finding: jwt-bypass / session flaw / signature-verification gap
strand B fact:    that identity maps to on-chain permissions or funds
CROSSOVER:        session/identity forgery → act as another wallet
```

Hunt: SIWE nonce reuse/replay, EIP-712 domain confusion (a signature meant for
one contract accepted by another), JWT that trusts a client-supplied `address`
claim without proving control of the key.

### Seam 7 — Web2 rate-limit / access-control gates an on-chain economic assumption

A protocol assumes "only our backend calls this" or "the web2 layer rate-limits
this", and the on-chain code is written trusting that gate.

```
strand B fact:    a contract function is economically safe ONLY because a web2
                  layer restricts who/how often it's called
strand A finding: that web2 gate is bypassable (direct contract call, or the
                  rate limit doesn't hold)
CROSSOVER:        the "off-chain-enforced" invariant is not enforced on-chain
```

Hunt: from strand B, find every comment or design that says "handled off-chain",
"backend only", "rate-limited by the API". Then confirm on strand A whether the
contract can simply be called directly, bypassing the web2 gate entirely.

---

## How the crossover runs

```
1. LOAD both strands' raw findings + facts:
   .audit/findings/web-raw.md      (strand A findings + surface map + secrets)
   .audit/findings/web3-raw.md     (strand B findings + role map + oracle list)
   .audit/xray/system.md           (privileged roles, value stores, signers)

2. For each of the seven seams, build the join:
   - list strand B's power points (roles, signers, secrets-that-are-keys,
     tx-builders, oracle sources, off-chain-enforced invariants)
   - for each, find the strand A finding/lead that reaches it
   - if both halves exist → a CROSSOVER finding

3. Emit as a chained finding (shared-rules.md format):
   strand: crossover
   chain_with: <the web finding id> + <the web3 fact/finding id>
   severity: the COMBINED impact (usually one or two levels above either half)

4. Gate and verify like any other finding (judging.md). A crossover PoC often
   spans both worlds: the web request that triggers the on-chain effect, shown
   end to end.
```

---

## The crossover mindset

Neither strand's auditor is wrong; they're each half-blind. The web auditor sees
an IDOR and scores it medium because "it's just a config object." The contract
auditor sees a correct signature check and moves on. Only by holding both graphs
at once do you see that the config object *is* the oracle updater and the
correct signature was over *attacker-chosen data the web2 layer was tricked into
signing*.

**Ask the seam question on every finding that touches an interface. A web bug
that reaches on-chain power, or an on-chain assumption that rests on a web
control, is never scored as a single-strand bug.** That is the whole reason
Helix walks both strands before it reports.
