# Knowledge-base fixture

A tiny, synthetic corpus used by tests and CI to exercise `kb_sync` normalization and
`kb_match` grounding without cloning the real (large, mixed-license) corpora. These
files are invented; any resemblance to a real protocol is coincidental. The live
corpora are fetched on demand with `ih-kb-sync --fetch` into the gitignored
`knowledge/cache/` directory.
