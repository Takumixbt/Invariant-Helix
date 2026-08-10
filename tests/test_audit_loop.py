from __future__ import annotations

import unittest

from scripts.audit_loop import BRANCHES, evaluate_termination, pass_delta, reopened_by_delta, run


def _pass(nodes: list[str], hypotheses: list[str], refuted: list[str] | None = None) -> dict:
    return {
        "nodes": [{"id": n} for n in nodes],
        "hypotheses": [{"id": h} for h in hypotheses],
        "refuted": [{"id": r} for r in (refuted or [])],
    }


def _item(coverage_id: str, status: str, impact: str, targets: list[str] | None = None) -> dict:
    return {
        "coverage_id": coverage_id, "status": status, "impact_class": impact,
        "target_refs": targets or [], "dependencies": [],
    }


class DeltaTests(unittest.TestCase):
    def test_delta_reports_only_what_is_new(self) -> None:
        delta = pass_delta(_pass(["a"], ["h1"]), _pass(["a", "b"], ["h1", "h2"]))
        self.assertEqual(delta["new_facts"], ["b"])
        self.assertEqual(delta["new_hypotheses"], ["h2"])

    def test_quiet_pass_has_empty_delta(self) -> None:
        delta = pass_delta(_pass(["a"], ["h1"]), _pass(["a"], ["h1"]))
        self.assertEqual(delta, {"new_facts": [], "new_hypotheses": [], "new_refutations": []})


class ReopenTests(unittest.TestCase):
    def test_cleared_item_reopens_when_its_target_is_touched(self) -> None:
        items = [_item("cov:a", "verified", "high", ["state:x"])]
        reopened = reopened_by_delta(items, {"new_facts": ["state:x"], "new_refutations": []})
        self.assertEqual(reopened, ["cov:a"])

    def test_untouched_item_stays_closed(self) -> None:
        items = [_item("cov:a", "verified", "high", ["state:x"])]
        self.assertEqual(reopened_by_delta(items, {"new_facts": ["state:y"]}), [])

    def test_open_item_is_not_reported_as_reopened(self) -> None:
        items = [_item("cov:a", "planned", "high", ["state:x"])]
        self.assertEqual(reopened_by_delta(items, {"new_facts": ["state:x"]}), [])


class TerminationTests(unittest.TestCase):
    """The loop must never let silence stand in for coverage."""

    def _quiet_history(self, quiet: int = 2) -> list[dict]:
        history = [{"delta": {"new_facts": ["a"], "new_hypotheses": [], "new_refutations": []}}]
        history += [{"delta": {"new_facts": [], "new_hypotheses": [], "new_refutations": []}}] * quiet
        return history

    def test_convergence_with_material_gap_is_inconclusive(self) -> None:
        result = evaluate_termination(
            self._quiet_history(), [_item("cov:a", "blocked", "critical")], max_passes=6
        )
        self.assertEqual(result["termination_status"], "inconclusive")
        self.assertIn("silence is not coverage", result["reason"])
        self.assertEqual(result["material_gaps"], ["cov:a"])

    def test_convergence_with_no_gaps_is_complete(self) -> None:
        result = evaluate_termination(
            self._quiet_history(), [_item("cov:a", "verified", "critical")], max_passes=6
        )
        self.assertEqual(result["termination_status"], "complete")

    def test_convergence_with_only_minor_gaps_is_limited(self) -> None:
        items = [_item("cov:a", "verified", "critical"), _item("cov:b", "blocked", "low")]
        result = evaluate_termination(self._quiet_history(), items, max_passes=6)
        self.assertEqual(result["termination_status"], "complete_with_limitations")

    def test_exhausted_budget_while_productive_is_inconclusive(self) -> None:
        history = [{"delta": {"new_facts": ["a"], "new_hypotheses": [], "new_refutations": []}}] * 6
        result = evaluate_termination(history, [_item("cov:a", "verified", "low")], max_passes=6)
        self.assertEqual(result["termination_status"], "inconclusive")
        self.assertIn("budget", result["reason"])

    def test_productive_loop_continues(self) -> None:
        history = [{"delta": {"new_facts": ["a"], "new_hypotheses": [], "new_refutations": []}}]
        result = evaluate_termination(history, [_item("cov:a", "verified", "low")], max_passes=6)
        self.assertEqual(result["termination_status"], "continue")

    def test_no_exercised_item_can_never_be_complete(self) -> None:
        result = evaluate_termination(
            self._quiet_history(), [_item("cov:a", "excluded", "low")], max_passes=6
        )
        self.assertNotEqual(result["termination_status"], "complete")


class RunTests(unittest.TestCase):
    def test_branches_alternate(self) -> None:
        state = {"passes": [_pass(["a"], []), _pass(["a", "b"], []), _pass(["a", "b", "c"], [])]}
        result = run(state, [])
        self.assertEqual([p["branch"] for p in result["passes"]], [BRANCHES[0], BRANCHES[1], BRANCHES[0]])

    def test_handoff_withholds_verdicts(self) -> None:
        # A branch must receive evidence and questions, never the prior branch's verdict.
        result = run({"passes": [_pass(["a"], ["h"])]}, [])
        handoff = result["passes"][0]["handoff"]
        self.assertTrue(handoff["verdicts_withheld"])
        self.assertEqual(handoff["evidence"], ["a"])
        self.assertEqual(handoff["questions"], ["h"])
        self.assertNotIn("verdict", handoff)

    def test_next_branch_is_named_only_while_continuing(self) -> None:
        result = run({"passes": [_pass(["a"], [])]}, [])
        self.assertEqual(result["termination"]["termination_status"], "continue")
        self.assertEqual(result["next_branch"], BRANCHES[1])

    def test_malformed_state_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            run({"passes": "nope"}, [])


if __name__ == "__main__":
    unittest.main()
