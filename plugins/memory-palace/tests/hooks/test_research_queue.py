"""Tests for the research-queue hook.

Feature: Research sessions reach the corpus queue
  knowledge-intake documents this queue as live, so it must exist.

Every payload here is the shape Claude Code actually sends on
SessionEnd: session_id, transcript_path, cwd, prompt_id,
hook_event_name, reason. Earlier revisions of this file fed the hook a
``prompt`` and a ``web_search_count`` that the harness has never sent,
so the suite passed green over a hook that could not qualify a single
session in production.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

HOOK = Path(__file__).resolve().parent.parent.parent / "hooks" / "research_queue.py"
HOOKS_JSON = HOOK.parent / "hooks.json"


def _transcript(
    cwd: Path,
    prompt: str | list,
    searches: int,
    before: tuple = (),
    injected: tuple = (),
) -> Path:
    """Write a transcript JSONL in the shape Claude Code records.

    ``before`` holds user records preceding *prompt*: the caveat block a
    resumed session opens with, a bash-input line, or an earlier prompt
    on another subject. ``injected`` holds the ``isMeta`` records the
    harness writes when a slash command or a skill body expands.
    """
    records: list[dict] = [
        {"type": "user", "message": {"content": earlier}} for earlier in before
    ]
    records += [
        {"type": "user", "isMeta": True, "message": {"content": text}}
        for text in injected
    ]
    records.append({"type": "user", "message": {"content": prompt}})
    records += [
        {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "WebSearch", "input": {"query": "q"}}
                ]
            },
        }
    ] * searches
    path = cwd / "transcript.jsonl"
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8"
    )
    return path


def _payload(transcript: Path | str, session_id: str = "abc12345") -> dict:
    """Build the SessionEnd payload the harness sends."""
    return {
        "session_id": session_id,
        "transcript_path": str(transcript),
        "cwd": str(Path(transcript).parent),
        "prompt_id": "0d1e2f3a",
        "hook_event_name": "SessionEnd",
        "reason": "other",
    }


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
    assert "research_queue.py" in HOOKS_JSON.read_text()


def test_session_end_hook_is_async() -> None:
    """Scenario: a synchronous hook here is cancelled before it runs.

    Claude Code bounds the whole SessionEnd batch by
    ``max(1500ms, max timeout declared in settings-level hooks)``. A
    plugin's own ``timeout`` does not raise that ceiling, and this hook
    costs more than 1500ms to start on macOS system Python, so a
    synchronous registration prints ``Hook cancelled`` on every exit.
    ``async`` detaches it from the deadline.
    """
    entry = json.loads(HOOKS_JSON.read_text())["hooks"]["SessionEnd"][0]["hooks"][0]

    assert entry.get("async") is True, "SessionEnd hook must be async"


def test_below_threshold_writes_nothing(tmp_path: Path) -> None:
    """Scenario: two searches is not a research session."""
    transcript = _transcript(tmp_path, "research agent memory decay", searches=2)

    result = _run(_payload(transcript), tmp_path)

    assert result.returncode == 0
    assert not (tmp_path / "docs" / "knowledge-corpus" / "queue").exists()


def test_searches_without_a_research_cue_write_nothing(tmp_path: Path) -> None:
    """Scenario: searching while fixing a bug is not research."""
    transcript = _transcript(tmp_path, "the login button is broken", searches=9)

    result = _run(_payload(transcript), tmp_path)

    assert result.returncode == 0
    assert not (tmp_path / "docs" / "knowledge-corpus" / "queue").exists()


def test_missing_transcript_writes_nothing(tmp_path: Path) -> None:
    """Scenario: an unreadable transcript leaves no signal to act on."""
    result = _run(_payload(tmp_path / "absent.jsonl"), tmp_path)

    assert result.returncode == 0
    assert not (tmp_path / "docs" / "knowledge-corpus" / "queue").exists()


def test_research_session_creates_queue_entry(tmp_path: Path) -> None:
    """Scenario: enough searches plus a research cue creates one entry."""
    transcript = _transcript(
        tmp_path, "deep dive research into agent memory decay", searches=5
    )

    result = _run(_payload(transcript), tmp_path)

    assert result.returncode == 0
    entry = _entry_path(tmp_path)
    frontmatter = yaml.safe_load(entry.read_text(encoding="utf-8").split("---")[1])
    assert frontmatter["status"] == "pending_review"
    assert frontmatter["web_searches"] == 5


def test_prompt_arriving_as_content_blocks_is_read(tmp_path: Path) -> None:
    """Scenario: a prompt with attachments is a list, not a string."""
    transcript = _transcript(
        tmp_path,
        [{"type": "text", "text": "research memory decay in long sessions"}],
        searches=4,
    )

    _run(_payload(transcript), tmp_path)

    assert "memory decay" in _entry_text(tmp_path)


def test_resumed_session_caveat_is_not_the_topic(tmp_path: Path) -> None:
    """Scenario: a resumed session opens with boilerplate, not a prompt.

    Three of eight real transcripts carrying web searches start with a
    ``local-command-caveat`` block. Reading the first user record as the
    prompt disqualifies every resumed research session.
    """
    transcript = _transcript(
        tmp_path,
        "research memory decay in long sessions",
        searches=5,
        before=(
            "<local-command-caveat>Caveat: The messages below were "
            "generated by the user while the model was unavailable."
            "</local-command-caveat>",
        ),
    )

    _run(_payload(transcript), tmp_path)

    assert "memory decay" in _entry_text(tmp_path)
    assert "caveat" not in _entry_path(tmp_path).name.lower()


def test_bash_input_is_not_the_topic(tmp_path: Path) -> None:
    """Scenario: a shell line typed at the prompt is not the subject."""
    transcript = _transcript(
        tmp_path,
        "research agent memory decay",
        searches=4,
        before=("<bash-input>ls</bash-input>",),
    )

    _run(_payload(transcript), tmp_path)

    assert "bash-input" not in _entry_text(tmp_path)


def test_research_cue_in_a_later_prompt_qualifies(tmp_path: Path) -> None:
    """Scenario: a session that turns to research partway still counts.

    The subject is the prompt that reads as research, not whatever the
    session happened to open with.
    """
    transcript = _transcript(
        tmp_path,
        "research memory decay in long sessions",
        searches=5,
        before=("fix the login button",),
    )

    _run(_payload(transcript), tmp_path)

    assert "memory decay" in _entry_text(tmp_path)
    assert "login button" not in _entry_text(tmp_path)


def test_injected_command_body_is_not_the_topic(tmp_path: Path) -> None:
    """Scenario: a slash-command manual is not a research prompt.

    Command and skill bodies enter the transcript as user records
    carrying ``isMeta: true``, and they are long enough to contain a
    research cue by accident. Four of eight real transcripts qualified
    on a command manual before this record type was excluded.
    """
    transcript = _transcript(
        tmp_path,
        "the login button is broken",
        searches=6,
        injected=(
            "# Update Tests\n\nTo update tests following TDD/BDD "
            "principles, analyze coverage patterns and research gaps.",
        ),
    )

    result = _run(_payload(transcript), tmp_path)

    assert result.returncode == 0
    assert not (tmp_path / "docs" / "knowledge-corpus" / "queue").exists()


def test_duplicate_session_is_not_queued_twice(tmp_path: Path) -> None:
    """Scenario: re-firing does not duplicate the entry."""
    transcript = _transcript(tmp_path, "research agent memory", searches=5)
    payload = _payload(transcript, session_id="dup12345")

    _run(payload, tmp_path)
    _run(payload, tmp_path)

    entries = list((tmp_path / "docs" / "knowledge-corpus" / "queue").glob("*.yaml"))
    assert len(entries) == 1


def test_disabled_by_environment(tmp_path: Path) -> None:
    """Scenario: the documented opt-out actually opts out."""
    import os

    transcript = _transcript(tmp_path, "research agent memory", searches=9)
    env = {**os.environ, "MEMORY_PALACE_AUTO_QUEUE": "false"}

    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(_payload(transcript)),
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


def test_malformed_transcript_lines_are_skipped(tmp_path: Path) -> None:
    """Scenario: a truncated final line must not lose the whole session."""
    transcript = _transcript(tmp_path, "research agent memory decay", searches=5)
    with transcript.open("a", encoding="utf-8") as handle:
        handle.write('{"type": "assistant", "message":\n')

    _run(_payload(transcript), tmp_path)

    assert "pending_review" in _entry_text(tmp_path)


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
    transcript = _transcript(
        tmp_path, 'research "mtime staleness" detection', searches=5
    )

    _run(_payload(transcript), tmp_path)
    frontmatter = _entry_text(tmp_path).split("---")[1]

    assert yaml.safe_load(frontmatter)["status"] == "pending_review"


def test_credential_in_prompt_is_redacted_everywhere_it_is_written(
    tmp_path: Path,
) -> None:
    """Scenario: redaction covers the topic and heading, not just the body.

    The entry outlives the session, so a credential reaching any of the
    three write sites is a credential on disk.
    """
    transcript = _transcript(
        tmp_path, "research sk-ABCDEFGHIJKLMNOP1234 rotation", searches=5
    )

    _run(_payload(transcript), tmp_path)

    assert "sk-ABCDEFGHIJKLMNOP1234" not in _entry_text(tmp_path)
    # The topic also becomes the filename. Redaction that runs after
    # slugification would leave the credential in the directory listing.
    assert "abcdefghijklmnop1234" not in _entry_path(tmp_path).name.lower()
