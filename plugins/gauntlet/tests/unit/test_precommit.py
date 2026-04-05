"""Tests for the pre-commit gate hook."""

from __future__ import annotations

import json

# The hook lives outside src/ so we import it by path manipulation.
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

_HOOKS_DIR = Path(__file__).parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from precommit_gate import (  # noqa: E402 - hook lives outside src/, path inserted above
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
