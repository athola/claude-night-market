"""Guards that the test suite never writes into the live observability store.

Discussion #654 surfaced that published skill digests reported 100%
success while the on-disk store held 41.6% failures. The cause was not
the aggregator: pytest itself appended fixture entries to the
developer's real ``~/.claude/skills/logs/``. Every synthetic
``test-session`` entry in that store was written by a test run.

The read-side ``_is_synthetic_session`` filter in
``aggregate_skill_logs.py`` masks the symptom at report time. These
tests close the write side, which is where the contamination happens.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[1] / "hooks"
POST_HOOK = HOOKS_DIR / "skill_execution_logger.py"


def _real_store() -> Path:
    """The store the suite must never touch, resolved without CLAUDE_HOME."""
    return Path.home() / ".claude" / "skills" / "logs"


def _entry_count(store: Path) -> int:
    """Total JSONL lines under a log store, 0 when absent."""
    if not store.is_dir():
        return 0
    return sum(
        1
        for log_file in store.rglob("*.jsonl")
        for line in log_file.read_text().splitlines()
        if line.strip()
    )


def test_log_directory_resolves_outside_the_real_home_store() -> None:
    """The autouse isolation fixture must redirect CLAUDE_HOME."""
    src = str(Path(__file__).resolve().parents[1] / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    utils = importlib.import_module("abstract.utils")

    assert utils.get_log_directory() != _real_store()


def test_post_hook_subprocess_does_not_grow_the_real_store() -> None:
    """Running the logging hook must leave the developer's store untouched.

    This is the revert-failing guard. Without the CLAUDE_HOME isolation
    fixture the hook resolves its log directory from the real home and
    this count increases, so deleting the fixture turns this test red.
    """
    real = _real_store()
    before = _entry_count(real)

    env = {
        **os.environ,
        "CLAUDE_TOOL_NAME": "Skill",
        "CLAUDE_TOOL_INPUT": json.dumps({"skill": "abstract:skill-auditor"}),
        "CLAUDE_TOOL_OUTPUT": "Error: validation failed",
        "CLAUDE_SESSION_ID": "test-session",
    }
    subprocess.run(
        [sys.executable, str(POST_HOOK)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    assert _entry_count(real) == before, (
        f"Hook wrote into the live observability store at {real}. "
        "Tests must set CLAUDE_HOME to a temporary directory."
    )


def test_isolated_store_actually_receives_the_entry() -> None:
    """Isolation must redirect the write, not suppress it.

    Guards against a fixture that satisfies the test above by breaking
    logging altogether.
    """
    claude_home = os.environ.get("CLAUDE_HOME")
    assert claude_home, "CLAUDE_HOME must be set by the isolation fixture"

    env = {
        **os.environ,
        "CLAUDE_TOOL_NAME": "Skill",
        "CLAUDE_TOOL_INPUT": json.dumps({"skill": "abstract:skill-auditor"}),
        "CLAUDE_TOOL_OUTPUT": "ok",
        "CLAUDE_SESSION_ID": "test-session",
    }
    subprocess.run(
        [sys.executable, str(POST_HOOK)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )

    isolated = Path(claude_home) / "skills" / "logs"
    assert _entry_count(isolated) > 0, (
        f"No entry landed in the isolated store at {isolated}"
    )
