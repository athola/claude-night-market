"""Project directories are named by replacing every non-alphanumeric character."""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))

from context_warning import _resolve_project_dir

from shared.session_file import project_dir_name, resolve_session_file


def _claude_dir_name(cwd: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


@pytest.fixture
def dotted_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cwd = tmp_path / "first.last" / "my_repo"
    cwd.mkdir(parents=True)
    monkeypatch.chdir(cwd)
    return Path.cwd()


def test_resolve_project_dir_matches_dir_for_cwd_with_dots(
    tmp_path: Path, dotted_cwd: Path
) -> None:
    projects = tmp_path / "projects"
    expected = projects / _claude_dir_name(dotted_cwd)
    expected.mkdir(parents=True)

    assert _resolve_project_dir(dotted_cwd, projects) == expected


def test_resolve_session_file_picks_project_dir_for_cwd_with_dots(
    tmp_path: Path, dotted_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude_home = tmp_path / "claude_home"
    projects = claude_home / "projects"
    mine = projects / _claude_dir_name(dotted_cwd)
    mine.mkdir(parents=True)
    (mine / "mine.jsonl").write_text("{}\n")
    other = projects / "-zzz-newer-project"
    other.mkdir()
    (other / "other.jsonl").write_text("{}\n")
    # Make `other` strictly newer so the most-recent-dir fallback would pick
    # it. Equal mtimes would let a broken name match pass by sort order.
    now = time.time()
    os.utime(mine, (now - 60, now - 60))
    os.utime(other, (now, now))
    monkeypatch.setenv("CLAUDE_HOME", str(claude_home))
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    assert resolve_session_file() == mine / "mine.jsonl"


def test_an_unmatched_session_id_falls_back_to_the_newest_transcript(
    tmp_path: Path, dotted_cwd: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    claude_home = tmp_path / "claude_home"
    mine = claude_home / "projects" / _claude_dir_name(dotted_cwd)
    mine.mkdir(parents=True)
    older = mine / "older.jsonl"
    newer = mine / "newer.jsonl"
    for path in (older, newer):
        path.write_text("{}\n")
    now = time.time()
    os.utime(older, (now - 60, now - 60))
    os.utime(newer, (now, now))
    monkeypatch.setenv("CLAUDE_HOME", str(claude_home))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "no-such-session")

    assert resolve_session_file() == newer


@pytest.mark.parametrize(
    ("cwd", "expected"),
    [
        ("/Users/a.b/my_repo", "-Users-a-b-my-repo"),
        ("C:\\work\\repo", "-C--work-repo"),
    ],
)
def test_project_dir_name_maps_every_non_alphanumeric_to_a_dash(
    cwd: str, expected: str
) -> None:
    assert project_dir_name(Path(cwd)) == expected
