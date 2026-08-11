# Knowledge base

The knowledge base grounds hypothesis generation (gate G5). Instead of improvising,
Invariant Helix matches a target against real history: past exploits, CVE-PoC records,
and researcher findings. A match raises recall without lowering the proof bar.

## Corpora (fetched on demand, never vendored)

Corpora land in the gitignored `knowledge/cache/`, keeping the repo lean and
license-clean. The source policy and refresh contract live in
[`source-registry.json`](source-registry.json). Three source-specific paths feed one
normalized index:

| Corpus | How it arrives | Ingester |
|---|---|---|
| **DeFi incident database** (kismp123/DeFi-Security-Incident) — incident writeups by year and vulnerability class, with attack flow, PoC, source, remediation, and lessons sections | `ih-kb-sync --fetch` (git clone) | `kb_sync` |
| **CVE-PoC corpus** (trickest/cve) — CVE→PoC records by year; also feeds `ih-cve` | `ih-kb-sync --fetch` (git clone) | `kb_sync` |
| **Researcher findings** (0xsimao, Solodit exports, contest reports, converted PDFs) | **you fetch locally**, then point the ingester at the directory | `findings_ingest` + `kb_sync --findings-index` |

Researcher findings are the highest-signal corpus — every entry is a *confirmed* bug
whose root cause a human wrote down. They are also the least automatable: sites are
often unreachable from an audit host under an egress policy, and scraping terms vary.
So the flow is explicit and local:

```bash
# on a machine with network access, mirror the pages you are entitled to read
wget -r -l2 -np -k -p https://0xsimao.com/findings -P ./simao

# then, on the audit host
ih-findings-ingest ./simao --source 0xsimao --output knowledge/cache/simao.json
ih-kb-sync --fetch --findings-index knowledge/cache/simao.json \
  --index knowledge/cache/index.json
```

The CVE repository is intentionally refreshable on its own because it is much larger
than the incident corpus:

```bash
ih-kb-sync --fetch --fetch-source defi-incidents --index knowledge/cache/defi.json
ih-kb-sync --fetch --fetch-source trickest-cve --index knowledge/cache/cve.json
```

`findings_ingest` parses HTML (standard-library `HTMLParser`; scripts and styles are
discarded, never executed) and markdown. The 0xSimao adapter understands both layers
of that site:

- the findings ledger becomes one record per finding, preserving its stable URL,
  finding reference, severity, project, auditor/platform, category, date, report, and
  short summary;
- downloaded detail pages are merged into the ledger record and add the summary,
  vulnerability detail/root cause, impact, recommendation, tool used, code references,
  fixed PR, and source/report links.

Every record carries `content_depth` (`index-summary`, `detail`, `postmortem`, or
`cve-record`) and a `provenance` object. The importer also routes the writeup into the
IH lens vocabulary, so a rounding record reaches `math-precision`, a stale-price
record reaches `trust-gap`, and a cross-chain state record reaches
`cross-chain-state`. Unclassified records remain visible as unclassified; they are
not assigned a lens merely to inflate coverage.

Upstream licenses stay with the upstream projects; IH stores only a derived index and
always keeps the source link.

## Normalized entry

Each record retains the old searchable fields and may additionally include:

`{id, source, entry_type, status, title, severity, cwe, cve_id, vuln_class,
chains, summary, root_cause, impact, attack_flow, remediation, lessons,
on_chain_source, poc_detail, estimated_loss, poc_refs, keywords, source_url,
report_url, finding_ref, incident_date, content_depth, provenance}`.

The generated index also includes `source_summary`, which makes corpus coverage
auditable without trusting a README claim or a stale hard-coded count. For git sources,
`source_url` points at the checked-out commit (`provenance.revision`); for local
findings it points back to the upstream page.

## Curated high-signal cards

`references/knowledge/defi-exploit-patterns.md` and the committed cards under
`evals/kb/incidents/` provide a small, source-linked baseline for common DeFi failure
seams: donation/accounting, thin oracles, flash-loan governance, cross-chain message
verification, compiler-generated guards, and concentrated-liquidity rounding. They are
kept intentionally short so they remain reviewable and license-safe. They improve recall
only; a target-specific proof is still required.

Before a campaign, refresh the on-demand corpora and record their snapshot. A source
match without a version, deployment, or reachable feature is a low-confidence lead, not
a release claim.

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
latest history. Pass the resulting researcher index with `--findings-index` so it is
actually merged into the same index used by `ih-kb-match`. The index is an input to G5,
not a release artifact.
