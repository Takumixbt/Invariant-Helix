#!/usr/bin/env python3
"""X-ray git-security analysis: emit inferred observations from repository history.

Scoped to HEAD only. Surfaces repo shape, security-relevant ("fix"/"bug"/"vuln") commits,
and change hotspots as ``inferred`` observations that feed gate G5. ``git`` is invoked as
a subprocess; standard library only. A non-repository input yields an empty result, not
an error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from .inventory import load_scope
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from inventory import load_scope
    from security_utils import atomic_write_text


SECURITY_TERMS = re.compile(r"\b(fix|bug|vuln|security|exploit|patch|revert|overflow|reentran|audit)\b", re.I)
SLUG = re.compile(r"[^a-z0-9]+")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    return result.stdout if result.returncode == 0 else ""


def is_git_root(root: Path) -> bool:
    """True only when *root itself* is a repository toplevel.

    ``git -C <path> rev-parse --is-inside-work-tree`` walks parents, so a temp
    directory under a checkout would otherwise inherit history from an ancestor.
    That launders git observations onto non-repos (and failed the Windows suite).
    """
    try:
        resolved = root.resolve()
    except OSError:
        return False
    if not resolved.is_dir():
        return False
    inside = git(resolved, "rev-parse", "--is-inside-work-tree").strip().lower()
    if inside != "true":
        return False
    toplevel = git(resolved, "rev-parse", "--show-toplevel").strip()
    if not toplevel:
        return False
    try:
        return Path(toplevel).resolve() == resolved
    except OSError:
        return False


def slug(text: str, prefix: str) -> str:
    return f"{prefix}:{SLUG.sub('-', text.lower()).strip('-')[:100] or 'x'}"[:128]


def analyze(root: Path, case_id: str, snapshot_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
    if not is_git_root(root):
        return []
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip() or "HEAD"
    log = git(root, "log", f"-{limit}", "--pretty=format:%H%x1f%an%x1f%s")
    commits = [line.split("\x1f") for line in log.splitlines() if line.count("\x1f") == 2]
    authors = Counter(author for _, author, _ in commits)
    hotspots = Counter()
    for name in git(root, "log", f"-{limit}", "--name-only", "--pretty=format:").splitlines():
        if name.strip():
            hotspots[name.strip()] += 1
    records: list[dict[str, Any]] = [{
        "id": slug(root.name or "repo", "component"), "case_id": case_id, "snapshot_id": snapshot_id,
        "kind": "component", "label": f"git-history:{root.name or 'repo'}", "status": "inferred",
        "sensitivity": "public",
        "confidence": {"level": "medium", "reason": "git history analysis, HEAD-scoped"},
        "properties": {
            "branch": branch, "commits_analyzed": len(commits), "contributors": len(authors),
            "top_hotspots": [name for name, _ in hotspots.most_common(5)],
        },
        "locators": [f"git:{branch}"], "evidence_refs": [f"git:{branch}:HEAD"],
    }]
    for sha, _author, subject in commits:
        if SECURITY_TERMS.search(subject):
            records.append({
                "id": slug(f"{sha[:12]}-{subject}", "pattern"), "case_id": case_id, "snapshot_id": snapshot_id,
                "kind": "pattern", "label": f"security-commit: {subject[:100]}", "status": "inferred",
                "sensitivity": "public",
                "confidence": {"level": "low", "reason": "commit subject matches a security term; lead only"},
                "properties": {"commit": sha, "subject": subject[:200]},
                "locators": [f"git:commit:{sha}"], "evidence_refs": [f"git:commit:{sha}"],
            })
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args(argv)
    try:
        case = load_scope(args.scope)
        records = analyze(args.root, str(case.get("case_id")), str(case.get("snapshot_id")), limit=args.limit)
        atomic_write_text(args.output, "".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"xray git error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({len(records)} inferred observations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
