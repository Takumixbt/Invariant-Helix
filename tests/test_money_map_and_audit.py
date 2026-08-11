"""Tests for money-map extraction, seed-lead dispatch, and the audit orchestrator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit import run_audit
from scripts.lens_dispatch import plan
from scripts.money_map import build_money_map
from scripts.solidity_analyze import analyze_source
from scripts.xray_git import is_git_root

ROOT = Path(__file__).resolve().parents[1]


VAULT = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
contract Vault {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    address public owner;
    modifier onlyOwner() { require(msg.sender == owner); _; }
    function deposit() external payable {
        balances[msg.sender] += msg.value;
        totalSupply += msg.value;
    }
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        (bool ok,) = msg.sender.call{value: amount}("");
        require(ok);
        balances[msg.sender] -= amount;
        totalSupply -= amount;
    }
    function setTreasury(address t) external {
        owner = t;
    }
    function mint() external {
        if (totalSupply == 0) {
            _mint(msg.sender, 1);
        }
    }
    function _mint(address to, uint256 amt) internal {
        balances[to] += amt;
        totalSupply += amt;
    }
}
"""


class MoneyMapTests(unittest.TestCase):
    def test_conservation_from_paired_deltas(self) -> None:
        facts, leads = analyze_source(VAULT, "Vault.sol")
        for row in facts + leads:
            row["case_id"], row["snapshot_id"] = "c", "s"
        model = build_money_map(facts + leads)
        self.assertIn("totalSupply", model["assets"])
        self.assertTrue(
            model["conservation_candidates"] or any(
                "totalSupply" in str(v) for v in model["write_sites"]
            )
        )

    def test_leads_include_first_depositor_class(self) -> None:
        _, leads = analyze_source(VAULT, "Vault.sol")
        classes = {str(lead["properties"].get("bug_class")) for lead in leads}
        self.assertIn("first-depositor-inflation", classes)
        self.assertIn("reentrancy", classes)  # CEI on withdraw


class SeedLeadDispatchTests(unittest.TestCase):
    def test_seed_leads_attach_to_named_lens(self) -> None:
        graph = {
            "case_id": "c",
            "snapshot_id": "s",
            "nodes": [
                {"id": "n1", "kind": "contract", "label": "Vault"},
                {"id": "n2", "kind": "entrypoint", "label": "withdraw"},
                {"id": "n3", "kind": "state", "label": "totalSupply"},
            ],
        }
        leads = [{
            "id": "hypothesis:cei",
            "kind": "hypothesis",
            "label": "CEI violation",
            "properties": {"lens": "execution-trace", "bug_class": "reentrancy"},
            "locators": ["Vault.sol:10"],
        }]
        result = plan(
            graph,
            actors=["a", "b"],
            capability_report={
                "source_analysis": {"available": True},
                "execution_trace": {"available": True},
                "http_crawl": {"available": False},
                "request_replay": {"available": False},
                "surface_inventory": {"available": False},
                "synchronized_requests": {"available": True},
            },
            seed_leads=leads,
        )
        et = next(entry for entry in result["lenses"] if entry["lens"] == "execution-trace")
        self.assertGreaterEqual(et["seed_lead_count"], 1)
        self.assertEqual(et["seed_leads"][0]["bug_class"], "reentrancy")
        self.assertIn(et["status"], {"planned", "blocked"})


class GitRootTests(unittest.TestCase):
    def test_nested_path_is_not_repo_root(self) -> None:
        nested = ROOT / "evals" / "web"
        if nested.is_dir():
            self.assertFalse(is_git_root(nested))

    def test_temp_dir_is_not_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(is_git_root(Path(tmp)))


class AuditOrchestratorTests(unittest.TestCase):
    def test_run_audit_on_fixture_produces_leads_and_bundles(self) -> None:
        fixture = ROOT / "evals" / "evm"
        with tempfile.TemporaryDirectory(prefix="ih-audit-") as tmp:
            code = run_audit(fixture, Path(tmp), local_dev=True, run_slither=False)
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "observations.jsonl").is_file())
            self.assertTrue((Path(tmp) / "money-map.json").is_file())
            self.assertTrue((Path(tmp) / "dispatch.json").is_file())
            self.assertTrue((Path(tmp) / "summary.json").is_file())
            summary = json.loads((Path(tmp) / "summary.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(summary["leads"], 1)
            self.assertGreaterEqual(summary["lenses_planned"], 1)
            bundles = list((Path(tmp) / "bundles").glob("bundle-*.md"))
            self.assertTrue(bundles)


if __name__ == "__main__":
    unittest.main()
