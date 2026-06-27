"""TDD tests for EGR-001: herald path via env var config lookup."""

from __future__ import annotations

from pathlib import Path

from notify import (  # type: ignore[import-not-found] - pytest pythonpath adds scripts/ to sys.path
    _find_herald_notify_path,
)


class TestFindHeraldNotifyPath:
    """Tests for _find_herald_notify_path function (EGR-001)."""

    def test_function_exists(self) -> None:
        """_find_herald_notify_path must be importable from notify."""
        assert callable(_find_herald_notify_path)

    def test_returns_env_var_path_when_set(self, monkeypatch, tmp_path) -> None:
        """When HERALD_NOTIFY_PATH is set, function returns that path."""
        custom_path = str(tmp_path / "custom_notify.py")
        monkeypatch.setenv("HERALD_NOTIFY_PATH", custom_path)

        result = _find_herald_notify_path()
        assert str(result) == custom_path

    def test_returns_path_object(self, monkeypatch) -> None:
        """Return type is always Path, not str."""
        monkeypatch.delenv("HERALD_NOTIFY_PATH", raising=False)

        result = _find_herald_notify_path()
        assert isinstance(result, Path)

    def test_falls_back_to_relative_path_when_env_unset(self, monkeypatch) -> None:
        """When HERALD_NOTIFY_PATH is unset, falls back to the repo-relative path."""
        monkeypatch.delenv("HERALD_NOTIFY_PATH", raising=False)

        result = _find_herald_notify_path()
        assert result.name == "notify.py"
        assert "herald" in result.parts
