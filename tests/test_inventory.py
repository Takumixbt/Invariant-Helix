from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.inventory import build_inventory, normalize_target, validate_scope


ROOT = Path(__file__).resolve().parents[1]


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = json.loads((ROOT / "evals/web/sample-scope.json").read_text(encoding="utf-8"))

    def test_sample_scope_is_valid(self) -> None:
        self.assertEqual(validate_scope(self.scope), [])

    def test_empty_authorization_is_rejected(self) -> None:
        self.scope["authorization_reference"] = " "
        self.assertTrue(any("authorization_reference" in error for error in validate_scope(self.scope)))

    def test_naive_expiry_is_rejected(self) -> None:
        self.scope["authorization_expires_at"] = "2030-01-01T00:00:00"
        self.assertTrue(any("authorization_expires_at" in error for error in validate_scope(self.scope)))

    def test_expired_authorization_is_rejected_before_execution(self) -> None:
        self.scope["authorization_expires_at"] = "2020-01-01T00:00:00Z"
        self.assertTrue(any("future" in error for error in validate_scope(self.scope)))

    def test_missing_rule_is_rejected(self) -> None:
        del self.scope["rules_of_engagement"]["max_concurrency"]
        self.assertTrue(any("max_concurrency" in error for error in validate_scope(self.scope)))

    def test_chain_identifier_case_is_preserved(self) -> None:
        target = {
            "type": "program", "value": "SoLaNaCaseSensitive", "chain": "solana",
            "network": "devnet", "environment": "testnet", "in_scope": True,
        }
        self.assertEqual(normalize_target(target), "SoLaNaCaseSensitive")

    def test_explicit_exclusion_is_preserved(self) -> None:
        inventory = build_inventory(self.scope)
        excluded = [item for item in inventory["coverage_items"] if item["status"] == "excluded"]
        self.assertEqual(len(excluded), 1)
        self.assertTrue(excluded[0]["exclusion_reason"])

    def test_no_in_scope_target_is_rejected(self) -> None:
        for target in self.scope["targets"]:
            target["in_scope"] = False
            target.setdefault("exclusion_reason", "excluded")
        self.assertTrue(any("at least one target" in error for error in validate_scope(self.scope)))

    def test_default_port_duplicate_is_detected(self) -> None:
        duplicate = copy.deepcopy(self.scope["targets"][0])
        duplicate["value"] = "https://app.example.test:443/"
        self.scope["targets"].append(duplicate)
        self.assertTrue(any("duplicate target" in error for error in validate_scope(self.scope)))


if __name__ == "__main__":
    unittest.main()
