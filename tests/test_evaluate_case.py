from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.evidence_manifest import load_manifest
from scripts.evaluate_case import evaluate
from scripts.graph_merge import load_graph
from scripts.inventory import load_scope
from scripts.validate_coverage import load_bundle
from scripts.validate_findings import load_findings


ROOT = Path(__file__).resolve().parents[1]


class CaseEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = load_scope(ROOT / "evals/web/sample-scope.json")
        self.graph = load_graph(ROOT / "evals/web/sample-graph.json")
        self.findings = load_findings(ROOT / "evals/web/sample-findings.json")
        self.coverage = load_bundle(ROOT / "evals/web/sample-coverage.json")
        self.manifest = load_manifest(ROOT / "evals/web/evidence-manifest.json")

    def test_end_to_end_case_passes(self) -> None:
        errors, summary = evaluate(
            case=self.case,
            graph=self.graph,
            findings=self.findings,
            coverage=self.coverage,
            manifest=self.manifest,
            release=True,
        )
        self.assertEqual(errors, [])
        self.assertEqual(summary["result"], "pass")

    def test_missing_finding_coverage_link_fails(self) -> None:
        findings = copy.deepcopy(self.findings)
        findings[0]["coverage_refs"] = ["coverage:missing"]
        errors, _ = evaluate(
            case=self.case,
            graph=self.graph,
            findings=findings,
            coverage=self.coverage,
            manifest=self.manifest,
            release=True,
        )
        self.assertTrue(any("unresolved coverage_refs" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
