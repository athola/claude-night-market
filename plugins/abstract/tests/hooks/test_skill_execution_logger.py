"""Input-contract tests for the skill_execution_logger PostToolUse hook.

Claude Code delivers hook payloads as JSON on **stdin**, not via
``CLAUDE_TOOL_*`` environment variables. These tests drive the hook the
way the runtime actually does and assert that a real (non-synthetic)
skill invocation produces a telemetry entry carrying the real session id.

Regression guard for the silent no-op that drained the ``[Learning]``
discussion pipeline: the hook read tool data from environment variables
the runtime never sets, so every real invocation exited 0 without
logging anything.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOOK = Path(__file__).resolve().parents[2] / "hooks" / "skill_execution_logger.py"

_LEGACY_ENV = (
    "CLAUDE_TOOL_NAME",
    "CLAUDE_TOOL_INPUT",
    "CLAUDE_TOOL_OUTPUT",
    "CLAUDE_SESSION_ID",
)


def _run(payload: dict, claude_home: Path, extra_env: dict | None = None):
    """Run the hook as a subprocess feeding ``payload`` as JSON on stdin."""
    env = dict(os.environ)
    env["CLAUDE_HOME"] = str(claude_home)
    # Clear legacy env vars so the stdin path is exercised in isolation.
    for key in _LEGACY_ENV:
        env.pop(key, None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


def _entries(claude_home: Path, plugin: str, skill: str) -> list[dict]:
    log_dir = claude_home / "skills" / "logs" / plugin / skill
    files = sorted(log_dir.glob("*.jsonl"))
    out: list[dict] = []
    for f in files:
        out.extend(
            json.loads(line) for line in f.read_text().splitlines() if line.strip()
        )
    return out


def test_logs_real_skill_invocation_from_stdin(tmp_path):
    """A Skill PostToolUse payload on stdin writes a telemetry entry."""
    payload = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Skill",
        "tool_input": {"skill": "superpowers:systematic-debugging"},
        "tool_response": {"success": True},
        "session_id": "11111111-2222-3333-4444-555555555555",
    }
    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr

    entries = _entries(tmp_path, "superpowers", "systematic-debugging")
    assert entries, f"no telemetry written; stderr={result.stderr}"
    assert entries[-1]["skill"] == "superpowers:systematic-debugging"
    # The real session id must survive into the entry (proves it is not
    # treated as a synthetic 'test-session' record by aggregation).
    assert entries[-1]["context"]["session_id"] == payload["session_id"]


def test_non_skill_payload_writes_nothing(tmp_path):
    """A non-Skill tool payload on stdin is ignored."""
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
        "session_id": "deadbeef",
    }
    result = _run(payload, tmp_path)
    assert result.returncode == 0, result.stderr
    assert not list((tmp_path / "skills" / "logs").rglob("*.jsonl"))


# ---------------------------------------------------------------------------
# Duration measurement (issue #671)
#
# The hook fabricated a duration_ms of 0 whenever it could not find the
# matching pre-execution state, and nothing downstream could tell that zero
# from a real sub-millisecond reading. It also paired post to pre by taking
# the newest state file by mtime, which under overlapping invocations of one
# skill claims the wrong start time.
# ---------------------------------------------------------------------------


def _write_state(claude_home: Path, skill_ref: str, started_at, mtime_epoch: float):
    """Write a pre-execution state file with a controlled mtime."""
    state_dir = claude_home / "skills" / "observability"
    state_dir.mkdir(parents=True, exist_ok=True)
    plugin, skill = skill_ref.split(":", 1)
    invocation_id = f"{skill_ref}:{started_at.timestamp()}"
    path = state_dir / f"{invocation_id}.json"
    path.write_text(
        json.dumps(
            {
                "invocation_id": invocation_id,
                "timestamp": started_at.isoformat(),
                "skill": skill_ref,
                "plugin": plugin,
                "skill_name": skill,
                "tool_input": {"skill": skill_ref},
            }
        )
    )
    os.utime(path, (mtime_epoch, mtime_epoch))
    return invocation_id


def _payload(skill_ref: str) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Skill",
        "tool_input": {"skill": skill_ref},
        "tool_response": {"success": True},
        "session_id": "11111111-2222-3333-4444-555555555555",
    }


def test_unmeasured_execution_reports_none_not_zero(tmp_path):
    """With no pre-state, duration_ms is None rather than a fabricated 0.

    A zero is indistinguishable from a real sub-millisecond measurement, so
    it passes every downstream ">= 0" filter and counts as a sample. None
    says "not measured", which is the truth the entry has to carry.
    """
    result = _run(_payload("abstract:skill-auditor"), tmp_path)
    assert result.returncode == 0, result.stderr

    entries = _entries(tmp_path, "abstract", "skill-auditor")
    assert entries, f"no telemetry written; stderr={result.stderr}"
    assert entries[-1]["duration_ms"] is None, (
        f"unmeasured execution reported {entries[-1]['duration_ms']!r}"
    )


def test_ambiguous_pairing_is_unmeasured_not_guessed(tmp_path):
    """Two live states for one skill: report None rather than pick one.

    The state glob keys on skill ref alone and a PostToolUse payload carries
    nothing identifying its invocation, so with two live candidates the hook
    cannot know which start time is its own. Newest-by-mtime yields the start
    of an invocation still running (the source of negative intervals);
    oldest-by-mtime is right only when completions are first-in-first-out.
    Guessing produces a number indistinguishable from a real measurement,
    which is the conflation this issue removes.
    """
    now = datetime.now(timezone.utc)
    skill_ref = "abstract:skill-auditor"
    for offset in (5, 0.5):
        started = now - timedelta(seconds=offset)
        _write_state(tmp_path, skill_ref, started, started.timestamp())

    result = _run(_payload(skill_ref), tmp_path)
    assert result.returncode == 0, result.stderr

    entries = _entries(tmp_path, "abstract", "skill-auditor")
    assert entries, f"no telemetry written; stderr={result.stderr}"
    assert entries[-1]["duration_ms"] is None, (
        f"guessed a pairing among two live states: {entries[-1]['duration_ms']!r}"
    )


def test_orphaned_state_is_purged_so_a_live_pairing_still_resolves(tmp_path):
    """An abandoned state must not make every later completion ambiguous.

    The pre hook writes a state the post hook removes. When a session dies
    between them the file survives forever. Treating it as a live candidate
    would make this skill permanently unmeasurable, so it is purged on sight
    and the real invocation still gets its interval.
    """
    now = datetime.now(timezone.utc)
    skill_ref = "abstract:skill-auditor"
    # Abandoned two hours ago: no execution runs that long here.
    stale = now - timedelta(hours=2)
    _write_state(tmp_path, skill_ref, stale, stale.timestamp())
    # The invocation actually finishing now.
    live = now - timedelta(seconds=3)
    _write_state(tmp_path, skill_ref, live, live.timestamp())

    result = _run(_payload(skill_ref), tmp_path)
    assert result.returncode == 0, result.stderr

    entries = _entries(tmp_path, "abstract", "skill-auditor")
    assert entries, f"no telemetry written; stderr={result.stderr}"
    duration = entries[-1]["duration_ms"]
    assert duration is not None, "orphan blocked a resolvable pairing"
    assert 2000 <= duration <= 10000, (
        f"paired against the orphan instead of the live state: {duration}ms"
    )

    state_dir = tmp_path / "skills" / "observability"
    assert not list(state_dir.glob(f"{skill_ref}:*.json")), (
        "orphan survived the purge and will re-ambiguate the next completion"
    )


def test_future_dated_pre_state_is_unmeasured_not_negative(tmp_path):
    """A start time after the end time yields None, never a negative.

    A backward wall-clock adjustment between the two hooks stores an
    interval no execution could have taken. Reporting it as a measurement
    is worse than reporting nothing: the -2375ms sample on
    attune:mission-orchestrator reached the aggregate report this way.
    """
    now = datetime.now(timezone.utc)
    skill_ref = "abstract:skill-auditor"
    _write_state(tmp_path, skill_ref, now + timedelta(seconds=3), now.timestamp())

    result = _run(_payload(skill_ref), tmp_path)
    assert result.returncode == 0, result.stderr

    entries = _entries(tmp_path, "abstract", "skill-auditor")
    assert entries, f"no telemetry written; stderr={result.stderr}"
    assert entries[-1]["duration_ms"] is None, (
        f"stored an impossible interval: {entries[-1]['duration_ms']!r}"
    )
