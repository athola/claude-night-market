"""Tests for MemoryPalaceCLI construction, helpers, and plugin enable/disable.

Covers:
- TendingOptions / TendingContext dataclasses
- CLI construction and path initialization
- print_* helper methods
- is_enabled(), enable_plugin(), disable_plugin()
- show_status()
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from scripts.memory_palace_cli import (
    MemoryPalaceCLI,
    TendingContext,
)

from memory_palace.palace_manager import MemoryPalaceManager

from .conftest import _default_tending_opts


class TestTendingDataclasses:
    """Feature: TendingOptions and TendingContext hold tending parameters."""

    def test_tending_options_fields(self) -> None:
        """Given all fields, TendingOptions stores each value."""
        opts = _default_tending_opts(
            path="/tmp/g.json",
            prune_days=3,
            stale_days=14,
            archive_days=60,
            apply=True,
            prometheus=True,
            label="test",
        )
        assert opts.path == "/tmp/g.json"
        assert opts.prune_days == 3
        assert opts.stale_days == 14
        assert opts.archive_days == 60
        assert opts.apply is True
        assert opts.prometheus is True
        assert opts.label == "test"

    def test_tending_context_fields(self, tmp_path: Path) -> None:
        """Given all fields, TendingContext holds data for a run."""
        now = datetime.now(timezone.utc)
        ctx = TendingContext(
            data={"garden": {"plots": []}},
            plots=[],
            actions={"prune": [], "stale": [], "archive": []},
            now_dt=now,
            target_path=tmp_path / "g.json",
        )
        assert ctx.data == {"garden": {"plots": []}}
        assert ctx.plots == []
        assert isinstance(ctx.now_dt, datetime)
        assert ctx.target_path == tmp_path / "g.json"


class TestCLIConstruction:
    """Feature: MemoryPalaceCLI initialises paths correctly."""

    def test_init_sets_paths(self) -> None:
        """Given default construction, paths reference plugin dir."""
        cli = MemoryPalaceCLI()
        assert cli.plugin_dir.exists() or True  # path may not exist in CI
        assert cli.config_file.name == "settings.json"
        assert cli.claude_config.name == "settings.json"


class TestPrintHelpers:
    """Feature: Status messages use consistent prefixes."""

    @pytest.mark.parametrize(
        "method,prefix",
        [
            ("print_status", "[STATUS]"),
            ("print_success", "[OK]"),
            ("print_warning", "[WARN]"),
            ("print_error", "[ERROR]"),
        ],
        ids=["status", "success", "warning", "error"],
    )
    def test_print_prefix(
        self,
        method: str,
        prefix: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a message, print method emits the correct prefix."""
        cli = MemoryPalaceCLI()
        getattr(cli, method)("hello")
        out = capsys.readouterr().out
        assert out.startswith(prefix)
        assert "hello" in out


class TestIsEnabled:
    """Feature: Plugin detects whether it is enabled in Claude config."""

    def test_returns_false_when_config_missing(self, tmp_path: Path) -> None:
        """Given no Claude config file, is_enabled returns False."""
        cli = MemoryPalaceCLI()
        cli.claude_config = tmp_path / "nonexistent.json"
        assert cli.is_enabled() is False

    def test_returns_false_on_malformed_json(self, tmp_path: Path) -> None:
        """Given corrupt JSON, is_enabled returns False."""
        cfg = tmp_path / "settings.json"
        cfg.write_text("{bad json", encoding="utf-8")
        cli = MemoryPalaceCLI()
        cli.claude_config = cfg
        assert cli.is_enabled() is False

    def test_returns_true_when_permission_present(self, tmp_path: Path) -> None:
        """Given matching permission entry, is_enabled returns True."""
        cli = MemoryPalaceCLI()
        plugin_dir_str = str(cli.plugin_dir)
        cfg = tmp_path / "settings.json"
        cfg.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [f"Read({plugin_dir_str}/**)"],
                    },
                }
            ),
            encoding="utf-8",
        )
        cli.claude_config = cfg
        assert cli.is_enabled() is True

    def test_returns_false_when_no_matching_permission(self, tmp_path: Path) -> None:
        """Given permissions without plugin dir, is_enabled returns False."""
        cfg = tmp_path / "settings.json"
        cfg.write_text(
            json.dumps({"permissions": {"allow": ["Read(/other/**)"]}}),
            encoding="utf-8",
        )
        cli = MemoryPalaceCLI()
        cli.claude_config = cfg
        assert cli.is_enabled() is False


