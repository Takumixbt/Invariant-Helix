"""Tests for slither ingest and Foundry PoC scaffold."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.poc import scaffold
from scripts.slither_ingest import from_sarif, from_slither_json, ingest


class SlitherIngestTests(unittest.TestCase):
    def test_slither_json_routes_reentrancy(self) -> None:
        data = {
            "results": {
                "detectors": [
                    {
                        "check": "reentrancy-eth",
                        "impact": "High",
                        "description": "Reentrancy in withdraw()",
                        "elements": [
                            {
                                "source_mapping": {
                                    "filename_relative": "Vault.sol",
                                    "lines": [42],
                                }
                            }
                        ],
                    }
                ]
            }
        }
        leads = from_slither_json(data, "c", "s")
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["status"], "hypothesized")
        self.assertEqual(leads[0]["properties"]["lens"], "execution-trace")
        self.assertEqual(leads[0]["properties"]["bug_class"], "reentrancy")
        self.assertIn("Vault.sol:42", leads[0]["locators"])

    def test_sarif_ingest(self) -> None:
        data = {
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {"driver": {"name": "slither", "rules": [{"id": "tx-origin"}]}},
                    "results": [
                        {
                            "ruleId": "tx-origin",
                            "level": "error",
                            "message": {"text": "tx.origin used for auth"},
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "Auth.sol"},
                                        "region": {"startLine": 9},
                                    }
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        leads = from_sarif(data, "c", "s")
        self.assertEqual(leads[0]["properties"]["lens"], "access-control")
        self.assertEqual(leads[0]["properties"]["bug_class"], "tx-origin-auth")

    def test_ingest_file_roundtrip(self) -> None:
        data = {
            "results": {
                "detectors": [
                    {
                        "check": "divide-before-multiply",
                        "impact": "Medium",
                        "description": "div then mul",
                        "elements": [],
                    }
                ]
            }
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            leads = ingest(path, "c", "s")
            self.assertEqual(leads[0]["properties"]["lens"], "math-precision")


class PocScaffoldTests(unittest.TestCase):
    def test_scaffold_contains_triggers_and_ids(self) -> None:
        finding = {
            "finding_id": "EVM-001",
            "title": "CEI gap",
            "severity": "high",
            "root_cause": "state after call",
            "security_claim": "no reentrancy",
            "affected_components": ["Vault.withdraw"],
            "reachable_path": ["deposit", "withdraw"],
            "minimal_trigger_sequence": ["deposit 100", "reenter withdraw"],
        }
        body = scaffold(finding)
        self.assertIn("contract PoC_EVM_001", body)
        self.assertIn("deposit 100", body)
        self.assertIn("forge-std/Test.sol", body)
        self.assertIn("do not treat as verified", body.lower())


if __name__ == "__main__":
    unittest.main()
