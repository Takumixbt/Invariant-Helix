from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.validate_coverage import validate

ROOT = Path(__file__).resolve().parents[1]


def _bundle() -> dict:
    return json.loads((ROOT / "evals/web/sample-coverage.json").read_text(encoding="utf-8"))


def _errors(bundle: dict) -> list[str]:
    return validate(bundle)[0]


class ExclusionLaunderingTests(unittest.TestCase):
    """`excluded` states a scope fact. It must never absorb work that was simply not
    done -- that is what turns an incomplete audit into a false clean bill of health."""

    def test_excluding_for_time_is_rejected(self) -> None:
        bundle = _bundle()
        bundle["items"][0].update(status="excluded", exclusion_reason="ran out of time")
        self.assertTrue(any("work not done" in e for e in _errors(bundle)))

    def test_excluding_for_missing_tooling_is_rejected(self) -> None:
        bundle = _bundle()
        bundle["items"][0].update(status="excluded", exclusion_reason="no tooling available")
        self.assertTrue(any("work not done" in e for e in _errors(bundle)))

    def test_excluding_for_difficulty_is_rejected(self) -> None:
        bundle = _bundle()
        bundle["items"][0].update(status="excluded", exclusion_reason="too complex to analyze")
        self.assertTrue(any("work not done" in e for e in _errors(bundle)))

    def test_material_exclusion_needs_explicit_scope_grounds(self) -> None:
        bundle = _bundle()
        bundle["items"][0].update(status="excluded", exclusion_reason="decided to leave it", impact_class="critical")
        self.assertTrue(any("scope/authorization ground" in e for e in _errors(bundle)))

    def test_legitimate_scope_exclusion_is_allowed(self) -> None:
        bundle = _bundle()
        bundle["items"][0].update(
            status="excluded",
            exclusion_reason="out of scope per program rules; asset owned by a third party",
            impact_class="critical",
        )
        exclusion_errors = [e for e in _errors(bundle) if "exclusion_reason" in e or "excluding a" in e]
        self.assertEqual(exclusion_errors, [])

    def test_unauthorized_ground_is_allowed(self) -> None:
        bundle = _bundle()
        bundle["items"][0].update(status="excluded", exclusion_reason="not authorized by the ROE")
        exclusion_errors = [e for e in _errors(bundle) if "exclusion_reason" in e or "excluding a" in e]
        self.assertEqual(exclusion_errors, [])


class CompletenessTests(unittest.TestCase):
    def test_all_excluded_cannot_be_complete(self) -> None:
        bundle = _bundle()
        bundle["termination_status"] = "complete"
        for item in bundle["items"]:
            item.update(status="excluded", exclusion_reason="out of scope per program rules")
        self.assertTrue(any("requires at least one tested" in e for e in _errors(bundle)))

    def test_all_blocked_cannot_be_complete_with_limitations(self) -> None:
        bundle = _bundle()
        bundle["termination_status"] = "complete_with_limitations"
        for item in bundle["items"]:
            item.update(status="blocked", blocker="capability unavailable", impact_class="low")
        self.assertTrue(any("requires at least one tested" in e for e in _errors(bundle)))

    def test_completeness_needs_a_material_path_exercised(self) -> None:
        bundle = _bundle()
        bundle["termination_status"] = "complete"
        # One low-impact item tested; the critical path merely excluded on scope grounds.
        bundle["items"][0].update(status="tested", impact_class="low")
        for item in bundle["items"][1:]:
            item.update(status="excluded", exclusion_reason="out of scope per program rules",
                        impact_class="critical")
        if len(bundle["items"]) > 1:
            self.assertTrue(any("no critical/high path was exercised" in e for e in _errors(bundle)))

    def test_unmodified_fixture_still_validates(self) -> None:
        self.assertEqual(_errors(_bundle()), [])

    def test_inconclusive_termination_is_always_honest(self) -> None:
        bundle = _bundle()
        bundle["termination_status"] = "inconclusive"
        for item in bundle["items"]:
            item.update(status="blocked", blocker="capability unavailable")
        completeness = [e for e in _errors(bundle) if "requires at least one tested" in e]
        self.assertEqual(completeness, [])


if __name__ == "__main__":
    unittest.main()
