"""Coverage booster 2: tests targeting remaining uncovered branches.

Feature: Coverage booster for src/abstract missing branches
    As a developer
    I want remaining uncovered branches in src/abstract tested
    So that overall coverage reaches 90%
"""

from __future__ import annotations

import builtins
import sys
from pathlib import Path

import pytest

from abstract.rollback_reviewer import RollbackReviewer
from abstract.skill_tools import analyze_skill
from abstract.skill_versioning import SkillVersionManager
from abstract.tdd_skill_wrapper import TddSkillWrapper
from abstract.tokens import analyze_content, check_efficiency, estimate_tokens

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


# ---------------------------------------------------------------------------
# Tests: tdd_skill_wrapper.py lines 64-65
# (phase not a string raises TypeError)
# ---------------------------------------------------------------------------


class TestTddSkillWrapperPhaseType:
    """Feature: TddSkillWrapper validates phase parameter type."""

    @pytest.mark.unit
    def test_execute_non_string_phase_raises_type_error(self) -> None:
        """Scenario: Non-string phase raises TypeError.
        Given a params dict where phase is an integer
        When execute is called
        Then TypeError is raised with 'phase must be a string' message
        """
        wrapper = TddSkillWrapper()
        with pytest.raises(TypeError, match="phase must be a string"):
            wrapper.execute({"skill-path": "my/skill", "phase": 42})


# ---------------------------------------------------------------------------
# Tests: tokens.py lines 43, 263, 284
# (estimate_tokens with empty string + analyze_content + check_efficiency)
# ---------------------------------------------------------------------------


class TestTokensModuleFunctions:
    """Feature: Module-level token functions delegate to TokenAnalyzer."""

    @pytest.mark.unit
    def test_estimate_tokens_empty_string_returns_zero(self) -> None:
        """Scenario: estimate_tokens('') returns 0.
        Given an empty string
        When estimate_tokens is called
        Then 0 is returned without error
        """
        result = estimate_tokens("")
        assert result == 0

    @pytest.mark.unit
    def test_analyze_content_module_function_returns_dict(self) -> None:
        """Scenario: Module-level analyze_content delegates to TokenAnalyzer.
        Given a non-empty content string
        When the module-level analyze_content is called
        Then a dict with token breakdown is returned
        """
        result = analyze_content("# Heading\n\nSome text content here.\n")
        assert isinstance(result, dict)
        assert "total_tokens" in result

    @pytest.mark.unit
    def test_check_efficiency_module_function_returns_dict(self) -> None:
        """Scenario: Module-level check_efficiency delegates to TokenAnalyzer.
        Given a token_count value
        When the module-level check_efficiency is called
        Then a dict with efficiency metrics is returned
        """
        result = check_efficiency(1500, optimal=2000, max_acceptable=4000)
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# Tests: rollback_reviewer.py line 78
# (invalid commit hash raises ValueError)
# ---------------------------------------------------------------------------


class TestRollbackReviewerInvalidHash:
    """Feature: generate_rollback_command rejects invalid commit hashes."""

    @pytest.mark.unit
    def test_invalid_commit_hash_raises_value_error(self) -> None:
        """Scenario: Commit hash with invalid characters raises ValueError.
        Given a commit hash containing uppercase letters or special characters
        When generate_rollback_command is called
        Then ValueError is raised with a helpful message
        """
        reviewer = RollbackReviewer()
        with pytest.raises(ValueError, match="Invalid commit hash"):
            reviewer.generate_rollback_command("INVALID-HASH!")

    @pytest.mark.unit
    def test_commit_hash_with_uppercase_raises_value_error(self) -> None:
        """Scenario: Commit hash with uppercase letters raises ValueError.
        Given a commit hash like 'ABC123' (uppercase)
        When generate_rollback_command is called
        Then ValueError is raised
        """
        reviewer = RollbackReviewer()
        with pytest.raises(ValueError, match="Invalid commit hash"):
            reviewer.generate_rollback_command("ABC123DEF")


# ---------------------------------------------------------------------------
# Tests: skill_tools.py lines 81-82
# (Exception handler in analyze_skill when reading fails)
# ---------------------------------------------------------------------------


class TestAnalyzeSkillException:
    """Feature: analyze_skill handles file read exceptions gracefully."""

    @pytest.mark.unit
    def test_analyze_skill_unreadable_file_records_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario: Unreadable skill file results in error dict entry.
        Given a skill directory with an unreadable SKILL.md
        When analyze_skill is called
        Then results contain an entry with 'error' key
        """
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# My Skill\n\nContent.\n")

        original_open = builtins.open

        def raising_open(file, *args, **kwargs):
            if Path(file) == skill_file:
                raise OSError("Permission denied")
            return original_open(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", raising_open)

        result = analyze_skill(str(skill_dir))
        # Should have one result entry with error
        assert result["total_files"] == 1
        error_entry = result["results"][0]
        assert "error" in error_entry
        assert error_entry["complexity"] == "error"


# ---------------------------------------------------------------------------
# Tests: skill_versioning.py lines 104-105
# (OSError in _write method)
# ---------------------------------------------------------------------------


class TestSkillVersioningWriteError:
    """Feature: SkillVersionManager._write handles OSError gracefully."""

    @pytest.mark.unit
    def test_write_failure_logs_to_stderr(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Scenario: OSError during file write is reported to stderr.
        Given a skill file and a patched write_text that raises OSError
        When bump_version is called
        Then stderr contains the error message
        """
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: test-skill\nversion: 1.0.0\n---\n\n# Test\n")

        manager = SkillVersionManager(skill_file)

        call_count = {"n": 0}

        def raising_write_text(self, *args, **kwargs):
            call_count["n"] += 1
            # Allow any initial reads; raise on first write_text call
            raise OSError("Disk full")

        monkeypatch.setattr(Path, "write_text", raising_write_text)

        # bump_version requires change_summary and metrics dict
        manager.bump_version("change summary", {"success_rate": 0.9})

        captured = capsys.readouterr()
        # The OSError is caught and reported to stderr
        assert "skill_versioning" in captured.err or "SKILL.md" in captured.err
