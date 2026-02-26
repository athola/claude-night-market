"""Tests for TDD skill wrapper."""

from __future__ import annotations

import pytest

from abstract.tdd_skill_wrapper import TddSkillWrapper


class TestTddSkillWrapper:
    """Tests for TddSkillWrapper behavior."""

    def test_wrapper_initializes_with_correct_superpower(self) -> None:
        """Given TddSkillWrapper, when created, then targets TDD superpower."""
        wrapper = TddSkillWrapper()
        assert wrapper.target_superpower == "test-driven-development"
        assert wrapper.source_plugin == "abstract"
        assert wrapper.source_command == "test-skill"

    def test_execute_with_valid_params(self) -> None:
        """Given valid params, when execute called, then returns result dict."""
        wrapper = TddSkillWrapper()
        result = wrapper.execute({"skill-path": "my/skill", "phase": "red"})
        assert result["superpower_called"] == "test-driven-development"
        assert result["phase_executed"] == "red"
        assert result["target"] == "my/skill"
        assert result["extensions"]["skill_validation"] is True

    def test_execute_missing_skill_path_raises(self) -> None:
        """Given missing skill-path, when execute called, then raises ValueError."""
        wrapper = TddSkillWrapper()
        with pytest.raises(ValueError, match="skill-path"):
            wrapper.execute({"phase": "red"})

    def test_execute_missing_phase_raises(self) -> None:
        """Given missing phase, when execute called, then raises ValueError."""
        wrapper = TddSkillWrapper()
        with pytest.raises(ValueError, match="phase"):
            wrapper.execute({"skill-path": "my/skill"})

    def test_execute_invalid_phase_raises(self) -> None:
        """Given invalid phase, when execute called, then raises ValueError."""
        wrapper = TddSkillWrapper()
        with pytest.raises(ValueError, match="phase must be one of"):
            wrapper.execute({"skill-path": "my/skill", "phase": "invalid"})

    def test_execute_empty_params_raises(self) -> None:
        """Given empty params, when execute called, then raises ValueError."""
        wrapper = TddSkillWrapper()
        with pytest.raises(ValueError, match="empty"):
            wrapper.execute({})

    def test_execute_non_string_skill_path_raises(self) -> None:
        """Given non-string skill-path, when execute called, then raises TypeError."""
        wrapper = TddSkillWrapper()
        with pytest.raises(TypeError, match="skill-path must be a string"):
            wrapper.execute({"skill-path": 123, "phase": "red"})

    def test_execute_all_valid_phases(self) -> None:
        """Given each valid phase, when execute called, then succeeds."""
        wrapper = TddSkillWrapper()
        for phase in ["red", "green", "refactor"]:
            result = wrapper.execute({"skill-path": "test/skill", "phase": phase})
            assert result["phase_executed"] == phase
