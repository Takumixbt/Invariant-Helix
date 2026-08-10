from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_findings import validate

ROOT = Path(__file__).resolve().parents[1]


def _finding() -> dict:
    findings = json.loads((ROOT / "evals/evm/sample-findings.json").read_text(encoding="utf-8"))
    items = findings["findings"] if isinstance(findings, dict) else findings
    return copy.deepcopy(items[0])


class FindingExtensionTests(unittest.TestCase):
    def test_baseline_sample_still_validates(self) -> None:
        self.assertEqual(validate([_finding()], release=False), [])

    def test_cvss_band_mismatch_is_rejected(self) -> None:
        finding = _finding()
        finding["severity"] = "low"
        # A 9.8 Critical vector on a low-severity finding must be caught.
        finding["cvss"] = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        errors = validate([finding], release=False)
        self.assertTrue(any("cvss band" in e for e in errors))

    def test_matching_cvss_is_accepted(self) -> None:
        finding = _finding()
        finding["severity"] = "critical"
        finding["cvss"] = "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        self.assertEqual(validate([finding], release=False), [])

    def test_lens_without_bundle_digest_is_rejected(self) -> None:
        finding = _finding()
        finding["lens"] = "math-precision"
        errors = validate([finding], release=False)
        self.assertTrue(any("bundle_digest" in e for e in errors))

    def test_convergence_implying_verified_is_rejected(self) -> None:
        finding = _finding()
        finding["convergence"] = {"agreement": 3, "implies_status": "verified"}
        errors = validate([finding], release=False)
        self.assertTrue(any("adjudicated status" in e for e in errors))

    def test_convergence_cannot_evade_by_renaming_the_key(self) -> None:
        # The rule must hold under ANY key, or it is trivially bypassed.
        for key in ("verdict", "outcome", "result", "status"):
            finding = _finding()
            finding["convergence"] = {"agreement": 9, key: "verified"}
            errors = validate([finding], release=False)
            self.assertTrue(
                any("adjudicated status" in e for e in errors), f"key {key!r} evaded the check"
            )

    def test_chain_of_unreleasable_parent_is_rejected(self) -> None:
        finding = _finding()
        finding["chain_of"] = ["finding-does-not-exist"]
        errors = validate([finding], release=False)
        self.assertTrue(any("chain_of parents are not releasable" in e for e in errors))

    def test_chain_of_cannot_reference_itself(self) -> None:
        finding = _finding()
        finding["chain_of"] = [finding["finding_id"]]
        errors = validate([finding], release=False)
        self.assertTrue(any("must not reference the finding itself" in e for e in errors))

    def test_cvss_base_score_cannot_contradict_its_vector(self) -> None:
        finding = _finding()
        finding["severity"] = "critical"
        finding["cvss"] = {"vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "base_score": 1.0}
        errors = validate([finding], release=False)
        self.assertTrue(any("contradicts the vector" in e for e in errors))

    def test_orphan_bundle_digest_without_lens_is_rejected(self) -> None:
        finding = _finding()
        finding["bundle_digest"] = "sha256:orphan"
        errors = validate([finding], release=False)
        self.assertTrue(any("requires the lens" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
