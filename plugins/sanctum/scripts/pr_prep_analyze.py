#!/usr/bin/env python3
"""Describe a branch's changes the way the pr-prep skill needs them.

``sanctum.pr_prep.PRPrepAnalyzer`` categorizes files, spots breaking
change markers, checks the quality gates and drafts a description, but
it works on dictionaries nobody was building. This script builds them
from git and prints the analyzer's answers, so the skill's summarize
step starts from facts instead of a fresh reading of the diff.

Usage:
    python3 scripts/pr_prep_analyze.py --base origin/master
    python3 scripts/pr_prep_analyze.py --base main --json
    python3 scripts/pr_prep_analyze.py --reviewer-map .github/reviewers.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# The package sits beside this script; the path insert above is what lets
# a plain `python3 scripts/pr_prep_analyze.py` find it from any cwd.
PRPrepAnalyzer = importlib.import_module("sanctum.pr_prep").PRPrepAnalyzer

_DOC_SUFFIXES = (".md", ".rst", ".txt", ".adoc")
#: insertions, deletions, path
_NUMSTAT_FIELDS = 3


def _git(args: list[str], cwd: Path | None) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return completed.stdout


def classify(path: str) -> str:
    """Name the bucket PRPrepAnalyzer sorts a path into."""
    name = path.rsplit("/", 1)[-1]
    if path.startswith("tests/") or "/tests/" in path or name.startswith("test_"):
        return "test"
    if path.endswith(_DOC_SUFFIXES):
        return "docs"
    return "feature"


def collect(base: str, cwd: Path | None = None) -> dict[str, Any]:
    """Read changed files and commits since ``base`` into analyzer input."""
    files: list[dict[str, Any]] = []
    for line in _git(["diff", "--numstat", f"{base}...HEAD"], cwd).splitlines():
        parts = line.split("\t")
        if len(parts) != _NUMSTAT_FIELDS:
            continue
        insertions, deletions, path = parts
        changes = (int(insertions) if insertions.isdigit() else 0) + (
            int(deletions) if deletions.isdigit() else 0
        )
        files.append({"path": path, "type": classify(path), "changes": changes})

    commits = [
        {"hash": sha, "message": message}
        for sha, message in (
            line.split("\x00", 1)
            for line in _git(
                ["log", "--format=%H%x00%s", f"{base}..HEAD"], cwd
            ).splitlines()
            if "\x00" in line
        )
    ]
    return {"changed_files": files, "commits": commits}


def analyze(
    context: dict[str, Any], reviewer_map: dict[str, list[str]] | None = None
) -> dict[str, Any]:
    """Run every PRPrepAnalyzer check over the collected context."""
    files = context["changed_files"]
    gates = PRPrepAnalyzer.validate_quality_gates(
        context, PRPrepAnalyzer.initialize_quality_gates()
    )
    report: dict[str, Any] = {
        "categories": asdict(PRPrepAnalyzer.categorize_changed_files(files)),
        "breaking": asdict(PRPrepAnalyzer.detect_breaking_changes(context)),
        "quality_gates": gates,
        "merge_strategy": asdict(PRPrepAnalyzer.recommend_merge_strategy(files)),
        "description": PRPrepAnalyzer.generate_pr_description(context),
    }
    if reviewer_map:
        report["reviewers"] = PRPrepAnalyzer.suggest_reviewers(files, reviewer_map)
    return report


def render_markdown(report: dict[str, Any], base: str) -> str:
    """Lay the analysis out as sections the skill can paste from."""
    categories = report["categories"]
    breaking = report["breaking"]
    lines = [f"# PR prep analysis: {base}...HEAD", "", "## File categories", ""]
    for bucket in ("feature", "test", "docs", "other"):
        paths = categories[bucket]
        lines.append(f"- {bucket} ({len(paths)}): {', '.join(paths) or 'none'}")
    lines += [f"- total line changes: {categories['total_changes']}", ""]

    lines += ["## Breaking changes", ""]
    if breaking["has_breaking_changes"]:
        lines += [
            f"- commit {sha[:7]} carries a `!` marker"
            for sha in breaking["breaking_commits"]
        ]
        lines += [f"- {path} is marked breaking" for path in breaking["affected_apis"]]
    else:
        lines.append("- none detected (no `!` in commit subjects)")
    lines.append("")

    lines += ["## Quality gates", ""]
    lines += [
        f"- {gate}: {'pass' if passed else 'FAIL'}"
        for gate, passed in report["quality_gates"].items()
    ]
    lines.append("")

    strategy = report["merge_strategy"]
    lines += [
        "## Merge strategy",
        "",
        f"- {strategy['strategy']}: {strategy['reasoning']}",
        "",
    ]
    if "reviewers" in report:
        lines += ["## Suggested reviewers", ""]
        lines += [f"- {name}" for name in report["reviewers"]] or ["- none matched"]
        lines.append("")
    lines += ["## Description scaffold", "", report["description"].rstrip(), ""]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Print the analysis for ``--base...HEAD``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/master", help="Ref the PR targets")
    parser.add_argument("--json", action="store_true", help="Emit JSON, not markdown")
    parser.add_argument("--cwd", type=Path, default=None, help="Repository to read")
    parser.add_argument(
        "--reviewer-map",
        type=Path,
        default=None,
        help="JSON mapping path prefixes to reviewer lists",
    )
    args = parser.parse_args(argv)

    reviewer_map = None
    if args.reviewer_map is not None:
        reviewer_map = json.loads(args.reviewer_map.read_text())

    try:
        context = collect(args.base, args.cwd)
    except subprocess.CalledProcessError as exc:
        print(f"git failed: {exc.stderr.strip()}", file=sys.stderr)
        return 1

    report = analyze(context, reviewer_map)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report, args.base), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
