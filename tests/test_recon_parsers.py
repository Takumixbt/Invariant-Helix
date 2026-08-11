from __future__ import annotations

import unittest
from pathlib import Path

from scripts.recon_to_obs import detect_and_parse

ROOT = Path(__file__).resolve().parents[1]
RECON = ROOT / "evals/recon"


def _parse(name: str, forced: str | None = None) -> tuple[str, list[dict]]:
    return detect_and_parse((RECON / name).read_text(encoding="utf-8"), forced)


class NmapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detected, self.records = _parse("nmap.xml")

    def test_autodetects_nmap_xml(self) -> None:
        self.assertEqual(self.detected, "nmap")

    def test_open_ports_become_services(self) -> None:
        ports = {r["properties"]["port"] for r in self.records if r["kind"] == "service"}
        self.assertEqual(ports, {"443", "8080"})

    def test_closed_port_is_excluded(self) -> None:
        # Port 22 is closed in the fixture and must not appear as a service.
        self.assertNotIn("22", {r["properties"]["port"] for r in self.records if r["kind"] == "service"})

    def test_down_host_is_excluded(self) -> None:
        self.assertNotIn("127.0.0.2", {r["label"] for r in self.records})

    def test_service_version_is_captured(self) -> None:
        https = next(r for r in self.records if r["properties"].get("port") == "443")
        self.assertEqual(https["properties"]["product"], "nginx")
        self.assertEqual(https["properties"]["version"], "1.24.0")


class HttpxTests(unittest.TestCase):
    def test_parses_jsonl_and_keeps_status(self) -> None:
        detected, records = _parse("httpx.jsonl", "httpx")
        self.assertEqual(detected, "httpx")
        self.assertEqual(len(records), 2)
        codes = {r["properties"]["status_code"] for r in records}
        self.assertEqual(codes, {200, 401})

    def test_tech_fingerprint_is_retained(self) -> None:
        _, records = _parse("httpx.jsonl", "httpx")
        self.assertIn("React", records[0]["properties"]["tech"])

    def test_secret_values_are_redacted_in_discovery_records(self) -> None:
        _, records = detect_and_parse(
            '{"url":"https://example.test/api/TOPSECRET/token?client_secret=TOPSECRET"}',
            "httpx",
        )
        self.assertEqual(len(records), 1)
        self.assertNotIn("TOPSECRET", str(records[0]))


class FfufTests(unittest.TestCase):
    def test_autodetects_and_extracts_results(self) -> None:
        detected, records = _parse("ffuf.json")
        self.assertEqual(detected, "ffuf")
        self.assertEqual({r["properties"]["status"] for r in records}, {301, 200})

    def test_routes_carry_urls_as_locators(self) -> None:
        _, records = _parse("ffuf.json")
        self.assertTrue(all(r["locators"][0].startswith("https://") for r in records))


class GobusterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detected, self.records = _parse("gobuster.txt")

    def test_autodetects_text_output(self) -> None:
        self.assertEqual(self.detected, "gobuster")

    def test_banner_and_progress_lines_are_skipped(self) -> None:
        self.assertEqual(len(self.records), 3)
        self.assertEqual({r["locators"][0] for r in self.records}, {"/admin", "/backup", "/.git"})

    def test_status_and_size_parsed(self) -> None:
        admin = next(r for r in self.records if r["locators"][0] == "/admin")
        self.assertEqual(admin["properties"]["status"], 301)
        self.assertEqual(admin["properties"]["size"], 169)


class HostnameListTests(unittest.TestCase):
    def test_non_hostname_lines_are_rejected(self) -> None:
        detected, records = _parse("amass.txt")
        self.assertEqual(detected, "hostnames")
        self.assertEqual(len(records), 3)
        self.assertNotIn("not a hostname line", {r["label"] for r in records})


class OutputContractTests(unittest.TestCase):
    def test_all_parsers_emit_observed_nodes_with_locators(self) -> None:
        for name in ("nmap.xml", "httpx.jsonl", "ffuf.json", "gobuster.txt", "amass.txt"):
            _, records = _parse(name)
            self.assertTrue(records, f"{name} produced nothing")
            for record in records:
                self.assertEqual(record["status"], "observed", name)
                self.assertTrue(record["locators"], name)
                self.assertTrue(record["evidence_refs"], name)

    def test_empty_input_is_not_an_error(self) -> None:
        detected, records = detect_and_parse("", None)
        self.assertEqual(records, [])


if __name__ == "__main__":
    unittest.main()
