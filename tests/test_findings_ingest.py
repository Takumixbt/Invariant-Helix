from __future__ import annotations

import unittest
from pathlib import Path

from scripts.findings_ingest import classify, ingest, parse_document, parse_simao_detail, parse_simao_index

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


class SimaoSourceTests(unittest.TestCase):
    INDEX = """
    <section class="sa-eng" data-kind="audit">
      <div class="sa-ehead">
        <a class="sa-ehl" href="/reports/demo"><h2 class="sa-name">Demo Protocol</h2>
          <span class="sa-meta">demo.org<span class="sa-sep">·</span>Sherlock<span class="sa-sep">·</span>Lending<span class="sa-sep">·</span>1st January, 2026</span>
        </a>
      </div>
      <article class="sa-find sa-item" data-sev="High">
        <a class="sa-frow" href="/findings/demo-stale-oracle"><span class="sa-sev high">High</span>
          <span class="sa-ft">Stale oracle price accepted during downtime</span><span class="sa-fnum">H-1</span></a>
        <p class="sa-fsum">The protocol accepts an old oracle value without a freshness check.</p>
      </article>
    </section>
    """
    DETAIL = """
    <html><head><link rel="canonical" href="https://0xsimao.com/findings/demo-stale-oracle"></head>
    <body><div class="sa-page sa-one"><h1>Stale oracle price accepted during downtime</h1>
      <p class="sa-meta"><span class="sa-sev high">High</span><span><a class="sa-mlk" href="/reports/demo">Demo audit</a>·Sherlock·Lending·1st January, 2026</span><span class="sa-fnum">H-1</span></p>
      <div class="sa-fbody"><p class="sa-fh">Summary</p><p>Old prices remain accepted.</p>
        <p class="sa-fh">Vulnerability Detail</p><p>The update timestamp is never checked.</p>
        <p class="sa-fh">Impact</p><p>Borrowers can open undercollateralized positions.</p>
        <p class="sa-fh">Recommendation</p><p>Require a freshness threshold.</p>
        <p class="sa-fh">Tool Used</p><p>Manual Review</p>
      </div></div></body></html>
    """

    def test_index_is_one_record_per_finding_with_provenance(self) -> None:
        entries = parse_simao_index(self.INDEX)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["id"], "0xsimao:demo-stale-oracle")
        self.assertEqual(entry["severity"], "high")
        self.assertEqual(entry["finding_ref"], "H-1")
        self.assertEqual(entry["report_url"], "https://0xsimao.com/reports/demo")
        self.assertEqual(entry["content_depth"], "index-summary")

    def test_detail_preserves_postmortem_sections(self) -> None:
        entry = parse_simao_detail(self.DETAIL, Path("demo-stale-oracle.html"))
        self.assertIsNotNone(entry)
        assert entry is not None
        self.assertEqual(entry["severity"], "high")
        self.assertEqual(entry["root_cause"], "The update timestamp is never checked.")
        self.assertEqual(entry["impact"], "Borrowers can open undercollateralized positions.")
        self.assertEqual(entry["recommendation"], "Require a freshness threshold.")
        self.assertEqual(entry["content_depth"], "detail")
        self.assertEqual(entry["source_url"], "https://0xsimao.com/findings/demo-stale-oracle")


if __name__ == "__main__":
    unittest.main()
