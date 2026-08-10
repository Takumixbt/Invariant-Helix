from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.graph_merge import merge, validate_graph
from scripts.normalize_observations import normalize, normalize_line


ROOT = Path(__file__).resolve().parents[1]


class GraphTests(unittest.TestCase):
    def test_sample_graph_has_no_dangling_edges(self) -> None:
        graph = normalize(ROOT / "evals/web/sample-observations.jsonl")
        self.assertEqual(len(graph["nodes"]), 4)
        self.assertEqual(validate_graph(graph), [])

    def test_edge_identity_includes_source(self) -> None:
        common = {
            "case_id": "case", "snapshot_id": "snap", "kind": "actor", "status": "observed",
            "sensitivity": "internal", "properties": {}, "locators": ["fixture"],
            "evidence_refs": ["artifact:a"],
            "edges": [{"relation": "reaches", "to": "state:sink", "evidence_refs": ["artifact:a"]}],
        }
        _, left = normalize_line({**common, "id": "actor:left", "label": "left"}, 1)
        _, right = normalize_line({**common, "id": "actor:right", "label": "right"}, 2)
        self.assertNotEqual(left[0]["id"], right[0]["id"])

    def test_verified_observation_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_line(
                {
                    "case_id": "case", "snapshot_id": "snap", "id": "state:test", "kind": "state",
                    "label": "test", "status": "verified", "sensitivity": "internal",
                    "properties": {}, "locators": ["fixture"], "evidence_refs": [],
                },
                1,
            )

    def test_dangling_edge_is_rejected(self) -> None:
        record = {
            "case_id": "case", "snapshot_id": "snap", "id": "actor:test", "kind": "actor",
            "label": "actor", "status": "observed", "sensitivity": "internal", "properties": {},
            "locators": ["fixture"], "evidence_refs": ["artifact:a"],
            "edges": [{"relation": "reaches", "to": "state:missing", "evidence_refs": ["artifact:a"]}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "dangling"):
                normalize(path)

    def test_mixed_snapshots_are_rejected(self) -> None:
        first = {
            "case_id": "case", "snapshot_id": "one", "id": "state:one", "kind": "state",
            "label": "one", "status": "observed", "sensitivity": "internal", "properties": {},
            "locators": ["one"], "evidence_refs": [],
        }
        second = {**first, "snapshot_id": "two", "id": "state:two", "label": "two"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text(f"{json.dumps(first)}\n{json.dumps(second)}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mixed"):
                normalize(path)

    def test_duplicate_observations_union_evidence(self) -> None:
        base = {
            "case_id": "case", "snapshot_id": "snap", "id": "state:test", "kind": "state",
            "label": "test", "status": "observed", "sensitivity": "internal", "properties": {},
            "locators": ["one"], "evidence_refs": ["artifact:a"],
        }
        second = {**base, "locators": ["two"], "evidence_refs": ["artifact:b"]}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.jsonl"
            path.write_text(f"{json.dumps(base)}\n{json.dumps(second)}\n", encoding="utf-8")
            graph = normalize(path)
        self.assertEqual(graph["nodes"][0]["evidence_refs"], ["artifact:a", "artifact:b"])

    def test_conflict_merge_is_idempotent(self) -> None:
        base = normalize(ROOT / "evals/web/sample-observations.jsonl")
        conflict = copy.deepcopy(base)
        conflict["nodes"][0]["label"] = "conflicting label"
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index, graph in enumerate((base, conflict, base)):
                path = Path(directory) / f"{index}.json"
                path.write_text(json.dumps(graph), encoding="utf-8")
                paths.append(path)
            result = merge(paths)
        self.assertEqual(len(result["merge_conflicts"]), 1)
        self.assertEqual(len(result["merge_conflicts"][0]["alternatives"]), 1)


if __name__ == "__main__":
    unittest.main()
