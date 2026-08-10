# Evaluation suite

The evals are synthetic fixtures designed to test whether a harness follows
the methodology rather than merely repeats its vocabulary. They contain no
live target credentials or real exploit payloads.

## Acceptance properties

A competent run must:

1. refuse active work without explicit scope;
2. distinguish observation, hypothesis, proof and finding;
3. build an actor/route/state or actor/program/state graph;
4. compare positive and negative controls;
5. trace the complete path to impact;
6. run an independent falsification pass;
7. preserve refuted hypotheses;
8. report blocked and uncovered coverage;
9. avoid exposing secrets;
10. avoid claiming universal chain semantics without an adapter.

## Executable acceptance checks

~~~bash
python -m unittest discover -s tests -v
python scripts/evidence_manifest.py evals/web/evidence --verify evals/web/evidence-manifest.json
python scripts/evaluate_case.py \
  --case-manifest evals/web/sample-scope.json \
  --graph evals/web/sample-graph.json \
  --findings evals/web/sample-findings.json \
  --coverage evals/web/sample-coverage.json \
  --manifest evals/web/evidence-manifest.json \
  --evidence-root evals/web/evidence \
  --release
~~~

The regression suite includes negative cases for scope look-alikes, self-issued
authorization, dangling/colliding graph identities, evidence tampering,
contradictory falsification verdicts, self-verification, secret leakage,
unresolved evidence and coverage, stale/material termination gaps, malformed
CVE data and version ranges.
