"""Regression tests for the attune low findings of the Tier 3 review."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from attune_upgrade import ProjectUpgrader
from attune_upgrade import main as upgrade_main
from sync_templates import TemplateSynchronizer

# conftest.py puts scripts/ on sys.path.
SCRIPTS = Path(__file__).parent.parent / "scripts"


def _run_upgrade_main(path: Path, *flags: str) -> Mock:
    upgrader = Mock()
    upgrader.upgrade.return_value = []
    detector = Mock()
    detector.detect_language.return_value = "python"
    with (
        patch("attune_upgrade.ProjectUpgrader", return_value=upgrader),
        patch("attune_upgrade.ProjectDetector", return_value=detector),
        patch("sys.argv", ["attune_upgrade.py", "--path", str(path), *flags]),
    ):
        upgrade_main()
    return upgrader


@pytest.mark.unit
def test_force_upgrade_does_not_prompt(tmp_path: Path) -> None:
    """`--force` is documented as "without prompting" (ATN-3)."""
    with patch("builtins.input", side_effect=AssertionError("prompted")):
        upgrader = _run_upgrade_main(tmp_path, "--force")
    upgrader.upgrade.assert_called_once()


@pytest.mark.unit
def test_closed_stdin_cancels_the_upgrade(tmp_path: Path) -> None:
    """`input()` on closed stdin raised an uncaught EOFError (ATN-3)."""
    with (
        patch("builtins.input", side_effect=EOFError),
        pytest.raises(SystemExit) as exit_info,
    ):
        _run_upgrade_main(tmp_path)
    assert exit_info.value.code == 0


@pytest.mark.unit
def test_infer_variables_reads_author_from_authors_table(tmp_path: Path) -> None:
    """The regex took the first `name =`, the project's own (ATN-4)."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "widget"\n'
        'authors = [{ name = "Ada Lovelace", email = "ada@example.com" }]\n'
    )
    variables = ProjectUpgrader(tmp_path, "python")._infer_variables()
    assert variables["AUTHOR"] == "Ada Lovelace"


@pytest.mark.unit
@pytest.mark.parametrize("name", ["x; touch pwned", "a$(id)", "-rf", "a b"])
def test_init_rejects_project_name_with_shell_metacharacters(
    tmp_path: Path, name: str
) -> None:
    """The name is written verbatim into Makefile recipes (ATN-5)."""
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "attune_init.py"),
            "--path",
            str(tmp_path),
            "--lang",
            "python",
            "--name",
            name,
        ],
        capture_output=True,
        text=True,
        input="",
        check=False,
    )
    assert result.returncode != 0
    assert not (tmp_path / "Makefile").exists()


@pytest.mark.unit
def test_extract_template_variables_only_rewrites_package_name(tmp_path: Path) -> None:
    """Every `name =` became the project placeholder, `[[bin]]` too (ATN-6)."""
    cargo = '[package]\nname = "skrills"\n\n[[bin]]\nname = "skrills-cli"\n'
    out = TemplateSynchronizer(tmp_path).extract_template_variables(cargo, "rust")
    assert out.count("{{PROJECT_NAME}}") == 1
    assert 'name = "skrills-cli"' in out


@pytest.mark.unit
def test_invalid_directory_name_points_at_the_name_flag(tmp_path: Path) -> None:
    """A directory like `my project` now fails; say how to proceed (ATN-5)."""
    project = tmp_path / "my project"
    project.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "attune_init.py"),
            "--path",
            str(project),
            "--lang",
            "python",
        ],
        capture_output=True,
        text=True,
        input="",
        check=False,
    )
    assert result.returncode != 0
    assert "--name" in result.stderr
