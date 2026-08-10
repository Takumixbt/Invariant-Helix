# Knowledge base

The knowledge base grounds hypothesis generation (gate G5). Instead of improvising,
Invariant Helix matches a target against real history: past exploits, CVE-PoC records,
and researcher findings. A match raises recall without lowering the proof bar.

## Corpora (fetched on demand, never vendored)

Corpora land in the gitignored `knowledge/cache/`, keeping the repo lean and
license-clean. Two ingesters feed one index:

| Corpus | How it arrives | Ingester |
|---|---|---|
| **DeFi incident database** (kismp123/DeFi-Security-Incident) — ~800 real exploits by year and ~25 vuln classes, with PoCs and CWE tags | `ih-kb-sync --fetch` (git clone) | `kb_sync` |
| **CVE-PoC corpus** (trickest/cve) — CVE→PoC records by year; also feeds `ih-cve` | `ih-kb-sync --fetch` (git clone) | `kb_sync` |
| **Researcher findings** (0xsimao, Solodit exports, contest reports, converted PDFs) | **you fetch locally**, then point the ingester at the directory | `findings_ingest` |

Researcher findings are the highest-signal corpus — every entry is a *confirmed* bug
whose root cause a human wrote down. They are also the least automatable: sites are
often unreachable from an audit host under an egress policy, and scraping terms vary.
So the flow is explicit and local:

```bash
# on a machine with network access, mirror the pages you are entitled to read
wget -r -l2 -k -p https://0xsimao.com/findings -P ./simao

# then, on the audit host
ih-findings-ingest ./simao --source 0xsimao --output knowledge/cache/simao.json
```

`findings_ingest` parses HTML (standard-library `HTMLParser`; scripts and styles are
discarded, never executed) and markdown, extracts title, severity, CWE, and root cause,
and — the important part — **classifies each writeup into IH bug classes and routes it
to the lens that owns them**, so a rounding writeup arrives at `math-precision` and a
stale-price writeup at `trust-gap`.

Upstream licenses stay with the upstream projects; IH stores only a derived index and
always keeps the source link.

## Normalized entry

Each record: `{id, source, vuln_class, cwe, cve_id, chains, title, summary,
root_cause, estimated_loss, poc_refs, keywords}`.

## Matching (leads only)

`ih-kb-match` scores the target graph's node kinds, labels, and properties against each
entry's keywords and vuln class (same-chain-family history is boosted). Each match
becomes:

- an `inferred` observation of kind `pattern` (status is never `observed`), and
- a G5 hypothesis family for the relevant lens,

carrying the source URL as its reference. **A match is always a lead, never a finding.**
The gate still decides whether the pattern is reachable and impactful on this target;
the reachable path and independent falsification are required exactly as for any
hypothesis.

## What grounding can and cannot do

Be precise about this, because it is the difference between a useful claim and a false
one:

- **It does transfer patterns.** A bug class that hit protocol A is matched against the
  shape of protocol B. Most real findings are exactly this — a known class in a new
  place, reached by a path nobody checked. That is the bulk of the value.
- **It does not invent novel bug classes.** No corpus match will discover a category
  nobody has published. Novelty comes from the lenses reasoning about *this* system —
  its economics, its composition, its workflows — and from `ih-chain` composing proven
  findings into a path nobody looked at as a whole.
- **A match is never evidence.** It is a `hypothesized` observation with a source link.
  Reachability and impact on this target are still the lens's job to prove and the
  verifier's job to attack.

## Refresh

Re-run `ih-kb-sync --fetch` (and re-ingest local findings) before a campaign to pull the
latest history. The index is an input to G5, not a release artifact.
