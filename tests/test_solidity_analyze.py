from __future__ import annotations

import unittest
from pathlib import Path

from scripts.solidity_analyze import analyze_source, analyze_tree, function_bodies, strip_comments

ROOT = Path(__file__).resolve().parents[1]
VULN = ROOT / "evals/evm/src/VulnerableVault.sol"


def _classes(leads: list[dict]) -> set[str]:
    return {str(lead["properties"].get("bug_class")) for lead in leads}


def _for(leads: list[dict], bug_class: str) -> list[dict]:
    return [lead for lead in leads if lead["properties"].get("bug_class") == bug_class]


class DetectionRateTests(unittest.TestCase):
    """The fixture contains six deliberately planted bugs. This asserts the analyzer
    finds every one of them -- it is the measured detection rate, not a claim."""

    @classmethod
    def setUpClass(cls) -> None:
        source = VULN.read_text(encoding="utf-8")
        cls.facts, cls.leads = analyze_source(source, "VulnerableVault.sol")

    def test_finds_all_six_planted_bugs(self) -> None:
        expected = {
            "unprotected-initializer",     # BUG 1
            "reentrancy",                  # BUG 2
            "missing-access-control",      # BUG 3
            "tx-origin-auth",              # BUG 4
            "precision-loss",              # BUG 5
            "unbounded-loop",              # BUG 6
        }
        missing = expected - _classes(self.leads)
        self.assertEqual(missing, set(), f"analyzer missed planted bugs: {sorted(missing)}")

    def test_reentrancy_points_at_withdraw(self) -> None:
        hits = _for(self.leads, "reentrancy")
        self.assertTrue(hits)
        self.assertEqual(hits[0]["properties"]["function"], "withdraw")
        self.assertIn("balances", hits[0]["properties"]["state_written_after_call"])

    def test_tx_origin_points_at_emergency_drain(self) -> None:
        self.assertEqual(_for(self.leads, "tx-origin-auth")[0]["properties"]["function"], "emergencyDrain")

    def test_unbounded_loop_names_the_growable_array(self) -> None:
        hit = _for(self.leads, "unbounded-loop")[0]["properties"]
        self.assertEqual(hit["function"], "payoutAll")
        self.assertEqual(hit["array"], "depositors")

    def test_precision_loss_points_at_fee(self) -> None:
        self.assertEqual(_for(self.leads, "precision-loss")[0]["properties"]["function"], "feeFor")

    def test_missing_access_control_flags_set_treasury(self) -> None:
        functions = {lead["properties"]["function"] for lead in _for(self.leads, "missing-access-control")}
        self.assertIn("setTreasury", functions)


class PrecisionTests(unittest.TestCase):
    def test_interface_declaration_does_not_capture_a_later_body(self) -> None:
        # A ';'-terminated signature must not latch onto the next contract's brace.
        source = """
        interface IToken { function transfer(address to, uint256 v) external returns (bool); }
        contract C { uint256 public x; function f() external { x = 1; } }
        """
        names = {fn["name"] for fn in function_bodies(source)}
        self.assertIn("f", names)
        self.assertNotIn("transfer", names)

    def test_self_scoped_writes_are_not_access_control_leads(self) -> None:
        # A deposit writing only mapping[msg.sender] is permissionless by design.
        source = """
        contract C {
            mapping(address => uint256) public balances;
            function deposit() external payable { balances[msg.sender] += msg.value; }
        }
        """
        _, leads = analyze_source(source, "C.sol")
        self.assertEqual(_for(leads, "missing-access-control"), [])

    def test_guarded_function_is_not_flagged(self) -> None:
        source = """
        contract C {
            address public owner; uint256 public v;
            function setV(uint256 n) external { require(msg.sender == owner, "no"); v = n; }
        }
        """
        _, leads = analyze_source(source, "C.sol")
        self.assertEqual(_for(leads, "missing-access-control"), [])

    def test_modifier_protected_function_is_not_flagged(self) -> None:
        source = """
        contract C {
            uint256 public v;
            function setV(uint256 n) external onlyOwner { v = n; }
        }
        """
        _, leads = analyze_source(source, "C.sol")
        self.assertEqual(_for(leads, "missing-access-control"), [])

    def test_cei_compliant_withdraw_is_not_flagged_as_reentrant(self) -> None:
        source = """
        contract C {
            mapping(address => uint256) public balances;
            function withdraw(uint256 a) external {
                balances[msg.sender] -= a;
                (bool ok, ) = msg.sender.call{value: a}("");
                require(ok, "fail");
            }
        }
        """
        _, leads = analyze_source(source, "C.sol")
        self.assertEqual(_for(leads, "reentrancy"), [])

    def test_comments_are_blanked_but_line_numbers_preserved(self) -> None:
        source = "a\n/* multi\nline */\nb\n"
        self.assertEqual(strip_comments(source).count("\n"), source.count("\n"))

    def test_commented_out_bug_is_not_detected(self) -> None:
        source = """
        contract C {
            address public owner;
            // function evil() external { owner = msg.sender; }
        }
        """
        _, leads = analyze_source(source, "C.sol")
        self.assertEqual(leads, [])


class OutputContractTests(unittest.TestCase):
    def test_every_lead_is_a_hypothesis_never_a_finding(self) -> None:
        _, leads = analyze_tree(ROOT / "evals/evm", "c", "s")
        for lead in leads:
            self.assertEqual(lead["status"], "hypothesized")
            self.assertEqual(lead["kind"], "hypothesis")
            self.assertEqual(lead["confidence"]["level"], "low")
            self.assertIn("unproven", lead["confidence"]["reason"])

    def test_leads_route_to_a_named_lens(self) -> None:
        _, leads = analyze_tree(ROOT / "evals/evm", "c", "s")
        lens_dir = ROOT / "references/lenses"
        for lead in leads:
            lens = lead["properties"].get("lens")
            self.assertTrue((lens_dir / f"{lens}.md").is_file(), f"lead routes to unknown lens {lens!r}")

    def test_facts_carry_resolvable_locators(self) -> None:
        facts, _ = analyze_tree(ROOT / "evals/evm", "c", "s")
        self.assertTrue(facts)
        for fact in facts:
            self.assertTrue(fact["locators"])
            self.assertRegex(fact["locators"][0], r".+:\d+$")


if __name__ == "__main__":
    unittest.main()