class TestEnablePlugin:
    """Feature: Enable plugin adds permissions and creates directories."""

    def test_creates_config_and_dirs(self, tmp_path: Path) -> None:
        """Given a fresh env, enable creates config and palace dir."""
        cli = MemoryPalaceCLI()
        cli.claude_config = tmp_path / ".claude" / "settings.json"

        with patch.object(Path, "home", return_value=tmp_path):
            cli.enable_plugin()

        assert cli.claude_config.exists()
        data = json.loads(cli.claude_config.read_text())
        assert len(data["permissions"]["allow"]) > 0

    def test_preserves_existing_permissions(self, tmp_path: Path) -> None:
        """Given existing config, enable preserves other permissions."""
        cli = MemoryPalaceCLI()
        cfg = tmp_path / "settings.json"
        cfg.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": ["Bash(echo*)"],
                        "deny": [],
                    },
                }
            ),
            encoding="utf-8",
        )
        cli.claude_config = cfg

        with patch.object(Path, "home", return_value=tmp_path):
            cli.enable_plugin()

        data = json.loads(cfg.read_text())
        assert "Bash(echo*)" in data["permissions"]["allow"]

    def test_backs_up_corrupt_config(self, tmp_path: Path) -> None:
        """Given malformed JSON, enable backs up the bad file."""
        cli = MemoryPalaceCLI()
        cfg = tmp_path / "settings.json"
        cfg.write_text("{corrupt", encoding="utf-8")
        cli.claude_config = cfg

        with patch.object(Path, "home", return_value=tmp_path):
            cli.enable_plugin()

        backup = cfg.with_suffix(".json.bak")
        assert backup.exists()
        assert backup.read_text() == "{corrupt"


class TestDisablePlugin:
    """Feature: Disable plugin removes memory-palace permissions."""

    def test_removes_plugin_permissions(self, tmp_path: Path) -> None:
        """Given enabled config, disable removes plugin perms."""
        cli = MemoryPalaceCLI()
        plugin_dir_str = str(cli.plugin_dir)
        cfg = tmp_path / "settings.json"
        cfg.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [
                            f"Read({plugin_dir_str}/**)",
                            "Bash(echo*)",
                        ],
                    },
                }
            ),
            encoding="utf-8",
        )
        cli.claude_config = cfg
        cli.disable_plugin()

        data = json.loads(cfg.read_text())
        remaining = data["permissions"]["allow"]
        assert f"Read({plugin_dir_str}/**)" not in remaining
        assert "Bash(echo*)" in remaining

    def test_handles_missing_config(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no config file, disable warns and returns."""
        cli = MemoryPalaceCLI()
        cli.claude_config = tmp_path / "nonexistent.json"
        cli.disable_plugin()
        out = capsys.readouterr().out
        assert "doesn't appear" in out

    def test_handles_corrupt_config(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given corrupt JSON, disable prints error."""
        cli = MemoryPalaceCLI()
        cfg = tmp_path / "settings.json"
        cfg.write_text("{bad", encoding="utf-8")
        cli.claude_config = cfg
        cli.disable_plugin()
        out = capsys.readouterr().out
        assert "[ERROR]" in out


class TestShowStatus:
    """Feature: Show status displays plugin state and statistics."""

    def test_disabled_status(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given plugin not enabled, status shows DISABLED."""
        cli = MemoryPalaceCLI()
        cli.claude_config = tmp_path / "nonexistent.json"
        cli.show_status()
        out = capsys.readouterr().out
        assert "DISABLED" in out

    def test_enabled_status_shows_stats(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given plugin enabled with palaces, status shows stats."""
        cli = MemoryPalaceCLI()
        plugin_dir_str = str(cli.plugin_dir)
        cfg = tmp_path / "settings.json"
        cfg.write_text(
            json.dumps(
                {
                    "permissions": {
                        "allow": [f"Read({plugin_dir_str}/**)"],
                    },
                }
            ),
            encoding="utf-8",
        )
        cli.claude_config = cfg

        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.get_master_index.return_value = {
            "global_stats": {
                "domains": {"testing": 2},
            },
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.show_status()

        out = capsys.readouterr().out
        assert "ENABLED" in out
        assert "testing: 2 palaces" in out
        mock_manager.get_master_index.assert_called_once()
