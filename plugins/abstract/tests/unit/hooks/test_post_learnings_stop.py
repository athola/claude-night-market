#!/usr/bin/env python3
"""Tests for the post_learnings_stop Stop hook.

Feature: Post learnings to GitHub Discussions on session stop

As an ecosystem maintainer
I want learnings posted to Discussions at session end
So that improvement data is captured automatically.
"""

from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import pytest

# Load the hook module dynamically
_HOOK_PATH = Path(__file__).parents[3] / "hooks" / "post_learnings_stop.py"
_spec = importlib.util.spec_from_file_location("post_learnings_stop", _HOOK_PATH)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["post_learnings_stop"] = _mod
_spec.loader.exec_module(_mod)


class TestStdinHandling:
    """Feature: Hook protocol stdin consumption

    As a Stop hook
    I want to safely consume and parse JSON from stdin
    So that malformed input never crashes the session.
    """

    @pytest.mark.unit
    def test_handles_valid_json_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: Valid JSON on stdin
        Given valid JSON on stdin
        When main() runs
        Then it consumes stdin without error.
        """
        monkeypatch.setattr("sys.stdin", io.StringIO('{"event": "stop"}'))
        monkeypatch.setattr(_mod, "_HAS_SCRIPTS", False)
        _mod.main()  # should not raise

    @pytest.mark.unit
    def test_handles_malformed_json_stdin(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Malformed JSON on stdin
        Given invalid JSON on stdin
        When main() runs
        Then it handles the JSONDecodeError gracefully.
        """
        monkeypatch.setattr("sys.stdin", io.StringIO("{not valid json!!!"))
        monkeypatch.setattr(_mod, "_HAS_SCRIPTS", False)
        _mod.main()  # should not raise

    @pytest.mark.unit
    def test_handles_empty_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: Empty stdin
        Given empty stdin
        When main() runs
        Then it exits without error.
        """
        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        monkeypatch.setattr(_mod, "_HAS_SCRIPTS", False)
        _mod.main()  # should not raise

    @pytest.mark.unit
    def test_handles_closed_stdin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Scenario: Closed stdin (pipe broken)
        Given stdin that raises OSError on read
        When main() runs
        Then it handles the error gracefully.
        """

        class BrokenStdin:
            def read(self) -> str:
                raise OSError("stdin closed")

        monkeypatch.setattr("sys.stdin", BrokenStdin())
        monkeypatch.setattr(_mod, "_HAS_SCRIPTS", False)
        _mod.main()  # should not raise


class TestLearningsContentCheck:
    """Feature: Skip posting when no content exists

    As a Stop hook
    I want to skip posting when LEARNINGS.md is empty
    So that empty summaries are not created.
    """

    @pytest.mark.unit
    def test_skips_when_no_learnings_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: LEARNINGS.md does not exist
        Given no LEARNINGS.md file
        When _learnings_have_content() is called
        Then it returns False.
        """
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert _mod._learnings_have_content() is False

    @pytest.mark.unit
    def test_skips_when_learnings_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: LEARNINGS.md has zero skills analyzed
        Given LEARNINGS.md with "Skills Analyzed: 0"
        When _learnings_have_content() is called
        Then it returns False.
        """
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "LEARNINGS.md").write_text("**Skills Analyzed**: 0\n")
        assert _mod._learnings_have_content() is False

    @pytest.mark.unit
    def test_detects_content(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: LEARNINGS.md has real content
        Given LEARNINGS.md with analyzed skills
        When _learnings_have_content() is called
        Then it returns True.
        """
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "LEARNINGS.md").write_text(
            "**Skills Analyzed**: 5\n\n## Findings\n..."
        )
        assert _mod._learnings_have_content() is True
