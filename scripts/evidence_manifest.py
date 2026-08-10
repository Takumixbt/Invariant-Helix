#!/usr/bin/env python3
"""Build or verify a case-bound evidence manifest with SHA-256 integrity records."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text


REDACTION_STATUSES = {"unreviewed", "redacted", "restricted", "public-safe"}
REQUIRED_ARTIFACT_FIELDS = {
    "artifact_id",
    "relative_path",
    "media_type",
    "size",
    "content_digest",
    "created_at",
    "producer",
    "snapshot_id",
    "redaction_status",
}


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _artifact_id(case_id: str, snapshot_id: str, relative: str, sha256: str) -> str:
    payload = f"{case_id}\0{snapshot_id}\0{relative}\0{sha256}".encode()
    return f"artifact:{hashlib.sha256(payload).hexdigest()[:24]}"


def _files(root: Path, excluded: set[Path] | None = None) -> list[Path]:
    if not root.exists() or not root.is_dir():
        raise ValueError("evidence root must be an existing directory")
    resolved_root = root.resolve()
    excluded = {item.resolve() for item in (excluded or set())}
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"evidence root contains a symbolic link: {path}")
        if not path.is_file() or path.resolve() in excluded:
            continue
        try:
            path.resolve().relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError(f"evidence file escapes the root: {path}") from exc
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix())


def build(
    root: Path,
    *,
    case_id: str,
    snapshot_id: str,
    producer: str,
    redaction_status: str,
    excluded: set[Path] | None = None,
    allow_empty: bool = False,
) -> list[dict[str, Any]]:
    if not all(isinstance(value, str) and value.strip() for value in (case_id, snapshot_id, producer)):
        raise ValueError("case_id, snapshot_id, and producer must be non-empty")
    if redaction_status not in REDACTION_STATUSES:
        raise ValueError(f"redaction_status must be one of: {', '.join(sorted(REDACTION_STATUSES))}")
    paths = _files(root, excluded)
    if not paths and not allow_empty:
        raise ValueError("evidence root contains no files")
    records: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(root).as_posix()
        stat = path.stat()
        sha256 = digest(path)
        records.append(
            {
                "artifact_id": _artifact_id(case_id, snapshot_id, relative, sha256),
                "relative_path": relative,
                "media_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "size": stat.st_size,
                "content_digest": f"sha256:{sha256}",
                "created_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "producer": producer,
                "snapshot_id": snapshot_id,
                "redaction_status": redaction_status,
            }
        )
    return records


def create_manifest(
    root: Path,
    *,
    case_id: str,
    snapshot_id: str,
    producer: str,
    redaction_status: str,
    output: Path,
    allow_empty: bool = False,
) -> dict[str, Any]:
    records = build(
        root,
        case_id=case_id,
        snapshot_id=snapshot_id,
        producer=producer,
        redaction_status=redaction_status,
        excluded={output},
        allow_empty=allow_empty,
    )
    return {
        "schema_version": "1.0",
        "case_id": case_id,
        "snapshot_id": snapshot_id,
        "producer": producer,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": records,
    }


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest must be JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("manifest root must be an object")
    return value


def validate_manifest_structure(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("schema_version", "case_id", "snapshot_id", "producer", "created_at", "artifacts"):
        if field not in manifest:
            errors.append(f"manifest missing {field}")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("manifest artifacts must be an array")
        return errors
    ids: set[str] = set()
    paths: set[str] = set()
    for index, record in enumerate(artifacts):
        prefix = f"artifacts[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = REQUIRED_ARTIFACT_FIELDS - record.keys()
        if missing:
            errors.append(f"{prefix} missing: {', '.join(sorted(missing))}")
        artifact_id = record.get("artifact_id")
        relative = record.get("relative_path")
        if not isinstance(artifact_id, str) or not artifact_id.startswith("artifact:"):
            errors.append(f"{prefix}.artifact_id is invalid")
        elif artifact_id in ids:
            errors.append(f"{prefix}.artifact_id is duplicated")
        ids.add(str(artifact_id))
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            errors.append(f"{prefix}.relative_path is invalid")
        elif relative in paths:
            errors.append(f"{prefix}.relative_path is duplicated")
        paths.add(str(relative))
        if record.get("snapshot_id") != manifest.get("snapshot_id"):
            errors.append(f"{prefix}.snapshot_id does not match the manifest")
        if record.get("redaction_status") not in REDACTION_STATUSES:
            errors.append(f"{prefix}.redaction_status is invalid")
    return errors


def verify(manifest_path: Path, root: Path) -> list[str]:
    manifest = load_manifest(manifest_path)
    errors = validate_manifest_structure(manifest)
    if errors:
        return errors
    resolved_manifest = manifest_path.resolve()
    try:
        manifest_inside_root = resolved_manifest.is_relative_to(root.resolve())
    except AttributeError:  # Python 3.8 compatibility is not required, but keep this safe.
        manifest_inside_root = False
    actual_paths = {
        path.relative_to(root).as_posix(): path
        for path in _files(root, {manifest_path} if manifest_inside_root else set())
    }
    expected_paths = {record["relative_path"] for record in manifest["artifacts"]}
    for missing in sorted(expected_paths - actual_paths.keys()):
        errors.append(f"manifested file is missing: {missing}")
    for untracked in sorted(actual_paths.keys() - expected_paths):
        errors.append(f"evidence file is not manifested: {untracked}")
    for record in manifest["artifacts"]:
        relative = record["relative_path"]
        path = actual_paths.get(relative)
        if path is None:
            continue
        sha256 = digest(path)
        if record.get("content_digest") != f"sha256:{sha256}":
            errors.append(f"digest mismatch: {relative}")
        if record.get("size") != path.stat().st_size:
            errors.append(f"size mismatch: {relative}")
        expected_id = _artifact_id(manifest["case_id"], manifest["snapshot_id"], relative, sha256)
        if record.get("artifact_id") != expected_id:
            errors.append(f"artifact_id mismatch: {relative}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case-id")
    parser.add_argument("--snapshot-id")
    parser.add_argument("--producer")
    parser.add_argument("--redaction-status", choices=sorted(REDACTION_STATUSES), default="unreviewed")
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--verify", type=Path, metavar="MANIFEST")
    args = parser.parse_args(argv)
    try:
        if args.verify:
            errors = verify(args.verify, args.root)
            if errors:
                for error in errors:
                    print(f"manifest error: {error}", file=sys.stderr)
                return 1
            manifest = load_manifest(args.verify)
            print(f"verified {len(manifest['artifacts'])} artifact(s)")
            return 0
        if not args.output:
            raise ValueError("--output is required when building a manifest")
        manifest = create_manifest(
            args.root,
            case_id=args.case_id or "",
            snapshot_id=args.snapshot_id or "",
            producer=args.producer or "",
            redaction_status=args.redaction_status,
            output=args.output,
            allow_empty=args.allow_empty,
        )
        atomic_write_text(args.output, json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"manifest error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(manifest['artifacts'])} artifact(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
