"""git pre-commit hook: refuse an agent commit whose index the gauntlet gate never saw.

The PreToolUse gate in precommit_gate.py reads the index before the Bash
command runs. ``git add -A && git commit``, ``git commit -a``,
``--include`` and ``git commit <pathspec>`` change the index inside that
command, so the gate checks one index and git commits another (#1172).
git runs this hook against the index actually being committed (it sets
GIT_INDEX_FILE for the pathspec forms), and the hook compares it with the
one the gate recorded.

It only checks commits made from Claude Code (``CLAUDECODE=1``), in gate
mode, after the gate recorded an index. A human commit from a terminal, or
one made by a script the gate never saw, passes. A record has no expiry:
the gate writes it before the whole command runs, so a long test run ahead
of the ``git add`` would otherwise outlast any window and open the gate.

``--install`` writes ``.git/hooks/pre-commit`` to call this script. An
existing hook is left alone, and the line to add to it is printed.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from precommit_gate import (
    _GATED_INDEX_FILENAME,
    _hash_stage_listing,
    _load_config,
    _precommit_mode,
)

_REFUSAL = (
    "gauntlet: the index changed after the pre-commit gate checked it "
    "(git add in the same command, commit -a, or commit <paths>). Run "
    "git add as a separate command, then git commit on its own, so the "
    "gate sees what is being committed. If nothing changed the index in "
    "this command, the gate's record was left by an earlier commit that "
    "never ran. It is cleared now, so retry the commit."
)


def recheck(repo_root: Path, env: Mapping[str, str]) -> str | None:
    """Return a refusal message, or None when the commit may proceed."""
    if env.get("CLAUDECODE") != "1" or env.get("GAUNTLET_PRECOMMIT_MODE") == "off":
        return None
    gauntlet_dir = repo_root / ".gauntlet"
    if not gauntlet_dir.is_dir():
        return None
    if _precommit_mode(_load_config(gauntlet_dir)) != "gate":
        return None

    record_path = gauntlet_dir / "state" / _GATED_INDEX_FILENAME
    if not record_path.exists():
        return None
    try:
        record = json.loads(record_path.read_text())
    except (json.JSONDecodeError, OSError):
        record = None
    record_path.unlink(missing_ok=True)
    if not isinstance(record, dict):
        return _REFUSAL

    listing = subprocess.run(
        ["git", "ls-files", "--stage"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if record.get("staged_hash") != _hash_stage_listing(listing):
        return _REFUSAL
    return None


def _hook_line(script: Path) -> str:
    """Return the hook line that runs *script*, or warns once it is gone.

    The script sits in the versioned plugin cache, and an update deletes
    the old version. ``|| exit 1`` on a missing file then aborted every
    commit in the repository, a person's included, until the hook was
    edited by hand.
    """
    return (
        f'if [ -f "{script}" ]; then python3 "{script}" || exit 1; '
        f"else printf 'gauntlet: %s is gone. Rerun git_index_recheck.py "
        f'--install\\n\' "{script}" >&2; fi'
    )


_HOOK_LINE = _hook_line(Path(__file__).resolve())


def install(repo_root: Path) -> int:
    """Write the pre-commit hook; 1 when another hook is already there."""
    hooks_dir = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    hook = repo_root / hooks_dir / "pre-commit"
    if hook.exists():
        if _HOOK_LINE in hook.read_text():
            return 0
        print(
            f"gauntlet: {hook} already exists. Add this line to it:\n{_HOOK_LINE}",
            file=sys.stderr,
        )
        return 1
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(f"#!/bin/sh\n{_HOOK_LINE}\n")
    hook.chmod(0o755)
    return 0


def main() -> int:
    """Exit nonzero, which makes git abort the commit, on a refusal."""
    if sys.argv[1:] == ["--install"]:
        return install(Path.cwd())
    refusal = recheck(Path.cwd(), os.environ)
    if refusal is None:
        return 0
    print(refusal, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
