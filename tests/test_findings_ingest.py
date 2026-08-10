from __future__ import annotations

import unittest
from pathlib import Path

from scripts.findings_ingest import classify, ingest, parse_document

ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "evals/kb/findings"


class IngestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.entries = ingest(FINDINGS, "0xsimao-style")

    def test_html_and_markdown_writeups_are_both_ingested(self) -> None:
        self.assertEqual(len(self.entries), 2)

    def test_index_stub_is_skipped(self) -> None:
        # A nav/index page carries no finding content and must not pollute the corpus.
        self.assertNotIn("findings", {e["title"].lower() for e in self.entries})

    def test_script_content_is_discarded(self) -> None:
        self.assertNotIn("should be discarded", str(self.entries))

    def test_severity_is_extracted(self) -> None:
        severities = {e["severity"] for e in self.entries}
        self.assertEqual(severities, {"high", "medium"})

    def test_every_entry_routes_to_real_lenses(self) -> None:
        lens_dir = ROOT / "references/lenses"
        for entry in self.entries:
            self.assertTrue(entry["lenses"], f"{entry['id']} routed to no lens")
            for lens in entry["lenses"]:
                self.assertTrue((lens_dir / f"{lens}.md").is_file(), f"unknown lens {lens!r}")

    def test_entries_carry_searchable_keywords(self) -> None:
        for entry in self.entries:
            self.assertTrue(entry["keywords"])

    def test_entry_type_marks_provenance(self) -> None:
        self.assertEqual({e["entry_type"] for e in self.entries}, {"researcher-finding"})


class ClassificationTests(unittest.TestCase):
    def test_rounding_writeup_routes_to_math_precision(self) -> None:
        self.assertIn("math-precision", [lens for _, lens in classify("the division rounds down, precision loss")])

    def test_stale_oracle_routes_to_trust_gap(self) -> None:
        self.assertIn("trust-gap", [lens for _, lens in classify("a stale price is accepted without freshness")])

    def test_reentrancy_routes_to_execution_trace(self) -> None:
        self.assertIn("execution-trace", [lens for _, lens in classify("classic reentrancy on withdraw")])

    def test_idor_routes_to_web_lens(self) -> None:
        self.assertIn("web-api", [lens for _, lens in classify("an IDOR on the profile endpoint")])

    def test_unclassifiable_text_routes_nowhere(self) -> None:
        self.assertEqual(classify("the weather is pleasant today"), [])

    def test_one_lens_is_not_duplicated(self) -> None:
        lenses = [lens for _, lens in classify("reentrancy and read-only reentrancy and a callback")]
        self.assertEqual(len(lenses), len(set(lenses)))


class SafetyTests(unittest.TestCase):
    def test_short_stub_returns_none(self) -> None:
        self.assertIsNone(parse_document(FINDINGS / "index.html", "s"))

    def test_missing_file_is_not_an_error(self) -> None:
        self.assertIsNone(parse_document(FINDINGS / "does-not-exist.md", "s"))


if __name__ == "__main__":
    unittest.main()
