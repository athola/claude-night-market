"""CLI contract for scripts/check-markdown-links.py, the pre-commit link hook.

The hook passes staged markdown paths as arguments and blocks the commit on
exit 1. These tests run the script the way the hook does: as a process, from
inside a repository, with file arguments.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-markdown-links.py"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    (tmp_path / "target.md").write_text("# Target\n\n## Real Section\n")
    return tmp_path


def _check(repo: Path, *files: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *files],
        capture_output=True,
        text=True,
        cwd=repo,
        timeout=30,
        check=False,
    )


@pytest.mark.unit
def test_valid_links_and_anchors_exit_zero(repo: Path) -> None:
    """A link to an existing file and heading passes."""
    (repo / "doc.md").write_text(
        "# Doc\n\nSee [t](target.md) and [s](target.md#real-section).\n"
    )

    result = _check(repo, "doc.md")

    assert result.returncode == 0, result.stdout
    assert "Checked 1 markdown file(s), no broken links found" in result.stdout


@pytest.mark.unit
def test_missing_file_and_missing_anchor_exit_one(repo: Path) -> None:
    """Each broken target is reported with its file and line."""
    (repo / "doc.md").write_text(
        "# Doc\n\n[gone](missing.md)\n\n[bad](target.md#no-such-heading)\n"
    )

    result = _check(repo, "doc.md")

    assert result.returncode == 1
    assert "doc.md:3: broken link to missing.md" in result.stdout
    assert "doc.md:5: broken anchor #no-such-heading in target.md" in result.stdout
    assert "2 broken link(s) found" in result.stdout


@pytest.mark.unit
def test_non_markdown_arguments_are_ignored(repo: Path) -> None:
    """The hook filters on .md, and the script skips anything else it is given."""
    (repo / "notes.txt").write_text("[gone](missing.md)\n")

    result = _check(repo, "notes.txt")

    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.unit
def test_missing_modules_link_exits_one(repo: Path) -> None:
    """A ./modules/ link to a file that does not exist fails (#831)."""
    (repo / "doc.md").write_text("# Doc\n\n[m](./modules/gone.md)\n")

    result = _check(repo, "doc.md")

    assert result.returncode == 1
    assert "doc.md:3: broken link to ./modules/gone.md" in result.stdout


@pytest.mark.unit
def test_link_inside_inline_code_is_not_checked(repo: Path) -> None:
    """Link syntax quoted in inline code is an example, not a link."""
    (repo / "doc.md").write_text("# Doc\n\nWrite `[link](./modules/foo.md)`.\n")

    result = _check(repo, "doc.md")

    assert result.returncode == 0, result.stdout
