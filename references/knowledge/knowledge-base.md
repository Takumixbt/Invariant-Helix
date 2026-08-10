# Knowledge base

The knowledge base grounds hypothesis generation (gate G5). Instead of improvising,
Invariant Helix matches a target against real history: past exploits, CVE-PoC records,
and researcher findings. A match raises recall without lowering the proof bar.

## Corpora (fetched on demand, never vendored)

`ih-kb-sync` normalizes markdown corpora into one index. Corpora are cloned into the
gitignored `knowledge/cache/` and are not committed, keeping the repo lean and
license-clean.

- **DeFi incident database** (kismp123/DeFi-Security-Incident) — ~800 real exploits by
  year and ~25 vuln classes, with PoCs and CWE/OWASP tags.
- **CVE-PoC corpus** (trickest/cve) — CVE→PoC records by year; feeds `cve_match`.
- **Researcher findings** (e.g. 0xsimao) — fetched on the operator's machine and passed
  with `--source`, since some sites are not reachable from the audit host.

MIT/other upstream licenses stay with the upstream projects; see each source repo.

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

## Refresh

Re-run `ih-kb-sync --fetch` before a campaign to pull the latest history. The index is
an input to G5, not a release artifact.
