"""Tests for the research-queue hook.

Feature: Research sessions reach the corpus queue
  knowledge-intake documents this queue as live, so it must exist.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

HOOK = Path(__file__).resolve().parent.parent.parent / "hooks" / "research_queue.py"


def _run(payload: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(cwd),
        check=False,
    )


def test_hook_exists() -> None:
    """Scenario: the spec has an implementation."""
    assert HOOK.exists(), f"missing {HOOK}"


def test_hook_is_registered() -> None:
    """Scenario: an unregistered hook never fires."""
    hooks = (HOOK.parent / "hooks.json").read_text()
    assert "research_queue.py" in hooks


def test_below_threshold_writes_nothing(tmp_path: Path) -> None:
    """Scenario: two searches is not a research session."""
    result = _run({"hook_event_name": "SessionEnd", "web_search_count": 2}, tmp_path)
    assert result.returncode == 0
    assert not (tmp_path / "docs" / "knowledge-corpus" / "queue").exists()


def test_research_session_creates_queue_entry(tmp_path: Path) -> None:
    """Scenario: enough searches plus a research cue creates one entry."""
    result = _run(
        {
            "hook_event_name": "SessionEnd",
            "web_search_count": 5,
            "session_id": "abc123",
            "prompt": "deep dive research into agent memory decay",
        },
        tmp_path,
    )
    assert result.returncode == 0
    entries = list((tmp_path / "docs" / "knowledge-corpus" / "queue").glob("*.yaml"))
    assert len(entries) == 1
    assert "status: pending_review" in entries[0].read_text()


def test_duplicate_session_is_not_queued_twice(tmp_path: Path) -> None:
    """Scenario: re-firing does not duplicate the entry."""
    payload = {
        "hook_event_name": "SessionEnd",
        "web_search_count": 5,
        "session_id": "dup1",
        "prompt": "research agent memory",
    }
    _run(payload, tmp_path)
    _run(payload, tmp_path)
    entries = list((tmp_path / "docs" / "knowledge-corpus" / "queue").glob("*.yaml"))
    assert len(entries) == 1


def test_disabled_by_environment(tmp_path: Path) -> None:
    """Scenario: the documented opt-out actually opts out."""
    import os

    env = {**os.environ, "MEMORY_PALACE_AUTO_QUEUE": "false"}
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(
            {
                "hook_event_name": "SessionEnd",
                "web_search_count": 9,
                "prompt": "research",
            }
        ),
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
        env=env,
        check=False,
    )
    assert result.returncode == 0
    assert not (tmp_path / "docs" / "knowledge-corpus" / "queue").exists()


def test_malformed_stdin_does_not_crash(tmp_path: Path) -> None:
    """Scenario: a hook must never break session teardown."""
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input="}{",
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
        check=False,
    )
    assert result.returncode == 0


def _entry_path(cwd: Path) -> Path:
    """Return the single queue entry the hook wrote, asserting exactly one."""
    written = list((cwd / "docs" / "knowledge-corpus" / "queue").glob("*.yaml"))
    assert written, "hook wrote no queue entry"
    return written[0]


def _entry_text(cwd: Path) -> str:
    """Return the single queue entry the hook wrote, as raw text."""
    return _entry_path(cwd).read_text(encoding="utf-8")


def test_quoted_phrase_in_prompt_keeps_frontmatter_parseable(tmp_path: Path) -> None:
    """Scenario: a quoted phrase must not break the entry it names.

    Interpolating an unescaped value into a YAML double-quoted scalar is
    how 2544 staging captures ended up with frontmatter no parser reads.
    """
    _run(
        {
            "prompt": 'research "mtime staleness" detection',
            "web_search_count": 5,
            "session_id": "abc12345",
        },
        tmp_path,
    )
    frontmatter = _entry_text(tmp_path).split("---")[1]

    assert yaml.safe_load(frontmatter)["status"] == "pending_review"


def test_credential_in_prompt_is_redacted_everywhere_it_is_written(
    tmp_path: Path,
) -> None:
    """Scenario: redaction covers the topic and heading, not just the body.

    The entry outlives the session, so a credential reaching any of the
    three write sites is a credential on disk.
    """
    _run(
        {
            "prompt": "research sk-ABCDEFGHIJKLMNOP1234 rotation",
            "web_search_count": 5,
            "session_id": "abc12345",
        },
        tmp_path,
    )

    assert "sk-ABCDEFGHIJKLMNOP1234" not in _entry_text(tmp_path)
    # The topic also becomes the filename. Redaction that runs after
    # slugification would leave the credential in the directory listing.
    assert "abcdefghijklmnop1234" not in _entry_path(tmp_path).name.lower()
