#!/usr/bin/env python3
"""Build deterministic per-lens bundles from a dispatch plan, ready to be hashed.

Each planned lens gets one bundle file combining its profile, the shared rules, and the
auditor SOP (the operator appends the redacted source under review). Running
``ih-evidence`` over the output directory hashes every bundle into the evidence
manifest, so a lens finding's ``bundle_digest`` resolves to the exact input its agent
read. Standard library only; byte-stable output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .security_utils import atomic_write_text
except ImportError:  # direct script execution
    from security_utils import atomic_write_text

LENS_DIR = Path("references/lenses")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return f"<missing: {path}>\n"


def build(plan: dict[str, Any], lens_dir: Path, sources: str = "") -> list[tuple[str, str]]:
    shared = _read(lens_dir / "shared-rules.md")
    sop = _read(lens_dir / "auditor-sop.md")
    bundles: list[tuple[str, str]] = []
    for entry in plan.get("lenses", []):
        if not isinstance(entry, dict) or entry.get("status") != "planned":
            continue
        lens = str(entry.get("lens"))
        profile = _read(lens_dir / f"{lens}.md")
        seeds = entry.get("seed_leads") if isinstance(entry.get("seed_leads"), list) else []
        if seeds:
            seed_lines = [
                "These are *hypothesized* analyzer leads. Prove reachability and impact. "
                "Do not promote to finding without G7 proof and G8 independent falsification.\n"
            ]
            for seed in seeds:
                if not isinstance(seed, dict):
                    continue
                locs = ", ".join(str(x) for x in (seed.get("locators") or [])[:4])
                seed_lines.append(
                    f"- **{seed.get('bug_class') or 'lead'}**: {seed.get('label')} "
                    f"({locs}) id={seed.get('id')}"
                )
            seed_section = "## Pre-seeded leads (hypothesized only)\n\n" + "\n".join(seed_lines) + "\n\n"
        else:
            seed_section = (
                "## Pre-seeded leads (hypothesized only)\n\n"
                "_None attached. Start from the lens attack surfaces and the graph._\n\n"
            )
        content = (
            f"# Lens bundle: {lens}\n\n"
            f"case: {plan.get('case_id')}  snapshot: {plan.get('snapshot_id')}\n"
            f"owner: {entry.get('owner')}  verifier: {entry.get('verifier')}\n\n"
            f"## Auditor SOP\n\n{sop}\n\n## Shared rules\n\n{shared}\n\n"
            f"{seed_section}"
            f"## Lens profile\n\n{profile}\n\n## Source under review\n\n{sources or '<appended by operator>'}\n"
        )
        bundles.append((f"bundle-{lens}.md", content))
    bundles.sort(key=lambda item: item[0])
    return bundles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dispatch", required=True, type=Path)
    parser.add_argument("--lens-dir", type=Path, default=LENS_DIR)
    parser.add_argument("--sources", type=Path, help="optional redacted source bundle to append")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.dispatch.read_text(encoding="utf-8"))
        sources = args.sources.read_text(encoding="utf-8") if args.sources else ""
        bundles = build(plan, args.lens_dir, sources)
        for name, content in bundles:
            atomic_write_text(args.output_dir / name, content)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"bundle build error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {len(bundles)} bundle(s) to {args.output_dir}; hash them with ih-evidence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
