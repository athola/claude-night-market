#!/usr/bin/env python3
"""Check that the files a PR description names are in the diff.

A description that claims changes the diff does not contain merges far
less often (arXiv 2601.04886). This reads the paths a description names
in backticks and sorts them against the files changed since the merge
base with BASE, uncommitted and untracked files included, because a
draft is written before the last commit:

- phantom: has a slash, and neither the diff nor ``git ls-files`` holds
  it. Fails.
- not in diff: tracked but untouched. A warning, because a description
  may name the caller of a fixed function. ``--strict`` fails on it.

A token counts as a file only when its last segment has an extension
with a letter in it, so branches (``feature/rc5``), addresses, versions,
globs, and directories are skipped. Paths match by suffix, because
descriptions name files relative to a crate. A bare name nothing tracks
is an identifier (``Dispatchers.IO``) and is skipped.

Measured on 200 agent MR descriptions from two GitLab projects, against
each repository's full history: 5 named files never existed in git. Two
were untracked docs, and three were a device path, a build artifact,
and an upstream crate. Those three are the false failures to expect.

Usage:
    python3 scripts/description_paths.py --base origin/master desc.md
    gh pr view --json body -q .body | python3 scripts/description_paths.py -
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

_FENCE = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
_TICKED = re.compile(r"`([^`\s]+)`")
_SUFFIX = re.compile(r"(::\w+|:\d+(?::\d+)?)$")
# A last segment shaped like a file name: an extension that holds a letter.
# Branches (feature/rc5), addresses, versions, and directories have none.
_FILE_NAME = re.compile(r"^[\w.-]*\w\.[A-Za-z][A-Za-z0-9]{0,5}$")
_SKIP_PREFIX = ("-", "~", "/", "...")


@dataclass
class Report:
    """Named paths sorted by how they fail the diff."""

    phantom: list[str] = field(default_factory=list)
    untouched: list[str] = field(default_factory=list)


def named_paths(text: str) -> list[str]:
    """Backticked tokens shaped like a file path, outside fenced code."""
    paths: list[str] = []
    for raw in _TICKED.findall(_FENCE.sub("", text)):
        token = _SUFFIX.sub("", raw)
        if "://" in token or "..." in token or token.startswith(_SKIP_PREFIX):
            continue
        if _FILE_NAME.match(token.rsplit("/", 1)[-1]):
            paths.append(token)
    return paths


def _found(path: str, files: list[str]) -> bool:
    return any(f == path or f.endswith("/" + path) for f in files)


def check(text: str, changed: list[str], tracked: list[str]) -> Report:
    """Sort the paths ``text`` names against the changed and tracked files.

    A path is matched by suffix, because descriptions name files relative
    to a crate or package (``event/mod.rs`` for ``swarm/event/mod.rs``).
    """
    report = Report()
    for path in named_paths(text):
        if _found(path, changed):
            continue
        if _found(path, tracked):
            report.untouched.append(path)
        elif "/" in path:
            report.phantom.append(path)
        # A bare name nothing tracks is an identifier such as
        # ``Dispatchers.IO``, so it is neither phantom nor untouched.
    return report


def _git(repo: Path, *args: str) -> list[str]:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.split()


def main(argv: list[str] | None = None) -> int:
    """Exit 1 on a phantom path, or on any path outside the diff with --strict.

    Exit 2 when git fails, so a bad base is not read as a phantom path.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("description", help="description file, or - for stdin")
    parser.add_argument("--base", default="origin/master")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    repo = Path(args.repo)
    if args.description == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.description).read_text(encoding="utf-8")
    try:
        merge_base = _git(repo, "merge-base", args.base, "HEAD")[0]
        # --no-renames lists a moved file under both names.
        changed = _git(repo, "diff", "--name-only", "--no-renames", merge_base)
        changed += _git(repo, "ls-files", "--others", "--exclude-standard")
        tracked = _git(repo, "ls-files")
    except subprocess.CalledProcessError as err:
        print(
            f"git failed against base {args.base}: {err.stderr.strip()}",
            file=sys.stderr,
        )
        return 2
    report = check(text, changed, tracked)
    for path in report.phantom:
        print(f"phantom: {path}")
    for path in report.untouched:
        print(f"not in diff: {path}")
    if report.phantom or (args.strict and report.untouched):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
