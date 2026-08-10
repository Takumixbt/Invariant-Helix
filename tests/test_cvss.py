from __future__ import annotations

import unittest

from scripts.cvss import base_score, severity_band


class CvssTests(unittest.TestCase):
    def test_scope_changed_full_impact_is_ten(self) -> None:
        result = base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
        self.assertEqual(result["base_score"], 10.0)
        self.assertEqual(result["severity_band"], "Critical")
        self.assertEqual(result["ih_severity"], "critical")

    def test_scope_unchanged_full_impact_is_9_8(self) -> None:
        # The canonical CVSS 3.1 reference score for this vector.
        result = base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")
        self.assertEqual(result["base_score"], 9.8)

    def test_low_vector_bands_low(self) -> None:
        result = base_score("CVSS:3.1/AV:N/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N")
        self.assertEqual(result["base_score"], 2.0)
        self.assertEqual(result["ih_severity"], "low")

    def test_zero_impact_is_none_band(self) -> None:
        result = base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
        self.assertEqual(result["base_score"], 0.0)
        self.assertEqual(result["ih_severity"], "informational")

    def test_missing_metric_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            base_score("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H")

    def test_bad_prefix_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            base_score("CVSS:3.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")

    def test_scope_dependent_pr_value_is_validated(self) -> None:
        # PR:H is valid; the numeric weight differs by scope but both parse.
        self.assertEqual(base_score("CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:C/C:H/I:H/A:H")["metrics"]["PR"], "H")

    def test_severity_band_boundaries(self) -> None:
        self.assertEqual(severity_band(0.0), "None")
        self.assertEqual(severity_band(3.9), "Low")
        self.assertEqual(severity_band(4.0), "Medium")
        self.assertEqual(severity_band(7.0), "High")
        self.assertEqual(severity_band(9.0), "Critical")


if __name__ == "__main__":
    unittest.main()
