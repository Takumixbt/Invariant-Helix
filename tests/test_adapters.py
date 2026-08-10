from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_adapters import validate_registry


ROOT = Path(__file__).resolve().parents[1]


class AdapterRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = json.loads((ROOT / "adapters/chains/registry.json").read_text(encoding="utf-8"))

    def test_registry_is_valid(self) -> None:
        self.assertEqual(validate_registry(self.registry, project_root=ROOT), [])

    def test_methodology_only_cannot_claim_high_maturity(self) -> None:
        registry = copy.deepcopy(self.registry)
        registry["adapters"][0]["maturity_tier"] = 1
        self.assertTrue(any("Tier 3" in error for error in validate_registry(registry, project_root=ROOT)))


if __name__ == "__main__":
    unittest.main()
