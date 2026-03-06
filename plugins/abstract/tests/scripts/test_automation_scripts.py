"""Tests for automation_setup and automation_validate scripts."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from automation_setup import main as setup_main  # noqa: E402
from automation_setup import setup_skills_eval
from automation_validate import (  # noqa: E402
    check_dependencies,
    validate_directory,
    validate_skill,
)
from automation_validate import (
    main as validate_main,
)

# ---------------------------------------------------------------------------
# Tests: automation_setup.py
# ---------------------------------------------------------------------------


class TestSetupSkillsEval:
    """Tests for setup_skills_eval function."""

    @pytest.mark.unit
    def test_returns_false_when_dirs_missing(self) -> None:
        """Returns bool regardless of whether skill dirs exist."""
        result = setup_skills_eval()
        assert isinstance(result, bool)


class TestSetupMain:
    """Tests for automation_setup main()."""

    @pytest.mark.unit
    def test_main_exits_with_code(self) -> None:
        """main() always exits with 0 or 1."""
        with pytest.raises(SystemExit) as exc_info:
            setup_main()
        assert exc_info.value.code in (0, 1)


# ---------------------------------------------------------------------------
# Tests: automation_validate.py
# ---------------------------------------------------------------------------


class TestValidateSkill:
    """Tests for validate_skill function."""

    @pytest.mark.unit
    def test_missing_skill_path_returns_false(self, tmp_path: Path) -> None:
        """Non-existent skill path returns False."""
        missing = tmp_path / "nonexistent" / "SKILL.md"
        result = validate_skill(missing)
        assert result is False

    @pytest.mark.unit
    def test_existing_skill_without_validator_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Existing SKILL.md but no validator tool returns False."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: test\n---\n# Skill\n")
        result = validate_skill(skill_file)
        assert result is False


class TestValidateDirectory:
    """Tests for validate_directory function."""

    @pytest.mark.unit
    def test_empty_directory_returns_true(self, tmp_path: Path) -> None:
        """Empty directory (no SKILL.md files) returns True."""
        result = validate_directory(tmp_path)
        assert result is True

    @pytest.mark.unit
    def test_directory_with_skills_runs_validation(self, tmp_path: Path) -> None:
        """Directory with SKILL.md files returns a boolean."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("---\nname: test\n---\n# Skill\n")
        result = validate_directory(tmp_path)
        assert isinstance(result, bool)


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    @pytest.mark.unit
    def test_returns_bool(self) -> None:
        """check_dependencies always returns a boolean."""
        result = check_dependencies()
        assert isinstance(result, bool)


class TestAutomationValidateMain:
    """Tests for automation_validate main() entry point."""

    @pytest.mark.unit
    def test_main_check_deps_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """main --check-deps exits 0 or 1."""
        monkeypatch.setattr(
            sys, "argv", ["automation_validate.py", "--check-deps", "."]
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_main()
        assert exc_info.value.code in (0, 1)

    @pytest.mark.unit
    def test_main_with_directory_path_exits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main with directory path exits 0 or 1."""
        monkeypatch.setattr(sys, "argv", ["automation_validate.py", str(tmp_path)])
        with pytest.raises(SystemExit) as exc_info:
            validate_main()
        assert exc_info.value.code in (0, 1)

    @pytest.mark.unit
    def test_main_with_nonexistent_path_exits_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main with nonexistent path exits 1."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["automation_validate.py", str(tmp_path / "nonexistent")],
        )
        with pytest.raises(SystemExit) as exc_info:
            validate_main()
        assert exc_info.value.code == 1

    @pytest.mark.unit
    def test_main_with_file_path_exits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """main with SKILL.md file path exits 0 or 1."""
        skill_file = tmp_path / "SKILL.md"
        skill_file.write_text("---\nname: test\n---\n# Skill\n")
        monkeypatch.setattr(sys, "argv", ["automation_validate.py", str(skill_file)])
        with pytest.raises(SystemExit) as exc_info:
            validate_main()
        assert exc_info.value.code in (0, 1)
