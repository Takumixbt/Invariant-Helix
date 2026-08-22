# Web gates — the binding matrix for HTTP surfaces

The contract side got its forcing function: `binding-matrix.md` fills a grid
instead of hunting a hypothesis, and the empty cells are the bugs. The web strand
was still pure hunting — five capable actors, but nothing that made them
*enumerate*. This file is the web equivalent, and it closes that asymmetry.

Same principle, different grid. On a contract you enumerate `(value, handler)`
and ask "who authenticated this?". On a web surface you enumerate
`(endpoint × method × auth-state × object)` and ask the same thing:
**who is allowed, and what stops someone who is not?**

**Every cell produces a LEAD, never a FINDING** (`shared-rules.md` §1). A grid gap
is a hypothesis; an actor still fires the request and reads the response to
confirm. The active-testing gate (`shared-rules.md`) applies to every request
that changes state.

---

## The grid

Build it from the recon surface map (`recon-agent` output: routes, JS-derived
endpoints, OpenAPI/GraphQL schema). One row per endpoint, and for each, these
columns:

```
METHODS      which verbs does it answer? (GET/POST/PUT/PATCH/DELETE + HEAD/OPTIONS)
AUTH-STATE   anon | authed-user-A | authed-user-B | admin — what does each get?
OBJECT       does it take a client-supplied id / key / path / filter?
MUTATES      does it change state, money, or another user's data?
```

The bugs live in the disagreements between cells that should agree:

### The four enumeration axes

**1. AUTHORIZATION — the object matrix (highest yield, ~30% of paid bugs).**
For every endpoint that takes an object id, fire it as **user B for user A's
object**. Then fire the **sibling verbs** on the same object: if `GET /order/{id}`
is scoped, is `PUT`, `DELETE`, `PATCH /order/{id}` scoped too? The classic IDOR is
not an unprotected GET — it is a protected GET whose DELETE sibling nobody scoped.
Fill the grid: object × verb × {owner, non-owner}. Every non-owner cell that
returns anything but a clean reject is a lead.

**2. AUTHENTICATION — the state matrix.** For every endpoint, what does **anon**
get vs **authed**? Look specifically for:
- secondary/legacy paths that skip the middleware: `/v1/…` when the app is on
  `/v2/`, `/internal/…`, `?format=csv`, `.json` suffixes, GraphQL fields behind a
  REST auth wall.
- the **else branch**: a gateway that authenticates the happy path and falls
  through on a malformed token, missing header, or unknown route.
- token handling: does changing `alg` to `none`, swapping a `kid`, or replaying an
  expired/other-user JWT get accepted?

**3. INPUT — the sink matrix.** For every parameter that reaches a dangerous sink,
mark which sink and whether it is confirmable:
```
SSRF     any "fetch from URL", webhook, import-from-link, PDF/image-from-URL, SSO metadata URL
SQLi     any filter/sort/search that reaches the DB — including ORDER BY and column names
SSTI     any value rendered back through a template (name, subject, label)
XXE      any XML/SVG/SOAP/DOCX ingest
PATH     any filename, export name, avatar path, ?file= / ?template=
DESERIAL any cookie/param that is a serialized blob (base64 of pickle/PHP/Java/Node)
CMDi     any value reaching a shell (image processing, git ops, archive handling)
```
The **import/export = SSRF** rule is mechanical: every feature that fetches from a
user URL has had SSRF. Test each against loopback, link-local `169.254.169.254`,
and an OOB canary.

**4. RACE & LOGIC — the sequence matrix.** For every "check then act" on something
of value (balance, coupon, invite, vote, withdrawal, rate limit), fire N parallel
identical requests and check whether the check held. And for every multi-step
workflow, test **step-skipping**: can you reach step 3's endpoint without step 2's
state? Can you replay step 1 after step 3?

---

## The six universal patterns (already in Helix — apply them as grid filters)

These are the lenses each web actor already carries; the grid makes them
exhaustive rather than opportunistic:

```
1  Feature complexity = bug surface — import/export, multi-step, integrations, batch, webhooks
2  Developer inconsistency (SIBLING RULE) — same op two ways, one is wrong
3  The "else branch" bug — a gateway with a dangerous fallthrough
4  Import/export = SSRF — every "fetch from URL" feature has had it
5  Secondary/legacy endpoints = no auth — /v1, /internal, ?format=csv, GraphQL fields
6  Race windows in financial ops — every "check then act"
```

## Confirmation — the part that pays

A web finding that cannot be **demonstrated** is gated out under evidence-or-
silence, so wire confirmation *before* hunting:
- **Reflected/stored** — show the payload executing (screenshot, response body).
- **Blind (SSRF/XXE/RCE/SQLi/deserial)** — you need an OOB listener. Without one
  you will *find* blind bugs and be unable to *prove* them, and drop your
  highest-value results. `local-tooling.md` binds `oob_observation` to Burp
  Collaborator or **`interactsh`** — stand one up first. This is not optional on
  a web engagement; it is the difference between a report and a maybe.
- **Auth/IDOR** — two accounts, and the cross-account request returning the other
  user's data verbatim. One account cannot prove authorization.

## Coverage gate (print before the report ships)

```
endpoints enumerated              N / N   (from recon surface map)
object-taking endpoints           N       — non-owner cell tested: N
                                            sibling verbs tested: N
auth-state matrix filled          N / N   (anon vs authed on every endpoint)
input sinks identified            N       — confirmed: N   blind (OOB-pending): K
race/logic candidates             N       — tested: N
OOB listener up?                  yes/no  <- if no, every blind class is coverage debt
```

An endpoint from the surface map that never entered the grid is coverage debt, and
it goes in the report as debt, not silence.
