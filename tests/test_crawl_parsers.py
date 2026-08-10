from __future__ import annotations

import unittest
from pathlib import Path

from scripts.scrapling_to_obs import detect_and_parse

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "evals/recon"


def _parse(name: str, forced: str | None = None) -> tuple[str, list[dict]]:
    return detect_and_parse((RECON / name).read_text(encoding="utf-8"), forced)


class HarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detected, self.records = _parse("crawl.har")

    def test_autodetects_har(self) -> None:
        self.assertEqual(self.detected, "har")

    def test_query_parameter_names_are_kept_as_attack_surface(self) -> None:
        profile = next(r for r in self.records if r["properties"]["path"] == "/api/profile")
        self.assertEqual(profile["properties"]["query_params"], ["token", "user_id"])

    def test_query_parameter_values_are_dropped(self) -> None:
        # Values carry secrets and add no structural signal.
        self.assertNotIn("SECRET", str(self.records))

    def test_post_body_parameter_names_are_captured(self) -> None:
        transfer = next(r for r in self.records if r["properties"]["path"] == "/api/transfer")
        self.assertEqual(transfer["properties"]["body_params"], ["amount", "to"])

    def test_userinfo_url_is_refused(self) -> None:
        # https://evil.test@app.example.test/admin must never enter the graph:
        # it is a scope-confusion primitive.
        self.assertEqual(len(self.records), 2)
        self.assertNotIn("/admin", {r["properties"]["path"] for r in self.records})


class BurpTests(unittest.TestCase):
    def test_sitemap_items_become_routes(self) -> None:
        detected, records = _parse("burp-sitemap.json")
        self.assertEqual(detected, "burp")
        self.assertEqual({r["properties"]["path"] for r in records}, {"/login", "/api/v1/users"})

    def test_status_is_retained(self) -> None:
        _, records = _parse("burp-sitemap.json")
        self.assertEqual({r["properties"]["status"] for r in records}, {200, 401})


class SafetyTests(unittest.TestCase):
    def test_control_characters_are_refused(self) -> None:
        _, records = detect_and_parse('[{"url":"https://app.example.test/a\\u0000b"}]')
        self.assertEqual(records, [])

    def test_encoded_traversal_separator_is_refused(self) -> None:
        _, records = detect_and_parse('[{"url":"https://app.example.test/a%2e%2e%2fadmin"}]')
        self.assertEqual(records, [])

    def test_non_http_scheme_is_refused(self) -> None:
        _, records = detect_and_parse('[{"url":"file:///etc/passwd"}]')
        self.assertEqual(records, [])

    def test_urls_are_canonicalized_so_duplicates_collapse(self) -> None:
        _, records = detect_and_parse(
            '[{"url":"https://APP.example.test:443/api"},{"url":"https://app.example.test/api"}]'
        )
        self.assertEqual(len({r["id"] for r in records}), 1)


class OutputContractTests(unittest.TestCase):
    def test_all_records_are_observed_with_locators(self) -> None:
        for name in ("crawl.har", "burp-sitemap.json"):
            _, records = _parse(name)
            self.assertTrue(records, name)
            for record in records:
                self.assertEqual(record["status"], "observed")
                self.assertEqual(record["kind"], "route")
                self.assertTrue(record["locators"])

    def test_empty_input_is_not_an_error(self) -> None:
        self.assertEqual(detect_and_parse("")[1], [])


if __name__ == "__main__":
    unittest.main()
