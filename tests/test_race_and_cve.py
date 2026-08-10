from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.cve_match import load_inputs, match, version_matches
from scripts.race_runner import allowed, validate_execution_spec


ROOT = Path(__file__).resolve().parents[1]


class RaceRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = json.loads((ROOT / "evals/web/sample-race-spec.json").read_text(encoding="utf-8"))
        self.case = json.loads((ROOT / "evals/web/sample-scope.json").read_text(encoding="utf-8"))

    def _active_local_case(self) -> dict:
        case = copy.deepcopy(self.case)
        case["rules_of_engagement"]["active_testing"] = True
        case["allowed_capabilities"].append("synchronized_requests")
        case["targets"][0]["value"] = "http://127.0.0.1:1/test"
        return case

    def test_dry_run_spec_is_valid_without_case(self) -> None:
        self.assertEqual(
            validate_execution_spec(self.spec, case=None, execute=False, allow_external=False, authorized=False),
            [],
        )

    def test_allowlist_lookalike_is_rejected(self) -> None:
        self.assertFalse(allowed("https://allowed.example.evil.invalid/x", ["https://allowed.example"]))

    def test_allowlist_userinfo_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            allowed("https://allowed.example@127.0.0.1/x", ["https://allowed.example"])

    def test_case_bound_execution_can_validate(self) -> None:
        spec = copy.deepcopy(self.spec)
        spec["authorization_confirmed"] = True
        errors = validate_execution_spec(
            spec,
            case=self._active_local_case(),
            execute=True,
            allow_external=False,
            authorized=True,
            artifact_ids={
                "artifact:ec80dfef68a153d0131ea268",
                "artifact:5557b62d891c6f683690bf8c",
            },
        )
        self.assertEqual(errors, [])

    def test_case_concurrency_limit_is_enforced(self) -> None:
        spec = copy.deepcopy(self.spec)
        spec["authorization_confirmed"] = True
        spec["concurrency"] = 3
        errors = validate_execution_spec(
            spec,
            case=self._active_local_case(),
            execute=True,
            allow_external=False,
            authorized=True,
            artifact_ids={
                "artifact:ec80dfef68a153d0131ea268",
                "artifact:5557b62d891c6f683690bf8c",
            },
        )
        self.assertTrue(any("concurrency exceeds" in error for error in errors))

    def test_routing_override_header_is_blocked(self) -> None:
        spec = copy.deepcopy(self.spec)
        spec["headers"]["Host"] = "other.example"
        errors = validate_execution_spec(spec, case=None, execute=False, allow_external=False, authorized=False)
        self.assertTrue(any("routing override" in error for error in errors))

    def test_real_funds_block_bundled_runner(self) -> None:
        case = self._active_local_case()
        case["rules_of_engagement"]["real_funds_allowed"] = True
        case["rules_of_engagement"]["max_test_funds"] = {"asset": "TEST", "amount": 1}
        spec = copy.deepcopy(self.spec)
        spec["authorization_confirmed"] = True
        errors = validate_execution_spec(
            spec,
            case=case,
            execute=True,
            allow_external=False,
            authorized=True,
            artifact_ids={
                "artifact:ec80dfef68a153d0131ea268",
                "artifact:5557b62d891c6f683690bf8c",
            },
        )
        self.assertTrue(any("cannot enforce real-fund" in error for error in errors))

    def test_expired_authorization_is_blocked(self) -> None:
        case = self._active_local_case()
        case["authorization_expires_at"] = "2020-01-01T00:00:00Z"
        spec = copy.deepcopy(self.spec)
        spec["authorization_confirmed"] = True
        errors = validate_execution_spec(
            spec,
            case=case,
            execute=True,
            allow_external=False,
            authorized=True,
            artifact_ids={
                "artifact:ec80dfef68a153d0131ea268",
                "artifact:5557b62d891c6f683690bf8c",
            },
        )
        self.assertTrue(any("expired" in error for error in errors))


class CveMatcherTests(unittest.TestCase):
    def test_version_range_match(self) -> None:
        self.assertTrue(version_matches("1.2.3", ">=1.0.0,<1.3.0"))
        self.assertFalse(version_matches("2.0.0", ">=1.0.0,<1.3.0"))

    def test_unknown_version_is_unresolved(self) -> None:
        self.assertIsNone(version_matches("vendor-build", ">=1.0.0"))

    def test_sample_is_product_and_version_match(self) -> None:
        components, cves = load_inputs(
            ROOT / "evals/web/sample-components.json",
            ROOT / "evals/web/sample-cves.json",
        )
        result = match(components, cves)
        self.assertEqual(result["candidates"][0]["match"], "product-and-version")

    def test_list_root_inventory_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            inventory = Path(directory) / "inventory.json"
            inventory.write_text('[{"name":"synthetic-service","version":"1.2.3"}]', encoding="utf-8")
            components, _ = load_inputs(inventory, ROOT / "evals/web/sample-cves.json")
        self.assertEqual(len(components), 1)

    def test_outside_range_is_not_a_candidate(self) -> None:
        components = [{"name": "synthetic-service", "version": "2.0.0"}]
        cves = json.loads((ROOT / "evals/web/sample-cves.json").read_text(encoding="utf-8"))
        result = match(components, cves)
        self.assertEqual(result["candidates"], [])
        self.assertEqual(len(result["not_affected"]), 1)


if __name__ == "__main__":
    unittest.main()
