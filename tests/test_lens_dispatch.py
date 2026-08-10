from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.lens_dispatch import plan

ROOT = Path(__file__).resolve().parents[1]

# A capability report with everything available, to isolate roster/verifier logic.
ALL_AVAILABLE = {
    cap: {"available": True, "bundled": True, "installed_tools": [], "candidate_tools": []}
    for cap in (
        "surface_inventory", "http_crawl", "browser_workflow", "proxy_observation",
        "request_replay", "input_mutation", "synchronized_requests", "oob_observation",
        "source_analysis", "chain_simulation", "execution_trace", "property_fuzzing",
        "evidence_manifest",
    )
}


class LensDispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = json.loads((ROOT / "evals/web/sample-graph.json").read_text(encoding="utf-8"))

    def test_only_justified_lenses_are_planned(self) -> None:
        result = plan(self.graph, capability_report=ALL_AVAILABLE)
        planned = {e["lens"] for e in result["lenses"]}
        # The web fixture has route/identity/state nodes; a pure-infra recon lens is
        # only present if host/service/origin/asset kinds exist.
        self.assertIn("web-api", planned)
        for entry in result["lenses"]:
            self.assertTrue(entry["trigger_kinds_present"])

    def test_owner_and_verifier_are_always_distinct(self) -> None:
        result = plan(self.graph, capability_report=ALL_AVAILABLE)
        for entry in result["lenses"]:
            if entry["status"] == "planned":
                self.assertNotEqual(entry["owner"], entry["verifier"])

    def test_single_actor_blocks_every_lens(self) -> None:
        result = plan(self.graph, actors=["solo"], capability_report=ALL_AVAILABLE)
        self.assertEqual(result["planned_count"], 0)
        for entry in result["lenses"]:
            self.assertEqual(entry["status"], "blocked")
            self.assertTrue(any("independent verifier" in b for b in entry["blockers"]))

    def test_unavailable_capability_blocks_lens(self) -> None:
        report = dict(ALL_AVAILABLE)
        report["http_crawl"] = {"available": False, "bundled": False, "installed_tools": [], "candidate_tools": ["scrapling"]}
        result = plan(self.graph, capability_report=report)
        web_api = next(e for e in result["lenses"] if e["lens"] == "web-api")
        self.assertEqual(web_api["status"], "blocked")

    def test_capability_not_admitted_blocks_lens(self) -> None:
        result = plan(self.graph, capability_report=ALL_AVAILABLE, allowed_capabilities=["source_analysis"])
        http_lens = next((e for e in result["lenses"] if e["capability"] == "http_crawl"), None)
        if http_lens is not None:
            self.assertEqual(http_lens["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
