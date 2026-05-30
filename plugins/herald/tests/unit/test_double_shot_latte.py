"""Behavior tests for the Double Shot Latte Stop-hook continuation judge.

These tests encode the three defects the reimplementation fixes:

1. Input keyhole -- the judge must find the assistant's closing message even
   when many tool-result lines follow it in the transcript.
2. Cross-platform state -- throttling must use the OS temp dir, never /tmp
   literally, and tolerate a missing/corrupt state file.
3. Stop-by-default bias -- a completed or question-ending turn must allow the
   stop; only an explicit next-action statement continues.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import double_shot_latte as dsl  # noqa: E402 - sys.path adjusted above


def _assistant_line(text: str) -> str:
    """Build a transcript JSONL line for an assistant text message."""
    return json.dumps(
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
            },
        }
    )


def _tool_result_line(payload: str) -> str:
    """Build a transcript JSONL line for a user/tool-result message."""
    block = {"type": "tool_result", "content": payload}
    return json.dumps({"type": "user", "message": {"role": "user", "content": [block]}})


class TestExtractLastAssistantText:
    """Feature: recover the assistant's closing message from a transcript.

    As the continuation judge
    I want the assistant's last *text* message regardless of trailing tool rows
    So that a finished turn is never misread as incomplete (defect #1).
    """

    @pytest.mark.unit
    def test_finds_assistant_text_behind_many_tool_lines(self):
        """
        Scenario: closing message is buried behind tool results
        Given an assistant message followed by 10 tool-result lines
        When the last assistant text is extracted
        Then the assistant's message is returned, not a tool line
        """
        lines = [_assistant_line("All done. Working tree is clean.")]
        lines += [_tool_result_line(f"output chunk {i}") for i in range(10)]
        transcript = "\n".join(lines)

        assert (
            dsl.extract_last_assistant_text(transcript)
            == "All done. Working tree is clean."
        )

    @pytest.mark.unit
    def test_returns_most_recent_assistant_message(self):
        """
        Scenario: multiple assistant turns
        Given two assistant messages in order
        When extracted
        Then the later one wins
        """
        transcript = "\n".join(
            [
                _assistant_line("first"),
                _tool_result_line("x"),
                _assistant_line("second"),
            ]
        )
        assert dsl.extract_last_assistant_text(transcript) == "second"

    @pytest.mark.unit
    def test_skips_malformed_lines(self):
        """
        Scenario: corrupt JSONL rows
        Given a transcript with a non-JSON line after the assistant message
        When extracted
        Then the malformed line is skipped and the assistant text is returned
        """
        transcript = "\n".join(
            [_assistant_line("kept"), "{not json", "   ", _tool_result_line("y")]
        )
        assert dsl.extract_last_assistant_text(transcript) == "kept"

    @pytest.mark.unit
    def test_handles_plain_string_content(self):
        """
        Scenario: alternate schema with string content
        Given an assistant entry whose content is a plain string
        When extracted
        Then the string is returned
        """
        line = json.dumps({"role": "assistant", "content": "plain text reply"})
        assert dsl.extract_last_assistant_text(line) == "plain text reply"

    @pytest.mark.unit
    def test_empty_transcript_returns_empty(self):
        """
        Scenario: no assistant content
        Given an empty transcript
        When extracted
        Then an empty string is returned
        """
        assert dsl.extract_last_assistant_text("") == ""


class TestClassify:
    """Feature: decide continue vs stop with a stop-by-default bias (defect #3).

    As the continuation judge
    I want to continue only on explicit next-action intent
    So that completed work is not nagged with false 'keep going' prompts.
    """

    @pytest.mark.unit
    def test_completion_statement_stops(self):
        """Given a completion summary, when classified, then stop."""
        should, _ = dsl.classify("The task is complete and pushed. Nothing left to do.")
        assert should is False

    @pytest.mark.unit
    def test_question_ending_stops(self):
        """Given a turn ending in a question, when classified, then stop."""
        should, _ = dsl.classify("I can take either path. Which option do you prefer?")
        assert should is False

    @pytest.mark.unit
    def test_await_phrase_stops(self):
        """Given an offer awaiting input, when classified, then stop."""
        should, _ = dsl.classify("I fixed the bug. Let me know if you want tests too.")
        assert should is False

    @pytest.mark.unit
    def test_explicit_next_action_continues(self):
        """Given explicit next-action intent, when classified, then continue."""
        should, _ = dsl.classify(
            "I committed the fix. Next, I'll add the regression test and push."
        )
        assert should is True

    @pytest.mark.unit
    def test_now_ill_continues(self):
        """Given a 'now I'll' statement, when classified, then continue."""
        should, _ = dsl.classify("Now I'll run the full suite to confirm.")
        assert should is True

    @pytest.mark.unit
    def test_empty_text_stops(self):
        """Given no text, when classified, then stop."""
        should, _ = dsl.classify("   ")
        assert should is False

    @pytest.mark.unit
    def test_neutral_text_falls_through_to_stop(self):
        """
        Scenario: a turn with neither completion, question, nor next-action
        Given prose that matches no continuation or completion pattern
        When classified
        Then the stop-by-default fall-through wins (defect #3 guard)

        This guards the final ``return False`` specifically: completion and
        question turns are caught by earlier branches, so only neutral text
        exercises the default. Flipping the default to continue breaks this.
        """
        should, reason = dsl.classify(
            "I looked at the file and the configuration values are reasonable."
        )
        assert should is False
        assert "defaulting to stop" in reason

    @pytest.mark.unit
    def test_early_next_with_trailing_completion_stops(self):
        """
        Scenario: a long turn that mentions 'next' early but ends complete
        Given text whose tail is a completion, not an intent
        When classified
        Then the trailing completion wins (tail window), so stop
        """
        text = (
            "Next I considered several approaches. "
            + ("padding. " * 200)
            + "Everything is done and verified clean."
        )
        should, _ = dsl.classify(text)
        assert should is False


class TestThrottleCrossPlatform:
    """Feature: throttle state lives in the OS temp dir, not literal /tmp.

    This is defect #2: the original hardcoded ``/tmp``, invalid on Windows.
    """

    @pytest.mark.unit
    def test_throttle_path_uses_system_tempdir(self, tmp_path, monkeypatch):
        """
        Scenario: temp dir resolution
        Given a custom temp dir
        When a throttle path is built
        Then it is rooted in that temp dir (portable), not hardcoded /tmp
        """
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        path = dsl._throttle_path("sess/with:bad*chars")
        assert path.parent == tmp_path
        assert "/" not in path.name and ":" not in path.name and "*" not in path.name

    @pytest.mark.unit
    def test_read_throttle_tolerates_missing_file(self, tmp_path):
        """Given no state file, when read, then a zeroed tuple is returned."""
        assert dsl._read_throttle(tmp_path / "nope.json") == (0, 0.0)

    @pytest.mark.unit
    def test_read_throttle_tolerates_corrupt_file(self, tmp_path):
        """Given a corrupt state file, when read, then a zeroed tuple."""
        p = tmp_path / "corrupt.json"
        p.write_text("{ not json", encoding="utf-8")
        assert dsl._read_throttle(p) == (0, 0.0)

    @pytest.mark.unit
    def test_write_then_read_roundtrips(self, tmp_path):
        """Given a written state, when read back, then values match."""
        p = tmp_path / "state.json"
        dsl._write_throttle(p, 2, 1234.5)
        assert dsl._read_throttle(p) == (2, 1234.5)


class TestDecide:
    """Feature: end-to-end Stop decision with recursion guard and throttling."""

    @pytest.mark.unit
    def test_judge_mode_short_circuits(self, monkeypatch):
        """Given JUDGE mode, when deciding, then approve (prevents recursion)."""
        monkeypatch.setenv(dsl.JUDGE_MODE_ENV, "true")
        out = dsl.decide({}, now=1000.0)
        assert out["decision"] == "approve"

    @pytest.mark.unit
    def test_missing_transcript_approves(self, monkeypatch):
        """Given no transcript path, when deciding, then approve the stop."""
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        out = dsl.decide({"session_id": "s1"}, now=1000.0)
        assert out["decision"] == "approve"

    @pytest.mark.unit
    def test_completed_turn_approves(self, tmp_path, monkeypatch):
        """
        Scenario: the exact failure that misfired on us
        Given a transcript whose last assistant message reports completion,
              followed by tool-result lines
        When deciding
        Then the stop is approved (no false continue)
        """
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        transcript = tmp_path / "t.jsonl"
        closing = "All four updated. The task is complete and verified."
        lines = [_assistant_line(closing)]
        lines += [_tool_result_line(f"chunk {i}") for i in range(6)]
        transcript.write_text("\n".join(lines), encoding="utf-8")

        out = dsl.decide(
            {"session_id": "s1", "transcript_path": str(transcript)}, now=1000.0
        )
        assert out["decision"] == "approve"

    @pytest.mark.unit
    def test_continuing_turn_blocks(self, tmp_path, monkeypatch):
        """Given an explicit next-action turn, when deciding, then block (continue)."""
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        transcript = tmp_path / "t.jsonl"
        transcript.write_text(
            _assistant_line("Tests pass. Now I'll update the docs."), encoding="utf-8"
        )
        out = dsl.decide(
            {"session_id": "s2", "transcript_path": str(transcript)}, now=1000.0
        )
        assert out["decision"] == "block"

    @pytest.mark.unit
    def test_throttle_forces_stop_after_max(self, tmp_path, monkeypatch):
        """
        Scenario: runaway loop guard
        Given the throttle already at MAX within the window
        When deciding on an otherwise-continue turn with stop_hook_active
        Then the stop is forced (approve)
        """
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        transcript = tmp_path / "t.jsonl"
        transcript.write_text(
            _assistant_line("Now I'll keep going forever."), encoding="utf-8"
        )
        throttle = dsl._throttle_path("s3")
        dsl._write_throttle(throttle, dsl.MAX_CONTINUATIONS, 1000.0)

        out = dsl.decide(
            {
                "session_id": "s3",
                "transcript_path": str(transcript),
                "stop_hook_active": True,
            },
            now=1001.0,
        )
        assert out["decision"] == "approve"
        assert "Maximum continuation" in out["reason"]
