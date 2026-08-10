from __future__ import annotations

import unittest

from scripts.converge_findings import converge


def _lead(dedup_key: str, lens: str, root_cause: str, level: str = "low") -> dict:
    return {
        "dedup_key": dedup_key,
        "lens": lens,
        "status": "hypothesis",
        "root_cause": root_cause,
        "confidence": {"level": level, "reason": "single-lens lead"},
    }


class ConvergenceTests(unittest.TestCase):
    def test_multi_lens_agreement_elevates_priority(self) -> None:
        findings = [
            _lead("Vault|withdraw|reentrancy", "invariant-state", "state written after external call"),
            _lead("Vault|withdraw|reentrancy", "execution-trace", "callback re-enters before balance update"),
        ]
        merged, errors = converge(findings)
        self.assertEqual(errors, [])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["priority"], "elevated")
        self.assertEqual(merged[0]["convergence"]["agreement"], 2)

    def test_convergence_never_sets_verified(self) -> None:
        findings = [_lead("k", "a", "x"), _lead("k", "b", "y")]
        merged, errors = converge(findings)
        self.assertEqual(errors, [])
        self.assertEqual(merged[0]["status"], "hypothesis")

    def test_verified_input_is_rejected(self) -> None:
        findings = [{"dedup_key": "k", "lens": "a", "status": "verified", "root_cause": "x",
                     "confidence": {"level": "high", "reason": "r"}}]
        merged, errors = converge(findings)
        self.assertTrue(any("must remain a hypothesis" in e for e in errors))

    def test_shared_premise_agreement_does_not_reach_high(self) -> None:
        # Two lenses, identical mechanism => shared premise => confidence capped at medium.
        findings = [
            _lead("k", "a", "same mechanism", level="medium"),
            _lead("k", "b", "same mechanism", level="medium"),
        ]
        merged, _ = converge(findings)
        self.assertTrue(merged[0]["convergence"]["shared_premise"])
        self.assertEqual(merged[0]["confidence"]["level"], "medium")

    def test_independent_mechanisms_can_reach_high(self) -> None:
        findings = [
            _lead("k", "a", "mechanism one", level="medium"),
            _lead("k", "b", "different mechanism two", level="medium"),
        ]
        merged, _ = converge(findings)
        self.assertFalse(merged[0]["convergence"]["shared_premise"])
        self.assertEqual(merged[0]["confidence"]["level"], "high")

    def test_missing_dedup_key_is_reported(self) -> None:
        merged, errors = converge([{"lens": "a", "status": "hypothesis", "root_cause": "x"}])
        self.assertTrue(any("missing dedup_key" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
