from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.evidence_manifest import build, create_manifest, verify


class EvidenceManifestTests(unittest.TestCase):
    def _manifest(self, root: Path, output: Path) -> dict:
        return create_manifest(
            root,
            case_id="case",
            snapshot_id="snap",
            producer="test",
            redaction_status="public-safe",
            output=output,
        )

    def test_records_include_provenance_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence.txt").write_text("evidence", encoding="utf-8")
            records = build(
                root,
                case_id="case",
                snapshot_id="snap",
                producer="test",
                redaction_status="public-safe",
            )
        self.assertEqual(len(records), 1)
        for field in ("artifact_id", "created_at", "producer", "snapshot_id", "content_digest"):
            self.assertIn(field, records[0])

    def test_missing_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "existing directory"):
                build(
                    Path(directory) / "missing",
                    case_id="case",
                    snapshot_id="snap",
                    producer="test",
                    redaction_status="public-safe",
                )

    def test_empty_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no files"):
                build(
                    Path(directory),
                    case_id="case",
                    snapshot_id="snap",
                    producer="test",
                    redaction_status="public-safe",
                )

    def test_manifest_verification_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "evidence"
            root.mkdir()
            evidence = root / "evidence.txt"
            evidence.write_text("original", encoding="utf-8")
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(json.dumps(self._manifest(root, manifest_path)), encoding="utf-8")
            self.assertEqual(verify(manifest_path, root), [])
            evidence.write_text("tampered", encoding="utf-8")
            self.assertTrue(any("mismatch" in error for error in verify(manifest_path, root)))

    def test_manifest_inside_root_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "evidence.txt").write_text("evidence", encoding="utf-8")
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(self._manifest(root, manifest_path)), encoding="utf-8")
            self.assertEqual(verify(manifest_path, root), [])


if __name__ == "__main__":
    unittest.main()
