"""Attune init and upgrade must touch only what their flags say they touch.

Each test pins one defect found by a bug review: a preview that wrote to
disk, an upgrade that overwrote or removed the user's own files, and a git
failure that raised instead of reporting.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import attune_init
import attune_upgrade
from attune_init import initialize_git
from attune_upgrade import ProjectUpgrader

USER_PYPROJECT = '[project]\nname = "mine"\nrequires-python = ">=3.11"\n# keep me\n'


@pytest.fixture
def python_project_with_user_pyproject(tmp_path: Path) -> Path:
    """A project holding a pyproject.toml the user wrote by hand."""
    (tmp_path / "pyproject.toml").write_text(USER_PYPROJECT)
    return tmp_path


class TestInitDryRun:
    """Dry run previews every step, git included."""

    def test_dry_run_does_not_create_a_git_repository(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dry run leaves the target directory empty."""
        monkeypatch.setattr(
            sys,
            "argv",
            ["attune_init", "--lang", "python", "--path", str(tmp_path), "--dry-run"],
        )

        attune_init.main()

        assert not (tmp_path / ".git").exists()
        assert list(tmp_path.iterdir()) == []


class TestInitializeGitFailures:
    """A git that cannot run is reported, not raised."""

    def test_missing_git_binary_returns_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No git on PATH gives False."""

        def no_git(*args: object, **kwargs: object) -> None:
            raise FileNotFoundError("git")

        monkeypatch.setattr(subprocess, "run", no_git)

        assert initialize_git(tmp_path) is False

    def test_hung_git_returns_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A git that times out gives False."""

        def hung(*args: object, **kwargs: object) -> None:
            raise subprocess.TimeoutExpired(cmd="git init", timeout=30)

        monkeypatch.setattr(subprocess, "run", hung)

        assert initialize_git(tmp_path) is False


class TestUpgradeLeavesExistingFilesAlone:
    """Upgrade adds missing files and leaves present ones as they are."""

    def test_force_does_not_overwrite_a_file_that_already_exists(
        self, python_project_with_user_pyproject: Path
    ) -> None:
        """--force overwrites nothing that exists."""
        project = python_project_with_user_pyproject
        upgrader = ProjectUpgrader(project, "python")

        upgrader.upgrade(force=True)

        assert (project / "pyproject.toml").read_text() == USER_PYPROJECT
        assert (project / "Makefile").exists()

    def test_component_limits_what_is_added(
        self, python_project_with_user_pyproject: Path
    ) -> None:
        """--component limits which missing files are added."""
        project = python_project_with_user_pyproject
        upgrader = ProjectUpgrader(project, "python")

        added = upgrader.upgrade(component="gitignore", force=True)

        assert (project / ".gitignore").exists()
        assert not (project / "Makefile").exists()
        assert [Path(path).name for path in added] == [".gitignore"]


class TestUpgradeUpdateOutdated:
    """--update replaces an outdated file and keeps a backup."""

    def test_updating_an_outdated_makefile_leaves_a_makefile_and_a_backup(
        self, python_project_with_user_pyproject: Path
    ) -> None:
        """The old Makefile is backed up and a new one is written."""
        project = python_project_with_user_pyproject
        outdated = "all:\n\techo old\n"
        (project / "Makefile").write_text(outdated)
        upgrader = ProjectUpgrader(project, "python")

        affected = upgrader.upgrade(
            component="makefile", force=True, update_outdated=True
        )

        assert "## Show this help" in (project / "Makefile").read_text()
        assert (project / "Makefile.bak").read_text() == outdated
        assert "Makefile" in affected

    def test_workflow_without_a_template_is_not_removed(
        self, python_project_with_user_pyproject: Path
    ) -> None:
        """A file with no template stays where it is."""
        project = python_project_with_user_pyproject
        workflows = project / ".github" / "workflows"
        workflows.mkdir(parents=True)
        custom = workflows / "release.yml"
        custom.write_text("uses: actions/checkout@v3\n")
        upgrader = ProjectUpgrader(project, "python")

        affected = upgrader.upgrade(
            component="workflows", force=True, update_outdated=True
        )

        assert custom.read_text() == "uses: actions/checkout@v3\n"
        assert ".github/workflows/release.yml" not in affected

    def test_render_failure_leaves_the_outdated_file_in_place(
        self,
        python_project_with_user_pyproject: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A template that fails to render must not leave only a .bak behind."""
        project = python_project_with_user_pyproject
        outdated = "all:\n\techo old\n"
        (project / "Makefile").write_text(outdated)
        upgrader = ProjectUpgrader(project, "python")
        real_copy = attune_upgrade.copy_templates

        def fail_on_makefile(**kwargs: object) -> list[str]:
            if kwargs.get("only_paths") == {"Makefile"}:
                raise KeyError("missing template variable")
            return real_copy(**kwargs)

        monkeypatch.setattr(attune_upgrade, "copy_templates", fail_on_makefile)

        with pytest.raises(KeyError):
            upgrader.upgrade(component="makefile", force=True, update_outdated=True)

        assert (project / "Makefile").read_text() == outdated

    def test_second_update_keeps_the_first_backup(
        self, python_project_with_user_pyproject: Path
    ) -> None:
        """An existing Makefile.bak is not replaced by a later backup."""
        project = python_project_with_user_pyproject
        (project / "Makefile.bak").write_text("first backup\n")
        outdated = "all:\n\techo old\n"
        (project / "Makefile").write_text(outdated)
        upgrader = ProjectUpgrader(project, "python")

        upgrader.upgrade(component="makefile", force=True, update_outdated=True)

        assert (project / "Makefile.bak").read_text() == "first backup\n"
        later = list(project.glob("Makefile.bak.*"))
        assert [p.read_text() for p in later] == [outdated]
