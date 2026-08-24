#!/usr/bin/env python3
"""Ratchet the prose lines that run past the 80-column wrap rule.

``.claude/rules/markdown-formatting.md`` requires prose to wrap at 80
characters and says the rule covers all documentation in the codebase.
Issue #681 recorded that nothing enforced it: the only markdown hook in
``.pre-commit-config.yaml`` was ``check-markdown-links``, which validates
link targets and says nothing about line length.

This is a ratchet rather than a gate because the backlog is real and
reformatting it wholesale would bury a diff. The count may fall and may
hold. It may not rise.

Most of the work here is staying quiet. The rule names its own
exemptions, and a checker that counted every long line would report
thousands of findings against tables and code blocks the rule already
excuses. A check that noisy stops being run, which is the state issue
#681 was filed about.

It is deterministic, read-only, and idempotent.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_FILE = REPO_ROOT / "scripts" / "prose_wrap_baseline.json"

#: The column the rule sets. A line of exactly this length is compliant.
LIMIT = 80

#: How far the baseline may sit above the real count before the test that
#: guards it complains. Zero would turn every incidental rewrap into a
#: required baseline edit; a small allowance absorbs that without letting
#: the number drift into permission nobody granted.
SLACK = 25

#: Filenames the slop rule's anti-goals put out of reach. Historical and
#: generated documents are not rewrapped, so counting them would pin the
#: baseline to a number no one is allowed to lower.
_EXCLUDED_NAMES = frozenset({"CHANGELOG.md"})

_FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")
_LINK_DEFINITION_RE = re.compile(r"^\s*\[[^\]]+\]:\s")
_URL_RE = re.compile(r"https?://|www\.")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(")


def _is_exempt(line: str) -> bool:
    """Return True when the rule excuses this line from wrapping.

    Every branch traces to a clause in
    ``.claude/rules/markdown-formatting.md``: it exempts tables, code
    blocks, headings, frontmatter, HTML, link definitions and image
    references, and forbids breaking inside a URL. A line carrying a URL
    therefore cannot always be brought under the limit, so counting it
    would report a finding with no available repair.
    """
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("|"):  # table row
        return True
    if stripped.startswith("#"):  # ATX heading
        return True
    if line.startswith("    "):  # indented code, and list continuations
        return True
    if stripped.startswith("<"):  # HTML block
        return True
    if _LINK_DEFINITION_RE.match(line):
        return True
    if _IMAGE_RE.search(line):
        return True
    return bool(_URL_RE.search(line))


def overlong_prose_lines(text: str) -> list[int]:
    """Return the 1-based numbers of prose lines longer than ``LIMIT``.

    Fenced blocks are skipped wholesale, and so is YAML frontmatter, but
    only when the document opens with it. A ``---`` further down is a
    thematic break; reading it as a fence opener would silence every
    prose line below the first horizontal rule in the file.
    """
    lines = text.splitlines()
    findings: list[int] = []
    in_fence = False
    start = 0

    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                start = index + 1
                break

    for offset, line in enumerate(lines[start:], start=start):
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if len(line) > LIMIT and not _is_exempt(line):
            findings.append(offset + 1)
    return findings


def is_governed(relative: Path) -> bool:
    """Return True when a repo-relative markdown path is ours to judge.

    Vendored and build-created trees arrive under a dot-directory, the
    same rule ``check_skill_exit_criteria_drift.py`` settled on after
    ``.venv`` and then ``.uv-cache`` each carried foreign documents into
    a tightened gate. The path is taken relative to the repository root
    so a checkout living under a hidden directory does not empty the
    whole surface.
    """
    if relative.name in _EXCLUDED_NAMES:
        return False
    if "node_modules" in relative.parts:
        return False
    return not any(
        part.startswith(".") and part not in {".claude", ".github"}
        for part in relative.parts
    )


def iter_markdown_files() -> list[Path]:
    """Every tracked markdown file the wrap rule governs.

    Enumeration goes through ``git ls-files`` rather than ``rglob``
    because a ratchet that walks the filesystem counts whatever happens
    to be on the machine running it. This repository gitignores
    ``clawhub/`` (generated plugin exports), ``reviews/`` (review
    artifacts) and the memory-palace web captures, which between them
    carried several hundred findings on the machine this guard was
    written on and none at all in a fresh checkout. A gate whose
    threshold moves with local state fires on work nobody committed.
    """
    listed = subprocess.run(  # noqa: S603 - fixed argv, no shell, repo-local path
        ["git", "-C", str(REPO_ROOT), "ls-files", "-z", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(
        REPO_ROOT / name
        for name in listed.stdout.split("\0")
        if name and is_governed(Path(name))
    )


def count_overlong(files: list[Path]) -> int:
    """Total overlong prose lines across ``files``.

    Only a missing file is absorbed. ``git ls-files`` lists tracked
    paths, so one deleted from the working tree is listed and is not
    there; its prose really is gone and zero is the honest count.

    Anything else propagates. A ratchet subtracts every skipped file from
    its own total, so a document that is present and cannot be read has
    an unknown count that silently reads as zero, and one of those can
    absorb a genuine rise somewhere else while the gate reports a pass.
    Discussions #530 and #531 recorded that shape twice already. A denied
    file or one that is not UTF-8 is an anomaly worth stopping for, not a
    number to guess at.
    """
    total = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue
        total += len(overlong_prose_lines(text))
    return total


def evaluate_drift(current: int, baseline: int) -> tuple[bool, str]:
    """Compare the finding count against the baseline.

    Returns ``(ok, message)``. Only a rise fails. A drop passes and asks
    for the baseline to be lowered, because a baseline left above the
    real count is permission nobody meant to grant.
    """
    if current > baseline:
        return False, (
            f"overlong prose lines rose to {current} (baseline {baseline}). "
            f"Wrap the new prose at {LIMIT} columns "
            f"(see .claude/rules/markdown-formatting.md)."
        )
    if current < baseline:
        return True, (
            f"overlong prose lines dropped to {current} (baseline "
            f"{baseline}). Lower max_overlong_prose_lines in "
            f"{BASELINE_FILE.name} to lock the win."
        )
    return True, f"overlong prose lines steady at {current} (baseline {baseline})."


def load_baseline() -> int:
    """Read the committed allowance, defaulting to zero when unreadable."""
    try:
        data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        return int(data.get("max_overlong_prose_lines", 0))
    except (OSError, ValueError):
        return 0


def main() -> int:
    """Run the ratchet; exit non-zero when the count rose."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="report the count and always exit 0, for sizing the backlog",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        help="also list the N worst files, for deciding what to wrap next",
    )
    args = parser.parse_args()

    files = iter_markdown_files()
    current = count_overlong(files)
    ok, message = evaluate_drift(current, load_baseline())
    print(f"[prose-wrap-drift] {message}")

    if args.top:
        ranked = sorted(
            (
                (len(overlong_prose_lines(p.read_text(encoding="utf-8"))), p)
                for p in files
            ),
            reverse=True,
        )
        for count, path in ranked[: args.top]:
            if count:
                print(f"  {count:5d}  {path.relative_to(REPO_ROOT)}")

    return 0 if ok or args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
