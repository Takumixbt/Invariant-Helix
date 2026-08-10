#!/usr/bin/env python3
"""Print the Invariant Helix banner and a live readiness line.

More than decoration: the banner doubles as a preflight readout, so the first thing an
operator sees is what this installation can actually do right now -- capabilities backed
by a real tool, lenses available, and the standing safety posture. Standard library only.

Colour is emitted only when stdout is a TTY and NO_COLOR is unset, so piped or redirected
output stays clean.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from .check_capabilities import probe
except ImportError:  # direct script execution
    from check_capabilities import probe

ROOT = Path(__file__).resolve().parents[1]

BANNER = r"""
██╗███╗   ██╗██╗   ██╗ █████╗ ██████╗ ██╗ █████╗ ███╗   ██╗████████╗
██║████╗  ██║██║   ██║██╔══██╗██╔══██╗██║██╔══██╗████╗  ██║╚══██╔══╝
██║██╔██╗ ██║██║   ██║███████║██████╔╝██║███████║██╔██╗ ██║   ██║
██║██║╚██╗██║╚██╗ ██╔╝██╔══██║██╔══██╗██║██╔══██║██║╚██╗██║   ██║
██║██║ ╚████║ ╚████╔╝ ██║  ██║██║  ██║██║██║  ██║██║ ╚████║   ██║
╚═╝╚═╝  ╚═══╝  ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝
        ██╗  ██╗███████╗██╗     ██╗██╗  ██╗
        ██║  ██║██╔════╝██║     ██║╚██╗██╔╝
        ███████║█████╗  ██║     ██║ ╚███╔╝
        ██╔══██║██╔══╝  ██║     ██║ ██╔██╗
        ██║  ██║███████╗███████╗██║██╔╝ ██╗
        ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝
"""
TAGLINE = "evidence-gated  ·  graph-driven  ·  fails closed"


def _colour(enabled: bool) -> tuple[str, str, str, str]:
    if not enabled:
        return "", "", "", ""
    return "\033[1;36m", "\033[2m", "\033[1m", "\033[0m"  # cyan-bold, dim, bold, reset


def use_colour(stream: object = None) -> bool:
    stream = stream or sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def readiness() -> tuple[int, int, int]:
    """(capabilities available, capabilities total, lens count)."""
    report = probe()
    available = sum(1 for detail in report.values() if detail["available"])
    lenses = len(list((ROOT / "references/lenses").glob("*.md")))
    # shared-rules, auditor-sop and nemesis-loop are protocol files, not attack lenses.
    lenses = max(lenses - 3, 0)
    return available, len(report), lenses


def render(*, colour: bool = True, quiet: bool = False) -> str:
    accent, dim, bold, reset = _colour(colour)
    lines = [f"{accent}{BANNER.rstrip()}{reset}", f"  {dim}{TAGLINE}{reset}"]
    if not quiet:
        available, total, lenses = readiness()
        status = f"{available}/{total} capabilities"
        lines.append("")
        lines.append(f"  {bold}{status}{reset}  ·  {bold}{lenses}{reset} attack lenses  ·  gates {bold}G0-G9{reset}")
        if available < total:
            lines.append(f"  {dim}run `ih-check-capabilities` to see what each gap blocks{reset}")
        lines.append(f"  {dim}no URL, repo, or RPC endpoint implies authorization{reset}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="banner only, without the readiness line")
    parser.add_argument("--no-color", action="store_true", help="force plain output")
    args = parser.parse_args(argv)
    sys.stdout.write(render(colour=use_colour() and not args.no_color, quiet=args.quiet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
