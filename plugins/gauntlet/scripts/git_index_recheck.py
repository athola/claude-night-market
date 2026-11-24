"""git pre-commit hook: refuse an agent commit whose index the gauntlet gate never saw.

The PreToolUse gate in precommit_gate.py reads the index before the Bash
command runs. ``git add -A && git commit``, ``git commit -a``,
``--include`` and ``git commit <pathspec>`` change the index inside that
command, so the gate checks one index and git commits another (#1172).
git runs this hook against the index actually being committed (it sets
GIT_INDEX_FILE for the pathspec forms), and the hook compares it with the
one the gate recorded.

It only checks commits made from Claude Code (``CLAUDECODE=1``), in gate
mode, after the gate recorded an index in the last few seconds. A human
commit from a terminal, or one made by a script the gate never saw, passes.

Install by calling it from ``.git/hooks/pre-commit``::

    python3 /path/to/plugins/gauntlet/scripts/git_index_recheck.py || exit 1
"""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks"))

from _gauntlet_config import load_config
from precommit_gate import (
    _GATED_INDEX_FILENAME,
    _aware_time,
    _hash_stage_listing,
    _precommit_mode,
)

# The gate writes its record a moment before git runs this hook. A record
# older than this belongs to a commit that never reached git (nothing to
# commit, a failed earlier command), and must not judge a later one.
RECORD_TTL_SECONDS = 120

_REFUSAL = (
    "gauntlet: the index changed after the pre-commit gate checked it "
    "(git add in the same command, commit -a, or commit <paths>). Run "
    "git add as a separate command, then git commit on its own, so the "
    "gate sees what is being committed."
)


def recheck(repo_root: Path, env: Mapping[str, str]) -> str | None:
    """Return a refusal message, or None when the commit may proceed."""
    if env.get("CLAUDECODE") != "1" or env.get("GAUNTLET_PRECOMMIT_MODE") == "off":
        return None
    gauntlet_dir = repo_root / ".gauntlet"
    if not gauntlet_dir.is_dir():
        return None
    if _precommit_mode(load_config(gauntlet_dir) or {}) != "gate":
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

    recorded_at = _aware_time(record.get("recorded_at"))
    if recorded_at is None:
        return _REFUSAL
    age = datetime.datetime.now(datetime.timezone.utc) - recorded_at
    if age.total_seconds() > RECORD_TTL_SECONDS:
        return None

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


def main() -> int:
    """Exit nonzero, which makes git abort the commit, on a refusal."""
    refusal = recheck(Path.cwd(), os.environ)
    if refusal is None:
        return 0
    print(refusal, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
