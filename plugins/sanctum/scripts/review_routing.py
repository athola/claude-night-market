#!/usr/bin/env python3
"""Suggest reviewers for the parts of a change outside its author's lane.

A pull request is the human review of code entering main. Most of it
needs no routing: the author knows the code and any teammate can read
it. The part that does is a change in a directory the author has not
worked in while others have, which is where Ship/Show/Ask says to ask
for eyes. This reads the history of each touched directory up to the
base and names the people who work there.

CODEOWNERS rules take precedence, because GitHub already requests those
reviewers. Names come from ``%aN``, which honors ``.mailmap``, and an
email address is never printed: the output goes into a PR description.

Exit 0 with the report, or 2 when git fails, naming the base.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_WINDOW_DAYS = 180
DEFAULT_DEPTH = 2
MAX_REVIEWERS = 2
CODEOWNERS_LOCATIONS = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")


@dataclass
class Lane:
    """One touched directory and who should look at it."""

    directory: str
    outside: bool
    reviewers: list[str] = field(default_factory=list)
    owners: list[str] = field(default_factory=list)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def parse_codeowners(text: str) -> list[tuple[str, list[str]]]:
    """Read CODEOWNERS rules in file order.

    A pattern with no owners is kept: as the last match it clears the
    owners an earlier rule assigned, which is how GitHub reads it.
    """
    rules: list[tuple[str, list[str]]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        pattern, *owners = line.split()
        rules.append((pattern, owners))
    return rules


def _matches(pattern: str, path: str) -> bool:
    anchored = pattern.startswith("/")
    body = pattern.lstrip("/")
    if body.endswith("/"):
        if anchored:
            return path.startswith(body)
        return path.startswith(body) or f"/{body}" in f"/{path}"
    parts = path.split("/")
    if anchored:
        return fnmatch.fnmatchcase(path, body) or path.startswith(f"{body}/")
    # Unanchored: the pattern may name a file or a directory at any depth.
    for start in range(len(parts)):
        for end in range(start + 1, len(parts) + 1):
            if fnmatch.fnmatchcase("/".join(parts[start:end]), body):
                return True
    return False


def owners_for(path: str, rules: list[tuple[str, list[str]]]) -> list[str]:
    """Owners of ``path``. The last matching rule wins."""
    owners: list[str] = []
    for pattern, rule_owners in rules:
        if _matches(pattern, path):
            owners = rule_owners
    return owners


def _read_codeowners(repo: Path) -> list[tuple[str, list[str]]]:
    for location in CODEOWNERS_LOCATIONS:
        candidate = repo / location
        if candidate.is_file():
            return parse_codeowners(candidate.read_text(encoding="utf-8"))
    return []


def _directory(path: str, depth: int) -> str:
    parts = path.split("/")[:-1]
    return "/".join(parts[:depth]) if parts else "."


def lanes(
    repo: Path,
    base: str,
    head: str = "HEAD",
    window_days: int = DEFAULT_WINDOW_DAYS,
    depth: int = DEFAULT_DEPTH,
) -> list[Lane]:
    """One Lane per directory the change touches, in path order.

    History is read up to ``base``, so commits in the change itself
    never put their author inside a lane.
    """
    authors = set(_git(repo, "log", "--format=%aN", f"{base}..{head}").split("\n"))
    authors.discard("")
    files = [
        f
        for f in _git(repo, "diff", "--name-only", f"{base}...{head}").split("\n")
        if f
    ]
    rules = _read_codeowners(repo)

    by_directory: dict[str, list[str]] = {}
    for path in sorted(files):
        by_directory.setdefault(_directory(path, depth), []).append(path)

    result: list[Lane] = []
    for directory, paths in by_directory.items():
        owners: list[str] = []
        for path in paths:
            for owner in owners_for(path, rules):
                if owner not in owners:
                    owners.append(owner)
        history = _git(
            repo,
            "log",
            "--format=%aN",
            f"--since={window_days} days ago",
            base,
            "--",
            directory,
        )
        counts = Counter(name for name in history.split("\n") if name)
        author_commits = sum(counts[name] for name in authors)
        others = sorted(
            ((name, n) for name, n in counts.items() if name not in authors),
            key=lambda item: (-item[1], item[0]),
        )
        outside = author_commits == 0 and bool(others)
        reviewers = (
            [name for name, _ in others[:MAX_REVIEWERS]]
            if outside and not owners
            else []
        )
        result.append(Lane(directory, outside, reviewers, owners))
    return result


def _default_base(repo: Path) -> str:
    return _git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD").strip()


def _report(found: list[Lane]) -> str:
    lines = []
    for lane in found:
        if lane.owners:
            lines.append(
                f"- `{lane.directory}`: CODEOWNERS requests {', '.join(lane.owners)}."
            )
        elif lane.outside:
            lines.append(
                f"- `{lane.directory}`: outside the author's lane. "
                f"Ask {' or '.join(lane.reviewers)}."
            )
    if not lines:
        return "All touched directories are inside the author's lanes. No extra reviewer needed."
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Print reviewer routing for the change between --base and --head."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", default=".", help="repository root")
    parser.add_argument("--base", help="base ref; defaults to origin's HEAD branch")
    parser.add_argument("--head", default="HEAD", help="head ref (default HEAD)")
    parser.add_argument(
        "--window-days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help="history window that counts as working in a directory",
    )
    parser.add_argument(
        "--depth", type=int, default=DEFAULT_DEPTH, help="path segments per lane"
    )
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    repo = Path(args.repo)
    base = args.base
    try:
        if base is None:
            base = _default_base(repo)
        found = lanes(repo, base, args.head, args.window_days, args.depth)
    except subprocess.CalledProcessError as err:
        print(f"git failed against base {base}: {err.stderr.strip()}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([asdict(lane) for lane in found], indent=2))
    else:
        print(_report(found))
    return 0


if __name__ == "__main__":
    sys.exit(main())
