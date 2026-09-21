#!/usr/bin/env python3
"""Tier 1 of the tiered audit: read git history, read no source.

The tiered-audit skill names four signals (churn hotspots, fix-on-fix
commits, large diffs, new-file clusters) and the thresholds that turn
each into an escalation flag live in ``pensive.skills.tiered_audit``.
This script runs the git queries, applies those thresholds, and prints
the flags next to the exact command that produced each one, so the
findings file can cite them as evidence.

Usage:
    python3 scripts/tiered_audit.py --base origin/master
    python3 scripts/tiered_audit.py --base main --json
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# The package sits beside this script; the path insert above is what lets
# a plain `python3 scripts/tiered_audit.py` find it from any cwd.
_checks = importlib.import_module("pensive.skills.tiered_audit")

if TYPE_CHECKING:
    from pensive.skills.tiered_audit import Tier1Results

_BASE_CANDIDATES = ("origin/main", "origin/master", "main", "master")
#: insertions, deletions, path
_NUMSTAT_FIELDS = 3


def _git(args: list[str], cwd: Path | None) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return completed.stdout


def default_base(cwd: Path | None) -> str:
    """Pick the first conventional trunk ref the repository knows."""
    for candidate in _BASE_CANDIDATES:
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", candidate],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode == 0:
            return candidate
    msg = f"no trunk ref found among {', '.join(_BASE_CANDIDATES)}; pass --base"
    raise SystemExit(msg)


def _parse_numstat(raw: str) -> list[tuple[str, str, int, int]]:
    """Fold ``git log --format=%H%x00%s --numstat`` into per-commit totals."""
    stats: list[tuple[str, str, int, int]] = []
    sha = message = ""
    insertions = deletions = 0
    for line in raw.splitlines():
        if "\x00" in line:
            if sha:
                stats.append((sha, message, insertions, deletions))
            sha, message = line.split("\x00", 1)
            insertions = deletions = 0
            continue
        parts = line.split("\t")
        if len(parts) == _NUMSTAT_FIELDS and parts[0].isdigit() and parts[1].isdigit():
            insertions += int(parts[0])
            deletions += int(parts[1])
    if sha:
        stats.append((sha, message, insertions, deletions))
    return stats


def collect(base: str, cwd: Path | None = None) -> tuple[Tier1Results, dict[str, str]]:
    """Run the four git queries and apply the Tier 1 thresholds.

    Returns the flags and, keyed by signal, the command that produced them.
    """
    span = f"{base}..HEAD"
    commands = {
        "churn": ["log", "--format=", "--name-only", span],
        "fix-on-fix": ["log", "--format=%H%x00%s", span],
        "large-diff": ["log", "--format=%H%x00%s", "--numstat", span],
        "new-file-cluster": ["diff", "--name-status", span],
    }
    evidence = {name: "git " + " ".join(args) for name, args in commands.items()}

    file_changes = [
        line for line in _git(commands["churn"], cwd).splitlines() if line.strip()
    ]
    commits = [
        tuple(line.split("\x00", 1))
        for line in _git(commands["fix-on-fix"], cwd).splitlines()
        if "\x00" in line
    ]
    diff_stats = _parse_numstat(_git(commands["large-diff"], cwd))
    new_files = [
        line.split("\t", 1)[1]
        for line in _git(commands["new-file-cluster"], cwd).splitlines()
        if line.startswith("A\t")
    ]

    results = _checks.Tier1Results(
        churn_flags=_checks.check_churn_hotspots(file_changes),
        fix_flags=_checks.check_fix_on_fix([(sha, msg) for sha, msg in commits]),
        large_diff_flags=_checks.check_large_diffs(diff_stats),
        new_cluster_flags=_checks.check_new_file_clusters(new_files),
    )
    return results, evidence


def render_markdown(results: Tier1Results, evidence: dict[str, str], base: str) -> str:
    """Lay the flags out in the sections the findings file uses."""
    sections = (
        ("Churn Hotspots", "churn", results.churn_flags),
        ("Fix-on-Fix Patterns", "fix-on-fix", results.fix_flags),
        ("New File Clusters", "new-file-cluster", results.new_cluster_flags),
        ("Large Diffs", "large-diff", results.large_diff_flags),
    )
    lines = [f"# Tier 1 audit: {base}..HEAD", ""]
    for index, (title, key, flags) in enumerate(sections, start=1):
        lines += [f"## {title}", ""]
        if flags:
            lines += [f"- {flag.area or '(commit)'}: {flag.detail}" for flag in flags]
        else:
            lines.append("- none above threshold")
        lines += ["", f"[E{index}] Command: {evidence[key]}", ""]
    targets = results.escalation_targets()
    lines += ["## Escalation", ""]
    if _checks.should_escalate_to_tier2(results):
        lines.append("Escalate to Tier 2: yes")
        lines += [f"- {target}" for target in targets if target]
    else:
        lines.append("Escalate to Tier 2: no")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Print the Tier 1 flags for ``--base..HEAD``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", help="Ref to diff against (default: the trunk)")
    parser.add_argument("--json", action="store_true", help="Emit JSON, not markdown")
    parser.add_argument("--cwd", type=Path, default=None, help="Repository to audit")
    args = parser.parse_args(argv)

    base = args.base or default_base(args.cwd)
    try:
        results, evidence = collect(base, args.cwd)
    except subprocess.CalledProcessError as exc:
        print(f"git failed: {exc.stderr.strip()}", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "base": base,
            "flags": [asdict(flag) for flag in results.all_flags()],
            "escalation_targets": results.escalation_targets(),
            "escalate": _checks.should_escalate_to_tier2(results),
            "evidence": evidence,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(render_markdown(results, evidence, base), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
