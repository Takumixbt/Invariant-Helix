from __future__ import annotations

import unittest
from pathlib import Path

from scripts import banner, self_audit
from scripts.build_lens_bundle import build
from scripts.xray_git import analyze, slug

ROOT = Path(__file__).resolve().parents[1]


class SelfAuditTests(unittest.TestCase):
    """The repository must satisfy the contract it advertises."""

    def test_repository_passes_its_own_audit(self) -> None:
        findings = self_audit.run_all()
        self.assertEqual(
            findings, [], "\n".join(f"[{f['severity']}] {f['check']}: {f['detail']}" for f in findings)
        )

    def test_every_lens_file_is_dispatchable(self) -> None:
        self.assertEqual(self_audit.check_lens_wiring(), [])

    def test_every_lens_triggers_on_real_node_kinds(self) -> None:
        self.assertEqual(self_audit.check_lens_triggers(), [])

    def test_every_command_resolves(self) -> None:
        self.assertEqual(self_audit.check_entry_points(), [])

    def test_capability_vocabulary_is_shared(self) -> None:
        self.assertEqual(self_audit.check_capability_names(), [])

    def test_documented_commands_all_exist(self) -> None:
        self.assertEqual(self_audit.check_docs_claims(), [])

    def test_peer_registry_carries_the_independence_rule(self) -> None:
        self.assertEqual(self_audit.check_peer_registry(), [])

    def test_observations_can_never_claim_verified(self) -> None:
        self.assertEqual(self_audit.check_status_vocabulary(), [])


class SelfAuditFaultInjectionTests(unittest.TestCase):
    """A self-audit that cannot fail is decoration. These prove the checks fire."""

    def test_missing_lens_file_is_caught(self) -> None:
        from scripts import lens_dispatch

        lens_dispatch.LENSES["ghost-lens"] = {
            "domain": "contract", "capability": "source_analysis", "triggers": ["state"],
        }
        try:
            findings = self_audit.check_lens_wiring()
            self.assertTrue(any("ghost-lens" in f["detail"] for f in findings))
        finally:
            del lens_dispatch.LENSES["ghost-lens"]

    def test_unfireable_trigger_is_caught(self) -> None:
        from scripts import lens_dispatch

        lens_dispatch.LENSES["bad-trigger"] = {
            "domain": "contract", "capability": "source_analysis", "triggers": ["not_a_node_kind"],
        }
        try:
            self.assertTrue(any("bad-trigger" in f["detail"] for f in self_audit.check_lens_triggers()))
        finally:
            del lens_dispatch.LENSES["bad-trigger"]

    def test_unprobed_capability_is_caught(self) -> None:
        from scripts import lens_dispatch

        lens_dispatch.LENSES["bad-cap"] = {
            "domain": "contract", "capability": "telepathy", "triggers": ["state"],
        }
        try:
            self.assertTrue(any("telepathy" in f["detail"] for f in self_audit.check_capability_names()))
        finally:
            del lens_dispatch.LENSES["bad-cap"]


class BannerTests(unittest.TestCase):
    def test_banner_names_the_skill(self) -> None:
        text = banner.render(colour=False)
        self.assertIn("█", text)
        self.assertIn("evidence-gated", text)

    def test_readiness_reports_real_counts(self) -> None:
        available, total, lenses = banner.readiness()
        self.assertGreater(total, 0)
        self.assertLessEqual(available, total)
        self.assertGreater(lenses, 10)

    def test_no_ansi_escapes_when_colour_disabled(self) -> None:
        self.assertNotIn("\033", banner.render(colour=False))

    def test_colour_is_suppressed_for_non_tty(self) -> None:
        class NotATty:
            def isatty(self) -> bool:
                return False

        self.assertFalse(banner.use_colour(NotATty()))

    def test_quiet_omits_the_readiness_line(self) -> None:
        self.assertNotIn("capabilities", banner.render(colour=False, quiet=True))

    def test_authorization_warning_is_always_present(self) -> None:
        self.assertIn("implies authorization", banner.render(colour=False))


class BundleBuilderTests(unittest.TestCase):
    def _plan(self, status: str = "planned") -> dict:
        return {
            "case_id": "c", "snapshot_id": "s",
            "lenses": [{"lens": "math-precision", "status": status, "owner": "a", "verifier": "b"}],
        }

    def test_bundle_includes_profile_sop_and_shared_rules(self) -> None:
        bundles = build(self._plan(), ROOT / "references/lenses")
        self.assertEqual(len(bundles), 1)
        name, content = bundles[0]
        self.assertEqual(name, "bundle-math-precision.md")
        for expected in ("Auditor SOP", "Shared rules", "Lens profile", "rounding"):
            self.assertIn(expected, content)

    def test_blocked_lens_gets_no_bundle(self) -> None:
        self.assertEqual(build(self._plan("blocked"), ROOT / "references/lenses"), [])

    def test_bundle_records_owner_and_verifier(self) -> None:
        _, content = build(self._plan(), ROOT / "references/lenses")[0]
        self.assertIn("owner: a", content)
        self.assertIn("verifier: b", content)

    def test_output_is_deterministic(self) -> None:
        first = build(self._plan(), ROOT / "references/lenses")
        second = build(self._plan(), ROOT / "references/lenses")
        self.assertEqual(first, second)

    def test_lens_name_cannot_escape_profile_directory(self) -> None:
        plan = self._plan()
        plan["lenses"][0]["lens"] = "../../../escape"
        with self.assertRaises(ValueError):
            build(plan, ROOT / "references/lenses")


class XrayGitTests(unittest.TestCase):
    def test_analyzes_this_repository(self) -> None:
        records = analyze(ROOT, "c", "s", limit=20)
        self.assertTrue(records)
        self.assertEqual(records[0]["kind"], "component")
        self.assertEqual(records[0]["status"], "inferred")

    def test_non_repository_returns_empty_not_error(self) -> None:
        import tempfile

        # Must not inherit a parent checkout: git walks up; we require toplevel == root.
        with tempfile.TemporaryDirectory(prefix="ih-nongit-") as tmp:
            self.assertEqual(analyze(Path(tmp), "c", "s"), [])
        # Nested path under this repo must also return empty (not parent history).
        nested = ROOT / "evals" / "web"
        if nested.is_dir() and not (nested / ".git").exists():
            self.assertEqual(analyze(nested, "c", "s"), [])

    def test_history_observations_are_never_observed_facts(self) -> None:
        for record in analyze(ROOT, "c", "s", limit=20):
            self.assertEqual(record["status"], "inferred")

    def test_slug_is_bounded_and_safe(self) -> None:
        self.assertTrue(slug("A" * 500, "pattern").startswith("pattern:"))
        self.assertLessEqual(len(slug("A" * 500, "pattern")), 128)


if __name__ == "__main__":
    unittest.main()
