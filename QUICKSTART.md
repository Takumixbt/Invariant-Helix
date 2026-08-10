# Quickstart

One target, end to end. Assumes `pip install -e .` (see `INSTALL.md`). The commands
below run entirely on the bundled synthetic fixtures — no external tools required.

## 1. Bind authorization (G0)

Write a case manifest (`case.json`) with authorization, expiry, snapshot, in-scope and
excluded targets, rules of engagement, and allowed capabilities. Validate it:

```bash
ih-inventory --scope evals/evm/sample-scope.json --output /tmp/inventory.json
ih-check-capabilities --case-manifest evals/evm/sample-scope.json
```

Expired authorization or missing limits is a hard stop.

## 2. Model the target: x-ray -> graph (G2/G3)

```bash
ih-xray-enumerate --scope evals/evm/sample-scope.json --root evals/evm --output /tmp/x.jsonl
ih-normalize /tmp/x.jsonl --output /tmp/graph.json
```

Web and contract observations land in one graph. Swap `evm` for `solana` to see the
same commands detect a different chain family — the methodology is chain-neutral.

## 3. Ground hypotheses against history (G5)

```bash
ih-kb-sync --source evals/kb/incidents --source evals/kb/cve --index /tmp/kb.json
ih-kb-match --graph /tmp/graph.json --index /tmp/kb.json --min-score 0.3
```

Every match is a lead, never a finding.

## 4. Dispatch the attacker lenses (G5)

```bash
ih-lens-dispatch --graph /tmp/graph.json --actor auditor-a --actor auditor-b --output /tmp/plan.json
ih-lens-bundle --dispatch /tmp/plan.json --output-dir /tmp/bundles
ih-evidence /tmp/bundles --case-id eval-evm-001 --snapshot-id fixture-v1 \
  --producer lens-bundler --output /tmp/bundle-manifest.json
```

Only lenses justified by the graph are planned; each gets an independent verifier and a
SHA-256-hashed bundle. Unavailable capabilities are planned as blocked coverage.

## 5. Converge, score, chain

```bash
ih-converge /tmp/lens-findings.json --output /tmp/converged.json    # priority/confidence, never status
ih-cvss "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H"              # 10.0 Critical
ih-chain /tmp/findings.json --graph /tmp/graph.json                 # A->B chains from real edges
```

## 6. Release (G9)

```bash
ih-evaluate-case --case-manifest evals/evm/sample-scope.json --graph evals/evm/sample-graph.json \
  --findings evals/evm/sample-findings.json --coverage evals/web/sample-coverage.json \
  --manifest evals/web/evidence-manifest.json --evidence-root evals/web/evidence --release
```

Exit 0 = releasable. The report is verified findings plus a separate coverage-debt
inventory. Platform framing (HackerOne / Immunefi / Bugcrowd) is in
`knowledge/report-templates/`.
