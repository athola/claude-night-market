#!/usr/bin/env python3
"""Pre-commit hook: block new per-file-ignores without human approval.

Compares [tool.ruff.lint.per-file-ignores] in staged pyproject.toml
files against the committed version. If new rules were added, the
commit is blocked.

Override with: ALLOW_NEW_IGNORES=1 git commit

Exit codes:
    0 - no new ignores found (or override active)
    1 - new ignores detected (commit blocked)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    tomllib = None


def _get_per_file_ignores(toml_text: str) -> dict[str, list[str]]:
    """Extract per-file-ignores from a TOML string."""
    try:
        data = tomllib.loads(toml_text)
    except Exception:
        return {}
    pfi = (
        data.get("tool", {}).get("ruff", {}).get("lint", {}).get("per-file-ignores", {})
    )
    if not isinstance(pfi, dict):
        return {}
    return {k: sorted(v) if isinstance(v, list) else [] for k, v in pfi.items()}


def diff_per_file_ignores(old_text: str, new_text: str) -> dict[str, list[str]]:
    """Return newly added rules per file pattern.

    Keys are glob patterns, values are lists of rule codes
    that appear in new_text but not in old_text.
    """
    old = _get_per_file_ignores(old_text)
    new = _get_per_file_ignores(new_text)

    added: dict[str, list[str]] = {}
    for pattern, new_rules in new.items():
        old_rules = set(old.get(pattern, []))
        new_only = [r for r in new_rules if r not in old_rules]
        if new_only:
            added[pattern] = new_only
    return added


def _get_committed_content(file_path: Path, repo_root: Path) -> str:
    """Get the HEAD version of a file, or empty string if new."""
    try:
        rel = file_path.resolve().relative_to(repo_root.resolve())
        result = subprocess.run(
            ["git", "show", f"HEAD:{rel}"],
            capture_output=True,
            text=True,
            cwd=repo_root,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
    except (ValueError, FileNotFoundError):
        pass
    return ""


def main(argv: list[str] | None = None, *, repo_root: Path | None = None) -> int:
    """Check staged pyproject.toml files for new per-file-ignores."""
    if os.environ.get("ALLOW_NEW_IGNORES") == "1":
        return 0

    files = argv if argv is not None else sys.argv[1:]
    if repo_root is None:
        repo_root = Path.cwd()

    all_added: dict[str, dict[str, list[str]]] = {}

    for f in files:
        path = Path(f)
        if path.name != "pyproject.toml":
            continue
        try:
            new_text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        old_text = _get_committed_content(path, repo_root)
        added = diff_per_file_ignores(old_text, new_text)
        if added:
            all_added[str(path)] = added

    if all_added:
        print(
            "BLOCKED: new per-file-ignores rules detected.\n"
            "Adding lint suppressions to pyproject.toml requires\n"
            "explicit human approval.\n"
        )
        for filepath, patterns in all_added.items():
            print(f"  {filepath}:")
            for pattern, rules in patterns.items():
                print(f"    {pattern}: +{', '.join(rules)}")
        print(
            "\nTo approve: ALLOW_NEW_IGNORES=1 git commit ...\n"
            "Or fix the underlying lint issues instead."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
