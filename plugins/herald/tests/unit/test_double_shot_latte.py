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
import os
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
    def test_llm_not_consulted_on_confident_verdict(self, tmp_path, monkeypatch):
        """
        Scenario: the optional LLM second shot must not override a confident verdict
        Given a transcript whose last message confidently reports completion
        And the LLM second shot is enabled
        When deciding
        Then the deterministic STOP stands and the LLM is never consulted
              (H2: the second shot is a tiebreaker for ambiguous turns only)
        """
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setenv("DOUBLE_SHOT_LATTE_LLM", "1")
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        calls: list[str] = []
        monkeypatch.setattr(
            dsl, "_llm_second_shot", lambda text: (calls.append(text), (True, "x"))[1]
        )
        transcript = tmp_path / "t.jsonl"
        transcript.write_text(
            _assistant_line("The task is complete and verified. Nothing left to do."),
            encoding="utf-8",
        )

        out = dsl.decide(
            {"session_id": "c1", "transcript_path": str(transcript)}, now=1000.0
        )
        assert out["decision"] == "approve"
        assert calls == []

    @pytest.mark.unit
    def test_llm_consulted_on_ambiguous_verdict(self, tmp_path, monkeypatch):
        """
        Scenario: an ambiguous (default fall-through) turn may defer to the LLM
        Given a neutral transcript that matches no continuation/completion signal
        And the LLM second shot is enabled and returns 'continue'
        When deciding
        Then the LLM is consulted and its verdict is used (block)
        """
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setenv("DOUBLE_SHOT_LATTE_LLM", "1")
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        calls: list[str] = []
        monkeypatch.setattr(
            dsl,
            "_llm_second_shot",
            lambda text: (calls.append(text), (True, "llm: keep going"))[1],
        )
        transcript = tmp_path / "t.jsonl"
        transcript.write_text(
            _assistant_line("I reviewed the configuration values in the file."),
            encoding="utf-8",
        )

        out = dsl.decide(
            {"session_id": "c2", "transcript_path": str(transcript)}, now=1000.0
        )
        assert out["decision"] == "block"
        assert calls != []

    @pytest.mark.unit
    def test_throttle_prompts_user_after_max(self, tmp_path, monkeypatch):
        """
        Scenario: cap reached -> hand back to the user with a prompt
        Given the throttle already at MAX within the window
        When deciding on an otherwise-continue turn with stop_hook_active
        Then the stop is approved and the reason prompts the user to continue,
              naming the limit that was hit (legitimate long runs can resume)
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
        # The message must prompt the user (not just announce a hard stop) and
        # name the concrete limit that tripped, so the user knows why it paused.
        assert "continue" in out["reason"].lower()
        assert str(dsl.MAX_CONTINUATIONS) in out["reason"]

    @pytest.mark.unit
    def test_max_continuations_is_ten(self):
        """
        Scenario: the auto-continue budget is raised from 3 to 10
        Given the configured continuation cap
        When read
        Then it is 10 (longer autonomous runs are allowed before a check-in)
        """
        assert dsl.MAX_CONTINUATIONS == 10

    @pytest.mark.unit
    def test_below_new_limit_still_continues(self, tmp_path, monkeypatch):
        """
        Scenario: the cap genuinely moved, not just relabeled
        Given the throttle one short of MAX within the window (would have tripped
              the old cap of 3)
        When deciding on an explicit next-action turn with stop_hook_active
        Then the turn still blocks (continue), proving the budget is now larger
        """
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        transcript = tmp_path / "t.jsonl"
        transcript.write_text(
            _assistant_line("Tests pass. Now I'll update the docs."), encoding="utf-8"
        )
        throttle = dsl._throttle_path("s9")
        dsl._write_throttle(throttle, dsl.MAX_CONTINUATIONS - 1, 1000.0)

        out = dsl.decide(
            {
                "session_id": "s9",
                "transcript_path": str(transcript),
                "stop_hook_active": True,
            },
            now=1001.0,
        )
        assert out["decision"] == "block"

    @pytest.mark.unit
    def test_cap_clears_throttle_for_fresh_window(self, tmp_path, monkeypatch):
        """
        Scenario: after the prompt, a user who continues gets a fresh budget
        Given the throttle at MAX within the window
        When the cap forces a stop
        Then the throttle file is cleared, so re-engaging starts a new count
              rather than instantly re-tripping the cap
        """
        monkeypatch.delenv(dsl.JUDGE_MODE_ENV, raising=False)
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        transcript = tmp_path / "t.jsonl"
        transcript.write_text(
            _assistant_line("Now I'll keep going forever."), encoding="utf-8"
        )
        throttle = dsl._throttle_path("s10")
        dsl._write_throttle(throttle, dsl.MAX_CONTINUATIONS, 1000.0)

        dsl.decide(
            {
                "session_id": "s10",
                "transcript_path": str(transcript),
                "stop_hook_active": True,
            },
            now=1001.0,
        )
        assert not throttle.exists()


class TestLlmTimeoutBudget:
    """Feature: the LLM second shot must finish within the hook's time budget.

    H1: the Stop hook is registered in hooks.json with a wall-clock timeout.
    If the LLM subprocess is allowed to run longer than that, the harness kills
    the whole hook before it can print any decision -- so the LLM timeout must
    be strictly less than the registered hook timeout, with margin for startup.
    """

    @pytest.mark.unit
    def test_llm_timeout_fits_within_hook_timeout(self):
        """
        Scenario: cross-component timeout consistency
        Given the hook timeout registered in hooks.json
        When compared to LLM_TIMEOUT_SECONDS
        Then the LLM timeout is strictly smaller, leaving margin to emit output
        """
        hooks_json = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
        hook_timeout = hooks_json["hooks"]["Stop"][0]["hooks"][0]["timeout"]
        assert dsl.LLM_TIMEOUT_SECONDS < hook_timeout


class TestHookRegistrationPortable:
    """Feature: the hook is registered in a way that runs on every platform.

    H3: ``python3`` is frequently absent on native Windows (the launcher is
    ``py`` and ``python3.exe`` ships only with the Store build). Invoking the
    script directly lets the shebang drive it on Unix and the ``.py`` file
    association (``py`` launcher) drive it on Windows.
    """

    @pytest.mark.unit
    def test_command_does_not_hardcode_python3(self):
        """
        Scenario: portable hook invocation
        Given the registered Stop hook command
        When inspected
        Then it invokes the script directly, not via a hardcoded 'python3'
        """
        hooks_json = json.loads((HOOKS_DIR / "hooks.json").read_text(encoding="utf-8"))
        cmd = hooks_json["hooks"]["Stop"][0]["hooks"][0]["command"]
        assert not cmd.startswith("python3 ")
        assert not cmd.startswith("python ")
        assert cmd.endswith("double_shot_latte.py")

    @pytest.mark.unit
    def test_script_has_python_shebang(self):
        """
        Scenario: direct invocation precondition
        Given the hook script
        When its first line is read
        Then it carries a python shebang (and is executable off Windows)
        """
        script = HOOKS_DIR / "double_shot_latte.py"
        first_line = script.read_text(encoding="utf-8").splitlines()[0]
        assert first_line.startswith("#!") and "python" in first_line
        if sys.platform != "win32":
            assert os.access(script, os.X_OK)


class TestThrottleSweep:
    """Feature: abandoned-session throttle files are eventually reclaimed.

    H4: a session that keeps continuing and is then closed without a final
    stop leaves its per-session throttle file in the temp dir. A best-effort
    sweep removes files older than the TTL so the temp dir does not accumulate
    orphans across sessions.
    """

    @pytest.mark.unit
    def test_sweep_removes_stale_keeps_fresh(self, tmp_path, monkeypatch):
        """
        Scenario: orphan reclamation
        Given one throttle file aged past the TTL and one recent file
        When the sweep runs
        Then the stale file is removed and the fresh file is kept
        """
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        now = 1_000_000.0
        stale = dsl._throttle_path("abandoned")
        fresh = dsl._throttle_path("active")
        dsl._write_throttle(stale, 2, now)
        dsl._write_throttle(fresh, 1, now)
        aged = now - dsl.THROTTLE_TTL_SECONDS - 100
        os.utime(stale, (aged, aged))
        os.utime(fresh, (now, now))

        dsl._sweep_stale_throttles(now)

        assert not stale.exists()
        assert fresh.exists()

    @pytest.mark.unit
    def test_sweep_tolerates_missing_tempdir(self, tmp_path, monkeypatch):
        """Given a non-existent temp dir, when sweeping, then no error is raised."""
        monkeypatch.setattr(
            dsl.tempfile, "gettempdir", lambda: str(tmp_path / "does-not-exist")
        )
        dsl._sweep_stale_throttles(1000.0)  # must not raise

    @pytest.mark.unit
    def test_sweep_only_targets_throttle_files(self, tmp_path, monkeypatch):
        """Given an unrelated old file, when sweeping, then it is left untouched."""
        monkeypatch.setattr(dsl.tempfile, "gettempdir", lambda: str(tmp_path))
        now = 1_000_000.0
        unrelated = tmp_path / "important-other-tool.json"
        unrelated.write_text("{}", encoding="utf-8")
        aged = now - dsl.THROTTLE_TTL_SECONDS - 100
        os.utime(unrelated, (aged, aged))

        dsl._sweep_stale_throttles(now)

        assert unrelated.exists()
