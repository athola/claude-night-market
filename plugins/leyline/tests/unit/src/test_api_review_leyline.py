"""Regression tests for API-review findings in leyline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from leyline import git_platform
from leyline.deferred_capture import find_duplicate
from leyline.frontmatter import parse_frontmatter
from leyline.git_platform import GhCommandError, gh_api
from unittest.mock import patch
import leyline
import subprocess

from leyline.session_store import SessionStore


class _DictStore(SessionStore):
    def _serialize(self, record: Any) -> dict:
        return dict(record)

    def _deserialize(self, data: dict) -> Any:
        return data


def test_load_rejects_path_traversal_session_id(tmp_path: Path) -> None:
    (tmp_path / "outside.json").write_text('{"secret": 1}', encoding="utf-8")
    store = _DictStore(tmp_path / "sessions")
    with pytest.raises(ValueError):
        store.load("../outside")


def test_delete_rejects_path_traversal_session_id(tmp_path: Path) -> None:
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    store = _DictStore(tmp_path / "sessions")
    with pytest.raises(ValueError):
        store.delete("../outside")
    assert outside.exists()


@pytest.mark.parametrize("content", ["---\nfoo\n---\nx", "---\n- a\n---\nx"])
def test_parse_frontmatter_returns_none_for_non_mapping_yaml(content: str) -> None:
    pytest.importorskip("yaml")

    assert parse_frontmatter(content) is None


def test_gh_api_wraps_missing_gh_binary_in_gh_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    monkeypatch.setenv("PATH", "/nonexistent")
    with pytest.raises(GhCommandError):
        gh_api("repos/x/y")


def test_gh_api_wraps_timeout_in_gh_command_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _timeout(*args: Any, **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(cmd="gh", timeout=1)

    monkeypatch.setattr(git_platform.subprocess, "run", _timeout)
    with pytest.raises(git_platform.GhCommandError):
        git_platform.gh_api("repos/x/y")


def test_find_duplicate_raises_when_gh_issue_list_fails() -> None:

    failed = subprocess.CompletedProcess(
        args=[], returncode=1, stdout="", stderr="auth required"
    )
    with patch("leyline.deferred_capture.subprocess.run", return_value=failed):
        with pytest.raises(RuntimeError, match="auth required"):
            find_duplicate("Add OAuth")


def test_find_duplicate_error_names_the_exit_code_when_stderr_is_empty() -> None:

    failed = subprocess.CompletedProcess(args=[], returncode=4, stdout="", stderr="")
    with patch("leyline.deferred_capture.subprocess.run", return_value=failed):
        with pytest.raises(RuntimeError, match="exit 4"):
            find_duplicate("Add OAuth")


def test_find_duplicate_raises_when_gh_returns_invalid_json() -> None:

    garbled = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="not json", stderr=""
    )
    with patch("leyline.deferred_capture.subprocess.run", return_value=garbled):
        with pytest.raises(RuntimeError):
            find_duplicate("Add OAuth")


def test_quota_status_is_not_advertised_in_public_all() -> None:

    assert "QuotaStatus" not in leyline.__all__
