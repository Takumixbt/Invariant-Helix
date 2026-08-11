from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.check_capabilities import (
    CAPABILITIES,
    _is_python_httpx_entrypoint,
    blocked_coverage_items,
    probe,
)
from scripts.validate_coverage import STATUSES as COVERAGE_STATUSES


class CapabilityTests(unittest.TestCase):
    def test_bundled_capabilities_are_always_available(self) -> None:
        report = probe()
        self.assertTrue(report["synchronized_requests"]["available"])
        self.assertTrue(report["evidence_manifest"]["available"])
        self.assertTrue(report["source_analysis"]["available"])

    def test_probe_covers_all_thirteen_capabilities(self) -> None:
        self.assertEqual(set(probe()), set(CAPABILITIES))
        self.assertEqual(len(CAPABILITIES), 13)

    def test_missing_capability_becomes_blocked_coverage(self) -> None:
        # A capability whose tools are absent must yield a well-formed blocked item.
        fake = {"telepathy": {"bundled": False, "tools": ["nonexistent-tool-xyz"]}}
        report = probe(fake)
        self.assertFalse(report["telepathy"]["available"])
        items = blocked_coverage_items(report, case_id="c", snapshot_id="s")
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["status"], "blocked")
        self.assertIn(item["status"], COVERAGE_STATUSES)
        self.assertTrue(item["blocker"])
        self.assertNotEqual(item["owner"], item["verifier_id"])

    def test_available_capability_emits_no_blocked_item(self) -> None:
        fake = {"present": {"bundled": True, "tools": []}}
        self.assertEqual(blocked_coverage_items(probe(fake), case_id="c", snapshot_id="s"), [])

    def test_python_httpx_entrypoint_is_not_recon_httpx(self) -> None:
        scripts_dir = Path(__import__("sysconfig").get_path("scripts"))
        with patch("scripts.check_capabilities.importlib.metadata.distribution") as distribution:
            entry = type("Entry", (), {"name": "httpx", "value": "httpx:main", "group": "console_scripts"})
            distribution.return_value.entry_points = [entry()]
            self.assertTrue(_is_python_httpx_entrypoint(str(scripts_dir / "httpx.exe")))


if __name__ == "__main__":
    unittest.main()
