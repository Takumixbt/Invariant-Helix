from __future__ import annotations

import unittest
from pathlib import Path

from scripts.kb_match import as_observations, match
from scripts.kb_sync import build_index, normalize_file

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "evals/kb"


class KbSyncTests(unittest.TestCase):
    def test_incident_filename_yields_vuln_class(self) -> None:
        entry = normalize_file(KB / "incidents/2023-07-30_ExampleDEX_reentrancy.md", "incidents")
        assert entry is not None
        self.assertEqual(entry["vuln_class"], "reentrancy")
        self.assertEqual(entry["cwe"], "CWE-841")
        self.assertIn("reentrancy", entry["keywords"])

    def test_cve_file_extracts_cve_id(self) -> None:
        entry = normalize_file(KB / "cve/CVE-2021-99999.md", "cve")
        assert entry is not None
        self.assertEqual(entry["id"], "CVE-2021-99999")
        self.assertEqual(entry["cve_id"], "CVE-2021-99999")

    def test_build_index_is_sorted_and_counted(self) -> None:
        index = build_index([("incidents", KB / "incidents"), ("cve", KB / "cve")])
        self.assertEqual(index["entry_count"], len(index["entries"]))
        ids = [(e["source"], e["id"]) for e in index["entries"]]
        self.assertEqual(ids, sorted(ids))


class KbMatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.index = build_index([("incidents", KB / "incidents"), ("cve", KB / "cve")])

    def test_oracle_graph_matches_oracle_incident(self) -> None:
        graph = {
            "case_id": "c", "snapshot_id": "s",
            "nodes": [
                {"kind": "oracle", "label": "spot price from reserves"},
                {"kind": "state", "label": "collateral flash loan borrow"},
            ],
            "edges": [],
        }
        results = match(graph, self.index, min_score=0.5)
        self.assertTrue(results)
        self.assertTrue(any("oracle" in str(r["vuln_class"]) for r in results))

    def test_matches_are_leads_only(self) -> None:
        graph = {"case_id": "c", "snapshot_id": "s",
                 "nodes": [{"kind": "oracle", "label": "reserves price"}], "edges": []}
        results = match(graph, self.index, min_score=0.5)
        self.assertTrue(all(r["lead_only"] for r in results))

    def test_observations_are_inferred_never_observed(self) -> None:
        graph = {"case_id": "c", "snapshot_id": "s",
                 "nodes": [{"kind": "oracle", "label": "reserves price"}], "edges": []}
        obs = as_observations(match(graph, self.index, min_score=0.5), "c", "s")
        self.assertTrue(obs)
        for record in obs:
            self.assertEqual(record["status"], "inferred")
            self.assertEqual(record["kind"], "pattern")

    def test_unrelated_graph_yields_no_high_score(self) -> None:
        graph = {"case_id": "c", "snapshot_id": "s",
                 "nodes": [{"kind": "cookie", "label": "session flag toggle"}], "edges": []}
        results = match(graph, self.index, min_score=5.0)
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
