"""Tests for the pre-commit gate hook."""

from __future__ import annotations

import datetime
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import precommit_gate
import pytest
from precommit_gate import (
    check_pass_token,
    generate_challenge_for_files,
    main,
    write_pass_token,
)


class TestPassToken:
    """
    Feature: pass-token write/check mechanism

    As a pre-commit gate,
    I want a one-time token tied to a staged-file hash,
    So that a completed challenge allows exactly one commit through.
    """

    @pytest.mark.unit
    def test_write_and_check_token(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: A freshly written token is valid
        Given a staged hash and a gauntlet directory
        When write_pass_token is called and then check_pass_token is called
        Then check_pass_token returns True
        """
        write_pass_token(tmp_gauntlet_dir, "abc123")
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is True

    @pytest.mark.unit
    def test_token_consumed_on_use(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: Checking a token deletes it (one-time use)
        Given a written pass token
        When check_pass_token is called successfully once
        Then a second call with the same hash returns False
        """
        write_pass_token(tmp_gauntlet_dir, "abc123")
        check_pass_token(tmp_gauntlet_dir, "abc123")
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is False

    @pytest.mark.unit
    def test_wrong_hash_fails(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: Token with wrong hash is rejected
        Given a token written for hash "abc123"
        When check_pass_token is called with hash "wrong"
        Then it returns False
        """
        write_pass_token(tmp_gauntlet_dir, "abc123")
        assert check_pass_token(tmp_gauntlet_dir, "wrong") is False

    @pytest.mark.unit
    def test_expired_token_fails(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: An expired token is rejected
        Given a token written with ttl_seconds=0
        When a brief delay passes and check_pass_token is called
        Then it returns False
        """
        write_pass_token(tmp_gauntlet_dir, "abc123", ttl_seconds=0)
        time.sleep(0.1)
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is False

    @pytest.mark.unit
    def test_token_stamped_in_the_future_fails(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: A token whose issue time is in the future is rejected
        Given the wall clock moved backward after the token was written
        When check_pass_token is called while expires_at is still ahead
        Then it returns False instead of honoring the unexpired token
        """
        state_dir = tmp_gauntlet_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now(datetime.timezone.utc)
        token = {
            "staged_hash": "abc123",
            "issued_at": (now + datetime.timedelta(seconds=60)).isoformat(),
            "expires_at": (now + datetime.timedelta(seconds=360)).isoformat(),
        }
        (state_dir / "pass_token.json").write_text(json.dumps(token))
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is False

    @pytest.mark.unit
    def test_missing_token_fails(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: No token file means check fails
        Given a gauntlet directory with no pass token written
        When check_pass_token is called
        Then it returns False
        """
        assert check_pass_token(tmp_gauntlet_dir, "abc123") is False


class TestGenerateChallenge:
    """
    Feature: generate_challenge_for_files selects a relevant challenge

    As a pre-commit gate,
    I want to generate a challenge tied to the staged files,
    So that the developer must demonstrate understanding before committing.
    """

    @pytest.mark.unit
    def test_generates_challenge_from_knowledge_base(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: Files that match knowledge entries produce a challenge
        Given a knowledge base with a billing entry
        When generate_challenge_for_files is called with ["billing"]
        Then a Challenge object is returned
        """
        gauntlet_dir = sample_knowledge_base.parent
        challenge = generate_challenge_for_files(
            gauntlet_dir, ["billing"], "dev@example.com"
        )
        assert challenge is not None
        assert challenge.knowledge_entry_id == "ke-001"

    @pytest.mark.unit
    def test_no_knowledge_returns_none(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: No matching knowledge entries returns None
        Given an empty gauntlet directory
        When generate_challenge_for_files is called
        Then None is returned
        """
        result = generate_challenge_for_files(
            tmp_gauntlet_dir, ["billing"], "dev@example.com"
        )
        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_challenges_unimportable(
        self,
        sample_knowledge_base: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Scenario: gauntlet.challenges cannot be imported at hook time
        Given a populated knowledge base (so the entry-miss early return
          does not fire) and a Python environment where
          `from gauntlet.challenges import ...` raises ImportError
        When generate_challenge_for_files is called with matching files
        Then it returns None via the hook-level try/except, not by
          crashing the precommit hook with ModuleNotFoundError

        Encodes the invariant established in 2026-04-26: the lazy
        import inside generate_challenge_for_files must catch ImportError
        so the precommit hook stays a clean no-op when optional deps
        are missing. The lower-level fallback in
        gauntlet.challenges._generate_problem_variation is covered by
        TestProblemVariationFallback in test_challenges.py; this test
        guards the hook surface itself.
        """
        # monkeypatch makes `from gauntlet.challenges import ...`
        # raise ImportError so we exercise the
        # `except ImportError: return None` branch in
        # generate_challenge_for_files. monkeypatch auto-restores.
        monkeypatch.setitem(sys.modules, "gauntlet.challenges", None)

        gauntlet_dir = sample_knowledge_base.parent
        result = generate_challenge_for_files(
            gauntlet_dir, ["billing"], "dev@example.com"
        )
        assert result is None

    @pytest.mark.unit
    def test_import_error_silent_without_debug_env(
        self,
        sample_knowledge_base: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Scenario: ImportError swallow does not pollute stderr by default
        Given GAUNTLET_DEBUG is unset and gauntlet.challenges is unimportable
        When generate_challenge_for_files is called
        Then it returns None without writing to stderr (silent in normal use)
        """
        monkeypatch.delenv("GAUNTLET_DEBUG", raising=False)
        monkeypatch.setitem(sys.modules, "gauntlet.challenges", None)

        gauntlet_dir = sample_knowledge_base.parent
        result = generate_challenge_for_files(
            gauntlet_dir, ["billing"], "dev@example.com"
        )

        assert result is None
        captured = capsys.readouterr()
        assert captured.err == ""

    @pytest.mark.unit
    def test_import_error_logs_to_stderr_with_debug_env(
        self,
        sample_knowledge_base: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """
        Scenario: GAUNTLET_DEBUG=1 surfaces the swallowed ImportError
        Given GAUNTLET_DEBUG is set and gauntlet.challenges is unimportable
        When generate_challenge_for_files is called
        Then it returns None AND writes a diagnostic line to stderr that
          identifies the cause (gauntlet.challenges unimportable)

        Regression: without this opt-in observability hook, a silent
        regression inside gauntlet.challenges (vs. a missing optional
        dep) is indistinguishable from the intended graceful-degradation
        path, so debugging is blind.
        """
        monkeypatch.setenv("GAUNTLET_DEBUG", "1")
        monkeypatch.setitem(sys.modules, "gauntlet.challenges", None)

        gauntlet_dir = sample_knowledge_base.parent
        result = generate_challenge_for_files(
            gauntlet_dir, ["billing"], "dev@example.com"
        )

        assert result is None
        captured = capsys.readouterr()
        assert "gauntlet.challenges unimportable" in captured.err
        assert "[gauntlet] precommit_gate" in captured.err


class TestMain:
    """
    Feature: main() hook entry point

    As the Claude Code hook runner,
    I want a main() function that reads hook input and returns a decision,
    So that git commits can be gated on challenge completion.
    """

    @pytest.mark.unit
    def test_non_commit_command_passes(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: Non-commit bash commands are not intercepted
        Given a hook input with command "git status"
        When main() is called
        Then it returns None (no decision)
        """
        hook_input = {
            "tool_input": {"command": "git status"},
        }
        result = main(hook_input)
        assert result is None

    @pytest.mark.unit
    def test_no_gauntlet_dir_passes(self, tmp_path: Path) -> None:
        """
        Scenario: No .gauntlet directory means hook is inactive
        Given a hook input with "git commit" and no .gauntlet dir
        When main() is called
        Then it returns None
        """
        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=None):
            result = main(hook_input)
        assert result is None

    @pytest.mark.unit
    def test_mode_off_passes(self, tmp_gauntlet_dir: Path) -> None:
        """
        Scenario: precommit.mode=off disables the gate entirely
        Given a .gauntlet config with precommit.mode = "off"
        When main() is called with a git commit command
        Then it returns None
        """
        config = {"precommit": {"mode": "off"}}
        (tmp_gauntlet_dir / "config.json").write_text(json.dumps(config))
        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=tmp_gauntlet_dir):
            result = main(hook_input)
        assert result is None

    @pytest.mark.unit
    def test_allows_with_valid_token(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: A valid pass token allows the commit through
        Given a .gauntlet dir in gate mode with a valid token for the staged hash
        When main() is called with a git commit command
        Then it returns a decision of "allow"
        """
        gauntlet_dir = sample_knowledge_base.parent
        staged_hash = "deadbeef"
        write_pass_token(gauntlet_dir, staged_hash)

        config = {"precommit": {"mode": "gate"}}
        (gauntlet_dir / "config.json").write_text(json.dumps(config))

        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value=staged_hash):
                result = main(hook_input)

        assert result is not None
        hso = result.get("hookSpecificOutput", {})
        assert hso.get("permissionDecision") == "allow"

    @pytest.mark.unit
    def test_denies_with_no_token_gate_mode(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: No pass token in gate mode denies the commit
        Given a .gauntlet dir in gate mode with no valid token and staged files
        When main() is called with a git commit command
        Then it returns a decision of "deny"
        """
        gauntlet_dir = sample_knowledge_base.parent
        config = {"precommit": {"mode": "gate"}}
        (gauntlet_dir / "config.json").write_text(json.dumps(config))

        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value="somehash"):
                with patch(
                    "precommit_gate._get_developer_id", return_value="dev@example.com"
                ):
                    with patch(
                        "precommit_gate._get_staged_files", return_value=["billing"]
                    ):
                        result = main(hook_input)

        assert result is not None
        hso = result.get("hookSpecificOutput", {})
        assert hso.get("permissionDecision") == "deny"

    @pytest.mark.unit
    def test_passes_on_git_failure_nudge_mode(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: Git failure in nudge mode passes through
        Given a .gauntlet dir in nudge mode
        When _get_staged_files returns None (git failure)
        Then it returns None (no opinion).
        """
        gauntlet_dir = sample_knowledge_base.parent
        config = {"precommit": {"mode": "nudge"}}
        (gauntlet_dir / "config.json").write_text(json.dumps(config))

        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value="somehash"):
                with patch("precommit_gate._get_staged_files", return_value=None):
                    result = main(hook_input)

        assert result is None

    @pytest.mark.unit
    def test_denies_on_git_failure_gate_mode(self, sample_knowledge_base: Path) -> None:
        """
        Scenario: Git failure in gate mode denies the commit
        Given a .gauntlet dir in gate mode
        When _get_staged_files returns None (git failure)
        Then it returns hookSpecificOutput with permissionDecision "deny"
        And the reason mentions git failure.
        """
        gauntlet_dir = sample_knowledge_base.parent
        config = {"precommit": {"mode": "gate"}}
        (gauntlet_dir / "config.json").write_text(json.dumps(config))

        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value="somehash"):
                with patch("precommit_gate._get_staged_files", return_value=None):
                    result = main(hook_input)

        assert result is not None
        hso = result.get("hookSpecificOutput", {})
        assert hso.get("permissionDecision") == "deny"
        assert "git failure" in hso.get("permissionDecisionReason", "").lower()

    @pytest.mark.unit
    def test_nudge_mode_adds_context_instead_of_denying(
        self, sample_knowledge_base: Path
    ) -> None:
        """
        Scenario: nudge mode adds context but does not block the commit
        Given a .gauntlet dir in nudge mode with no valid token
        When main() is called with a git commit command
        Then it returns additionalContext without a "deny" decision
        """
        gauntlet_dir = sample_knowledge_base.parent
        config = {"precommit": {"mode": "nudge"}}
        (gauntlet_dir / "config.json").write_text(json.dumps(config))

        hook_input = {"tool_input": {"command": "git commit -m 'test'"}}
        with patch("precommit_gate._get_gauntlet_dir", return_value=gauntlet_dir):
            with patch("precommit_gate._get_staged_hash", return_value="somehash"):
                with patch(
                    "precommit_gate._get_developer_id", return_value="dev@example.com"
                ):
                    with patch(
                        "precommit_gate._get_staged_files", return_value=["billing"]
                    ):
                        result = main(hook_input)

        # nudge: returns additionalContext without hookSpecificOutput deny
        assert result is not None
        assert "hookSpecificOutput" not in result
        assert "additionalContext" in result


class TestGateFailsClosed:
    """
    Feature: an unexpected failure denies the commit

    As a pre-commit gate,
    I want any error I did not anticipate to deny,
    So that a crash cannot be the way past me.

    This gate is the one hook among the 77 whose crash releases a
    block rather than losing a log line. `__main__` guarded
    `json.loads` and called `main()` bare, so any exception below it
    became a traceback, exit 1, and a commit that proceeded ungated.
    """

    @pytest.mark.unit
    def test_git_missing_from_path_does_not_release_the_gate(
        self, sample_knowledge_base: Path
    ) -> None:
        """Scenario: git is absent, so the staged hash cannot be read.

        `_get_staged_hash` caught `CalledProcessError` only. A missing
        git raises `FileNotFoundError`, which needs no malformed input
        to trigger: any environment whose PATH lacks git opened the
        gate.
        """
        with patch(
            "precommit_gate.subprocess.run", side_effect=FileNotFoundError("git")
        ):
            digest = precommit_gate._get_staged_hash()

        assert digest == "", (
            "a missing git must yield no staged hash rather than raising, "
            "or the exception escapes main() and exits the gate nonzero"
        )

    @pytest.mark.unit
    def test_an_unexpected_error_inside_main_denies(
        self, sample_knowledge_base: Path
    ) -> None:
        """Scenario: something below main() raises.

        The gate must emit a deny, not a traceback. An exit-0 wrapper
        would be wrong here: for a gate, silence is permission.
        """
        with patch("precommit_gate.main", side_effect=RuntimeError("boom")):
            output = precommit_gate.run_gate(
                {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}
            )

        assert output is not None, "an internal error must still produce output"
        decision = output.get("hookSpecificOutput", {}).get("permissionDecision")
        assert decision == "deny", f"a gate must fail closed; got {output!r}"

    @pytest.mark.unit
    def test_the_git_calls_carry_a_timeout(self) -> None:
        """Guard: hooks.json caps this hook at 2s.

        A git call with no timeout can outlive that cap, and the hook
        is killed rather than returning its deny, which releases the
        gate by a second route.
        """
        source = (
            Path(__file__).resolve().parents[2] / "hooks" / "precommit_gate.py"
        ).read_text(encoding="utf-8")
        run_calls = source.count("subprocess.run(")
        timeouts = source.count("timeout=")
        assert timeouts >= run_calls, (
            f"{run_calls} subprocess.run calls but only {timeouts} timeout= "
            "arguments; a git call that hangs outlives the hook's 2s cap"
        )
