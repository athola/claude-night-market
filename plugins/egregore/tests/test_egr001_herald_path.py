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

    def test_finds_herald_in_the_installed_plugin_cache(
        self, monkeypatch, tmp_path
    ) -> None:
        """Installed plugins sit at cache/<market>/<plugin>/<version>/.

        Three parents up from scripts/ is cache/<market>/egregore there, so
        a fixed repo-relative path never found an installed herald.
        """
        monkeypatch.delenv("HERALD_NOTIFY_PATH", raising=False)
        market = tmp_path / "cache" / "market"
        egregore_notify = market / "egregore" / "1.10.0" / "scripts" / "notify.py"
        herald_notify = market / "herald" / "1.10.0" / "scripts" / "notify.py"
        for path in (egregore_notify, herald_notify):
            path.parent.mkdir(parents=True)
            path.write_text("")
            (path.parents[1] / ".claude-plugin").mkdir()

        assert _find_herald_notify_path(egregore_notify) == herald_notify
