from __future__ import annotations

import copy
import unittest
from pathlib import Path

from scripts.evidence_manifest import load_manifest, verify
from scripts.inventory import load_scope
from scripts.validate_coverage import load_bundle, validate as validate_coverage
from scripts.validate_findings import load_findings, validate as validate_findings


ROOT = Path(__file__).resolve().parents[1]


class FindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.items = load_findings(ROOT / "evals/web/sample-findings.json")
        self.manifest = load_manifest(ROOT / "evals/web/evidence-manifest.json")
        self.case = load_scope(ROOT / "evals/web/sample-scope.json")

    def test_sample_release_is_valid(self) -> None:
        self.assertEqual(verify(ROOT / "evals/web/evidence-manifest.json", ROOT / "evals/web/evidence"), [])
        self.assertEqual(validate_findings(self.items, True, manifest=self.manifest, case=self.case), [])

    def test_false_positive_verdict_cannot_be_verified(self) -> None:
        items = copy.deepcopy(self.items)
        items[0]["falsification_result"]["verdict"] = "FALSE_POSITIVE"
        self.assertTrue(any("TRUE_POSITIVE" in error for error in validate_findings(items, True, manifest=self.manifest, case=self.case)))

    def test_discoverer_cannot_verify_own_finding(self) -> None:
        items = copy.deepcopy(self.items)
        items[0]["verifier_id"] = items[0]["discoverer_id"]
        items[0]["falsification_result"]["verifier_id"] = items[0]["discoverer_id"]
        self.assertTrue(any("must be different" in error for error in validate_findings(items, True, manifest=self.manifest, case=self.case)))

    def test_unresolved_evidence_is_rejected(self) -> None:
        items = copy.deepcopy(self.items)
        items[0]["evidence_refs"].append("artifact:does-not-exist")
        self.assertTrue(any("unresolved" in error for error in validate_findings(items, True, manifest=self.manifest, case=self.case)))

    def test_adjudicated_p2_exception_is_allowed(self) -> None:
        items = copy.deepcopy(self.items)
        items[0]["proof_level"] = "P2"
        items[0]["runtime_proof_exception"] = {
            "reason": "runtime is unavailable",
            "limitation": "static proof only",
            "adjudicator_id": "program-owner",
        }
        errors = validate_findings(items, True, manifest=self.manifest, case=self.case)
        self.assertFalse(any("requires P3/P4" in error for error in errors))

    def test_illegal_status_transition_is_rejected(self) -> None:
        items = copy.deepcopy(self.items)
        items[0]["status_history"] = [
            items[0]["status_history"][0],
            items[0]["status_history"][2],
        ]
        self.assertTrue(any("illegal status transition" in error for error in validate_findings(items, True, manifest=self.manifest, case=self.case)))


class CoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = load_bundle(ROOT / "evals/web/sample-coverage.json")
        self.manifest = load_manifest(ROOT / "evals/web/evidence-manifest.json")
        self.case = load_scope(ROOT / "evals/web/sample-scope.json")

    def test_sample_coverage_is_valid(self) -> None:
        errors, summary = validate_coverage(self.bundle, case=self.case, manifest=self.manifest)
        self.assertEqual(errors, [])
        self.assertEqual(summary["coverage_debt_by_impact"], {"low": 1})

    def test_complete_cannot_contain_blocked_item(self) -> None:
        bundle = copy.deepcopy(self.bundle)
        bundle["termination_status"] = "complete"
        errors, _ = validate_coverage(bundle, case=self.case, manifest=self.manifest)
        self.assertTrue(any("every coverage item" in error for error in errors))

    def test_material_gap_blocks_limited_completion(self) -> None:
        bundle = copy.deepcopy(self.bundle)
        bundle["items"][1]["impact_class"] = "high"
        errors, _ = validate_coverage(bundle, case=self.case, manifest=self.manifest)
        self.assertTrue(any("material gaps" in error for error in errors))

    def test_owner_and_verifier_must_differ(self) -> None:
        bundle = copy.deepcopy(self.bundle)
        bundle["items"][0]["verifier_id"] = bundle["items"][0]["owner"]
        errors, _ = validate_coverage(bundle, case=self.case, manifest=self.manifest)
        self.assertTrue(any("must differ" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
