"""SessionStart abbreviates context for the review agents it names.

`agent_type` reaches SessionStart only when a session starts with
`claude --agent <name>`; subagents never fire SessionStart
(code.claude.com/docs/en/hooks). For a plugin agent the value is scoped:
`claude -p --agent pensive:code-reviewer` sent
`"agent_type": "pensive:code-reviewer"` (probed on CLI 2.1.289). The
branch listed bare names, so it never matched the only case it can see.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PLUGIN_ROOT / "hooks" / "session-start.sh"


def _context(tmp_path: Path, payload: dict[str, str], terminator: str = "\n") -> str:
    completed = subprocess.run(
        ["bash", str(SCRIPT)],
        input=json.dumps(payload) + terminator,
        cwd=tmp_path,
        env={
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "PATH": "/usr/bin:/bin",
            "HOME": str(tmp_path),
        },
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize("agent_type", ["pensive:code-reviewer", "code-reviewer"])
def test_review_agent_gets_the_abbreviated_context(
    tmp_path: Path, agent_type: str
) -> None:
    context = _context(tmp_path, {"source": "startup", "agent_type": agent_type})
    assert "abbreviated" in context


def test_other_agents_get_the_full_context(tmp_path: Path) -> None:
    context = _context(
        tmp_path, {"source": "startup", "agent_type": "sanctum:pr-agent"}
    )
    assert "abbreviated" not in context


def test_a_session_without_an_agent_gets_the_full_context(tmp_path: Path) -> None:
    context = _context(tmp_path, {"source": "startup"})
    assert "abbreviated" not in context


def test_agent_type_is_read_without_a_trailing_newline(tmp_path: Path) -> None:
    """`read` returns nonzero on an unterminated line, and the branch was
    skipped with the value already read (shell review S0-6, S2-9).
    """
    payload = {"source": "startup", "agent_type": "pensive:code-reviewer"}
    assert "abbreviated" in _context(tmp_path, payload, terminator="")
