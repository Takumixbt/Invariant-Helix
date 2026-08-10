from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.chain_findings import build_chains
from scripts.recon_to_obs import detect_and_parse as recon_parse
from scripts.scrapling_to_obs import detect_and_parse as crawl_parse
from scripts.xray_enumerate import detect_family, enumerate_codebase, posix_to_python

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "adapters/chains/registry.json").read_text(encoding="utf-8"))


class XrayEnumerateTests(unittest.TestCase):
    def test_detects_evm_family(self) -> None:
        self.assertEqual(detect_family(ROOT / "evals/evm", REGISTRY), "evm")

    def test_detects_solana_family(self) -> None:
        # Chain-neutrality: the same code path detects a non-EVM family.
        self.assertEqual(detect_family(ROOT / "evals/solana", REGISTRY), "solana")

    def test_evm_entrypoints_extracted(self) -> None:
        records = enumerate_codebase(ROOT / "evals/evm", REGISTRY, "c", "s")
        entrypoints = [r["label"] for r in records if r["kind"] == "entrypoint"]
        self.assertTrue(any("deposit" in e for e in entrypoints))
        self.assertTrue(any("withdraw" in e for e in entrypoints))

    def test_solana_entrypoints_extracted(self) -> None:
        records = enumerate_codebase(ROOT / "evals/solana", REGISTRY, "c", "s")
        kinds = {r["kind"] for r in records}
        self.assertIn("program", kinds)
        entrypoints = [r["label"] for r in records if r["kind"] == "entrypoint"]
        self.assertTrue(any("deposit" in e for e in entrypoints))

    def test_posix_class_translation(self) -> None:
        self.assertEqual(posix_to_python("[[:alnum:]_]"), "[A-Za-z0-9_]")


class NormalizerTests(unittest.TestCase):
    """Smoke coverage; the real-format parsers are exercised in depth by
    tests/test_recon_parsers.py and tests/test_crawl_parsers.py."""

    def test_crawl_export_becomes_route_nodes(self) -> None:
        _, records = crawl_parse('{"routes":[{"url":"https://app.example.test/api/profile","method":"get"}]}')
        self.assertEqual(records[0]["kind"], "route")
        self.assertEqual(records[0]["status"], "observed")

    def test_recon_export_becomes_host_nodes(self) -> None:
        _, records = recon_parse("app.example.test\n")
        self.assertEqual(records[0]["kind"], "host")


class ChainBuilderTests(unittest.TestCase):
    def test_chain_only_when_graph_connects_components(self) -> None:
        findings = [
            {"finding_id": "f1", "status": "verified", "affected_components": ["route:a"]},
            {"finding_id": "f2", "status": "verified", "affected_components": ["contract:b"]},
        ]
        graph = {"edges": [{"from": "route:a", "to": "contract:b"}]}
        chains = build_chains(findings, graph)
        self.assertEqual(len(chains), 1)
        self.assertEqual(chains[0]["members"], ["f1", "f2"])

    def test_no_chain_without_a_connecting_edge(self) -> None:
        findings = [
            {"finding_id": "f1", "status": "verified", "affected_components": ["route:a"]},
            {"finding_id": "f2", "status": "verified", "affected_components": ["contract:b"]},
        ]
        chains = build_chains(findings, {"edges": []})
        self.assertEqual(chains, [])

    def test_non_releasable_findings_do_not_chain(self) -> None:
        findings = [
            {"finding_id": "f1", "status": "hypothesis", "affected_components": ["route:a"]},
            {"finding_id": "f2", "status": "verified", "affected_components": ["contract:b"]},
        ]
        graph = {"edges": [{"from": "route:a", "to": "contract:b"}]}
        self.assertEqual(build_chains(findings, graph), [])


if __name__ == "__main__":
    unittest.main()
