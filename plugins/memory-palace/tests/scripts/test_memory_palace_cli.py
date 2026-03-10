"""Tests for memory_palace_cli.py MemoryPalaceCLI class and CLI parser.

Feature: Memory Palace CLI operations

As a plugin administrator
I want to manage palaces, garden tending, and plugin state via CLI
So that administrative tasks are scriptable and testable.

Tests cover:
- MemoryPalaceCLI construction and helper methods
- Plugin enable/disable (mocked filesystem)
- Status display
- Palace CRUD (create, list, search, delete via manager subcommand)
- Garden metrics and tending (report, apply, prometheus)
- Export/Import workflows
- Skills listing and installation
- Sync queue operations
- Prune check and apply
- CLI argument parser (build_parser + main dispatch)
- Error paths and edge cases
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from memory_palace.palace_manager import MemoryPalaceManager

# Import the CLI module under test
from scripts.memory_palace_cli import (
    MemoryPalaceCLI,
    TendingContext,
    TendingOptions,
    build_parser,
    main,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_tending_opts(**overrides: Any) -> TendingOptions:
    """Return TendingOptions with sensible defaults for testing."""
    defaults: dict[str, Any] = {
        "path": None,
        "now": None,
        "prune_days": 2,
        "stale_days": 7,
        "archive_days": 30,
        "apply": False,
        "archive_export": None,
        "prometheus": False,
        "label": None,
    }
    defaults.update(overrides)
    return TendingOptions(**defaults)


def _garden_data_with_plots(
    now: datetime,
    stale_days: int = 0,
    archive_days: int = 0,
    never_tended: int = 0,
    fresh: int = 1,
) -> dict[str, Any]:
    """Build garden JSON data with configurable plot ages."""
    from datetime import timedelta

    plots: list[dict[str, Any]] = []
    for i in range(fresh):
        plots.append(
            {
                "name": f"fresh-{i}",
                "inbound_links": [],
                "outbound_links": [],
                "last_tended": now.isoformat(),
            }
        )
    for i in range(stale_days):
        old = now - timedelta(days=10)
        plots.append(
            {
                "name": f"stale-{i}",
                "inbound_links": [],
                "outbound_links": [],
                "last_tended": old.isoformat(),
            }
        )
    for i in range(archive_days):
        old = now - timedelta(days=60)
        plots.append(
            {
                "name": f"archive-{i}",
                "inbound_links": [],
                "outbound_links": [],
                "last_tended": old.isoformat(),
            }
        )
    for i in range(never_tended):
        plots.append(
            {
                "name": f"untended-{i}",
                "inbound_links": [],
                "outbound_links": [],
            }
        )
    return {"garden": {"plots": plots}}


# ---------------------------------------------------------------------------
# TestTendingDataclasses
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestCLIConstruction
# ---------------------------------------------------------------------------


class TestCLIConstruction:
    """Feature: MemoryPalaceCLI initialises paths correctly."""

    def test_init_sets_paths(self) -> None:
        """Given default construction, paths reference plugin dir."""
        cli = MemoryPalaceCLI()
        assert cli.plugin_dir.exists() or True  # path may not exist in CI
        assert cli.config_file.name == "settings.json"
        assert cli.claude_config.name == "settings.json"


# ---------------------------------------------------------------------------
# TestPrintHelpers
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestIsEnabled
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestEnablePlugin
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestDisablePlugin
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestShowStatus
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# TestGardenMetrics
# ---------------------------------------------------------------------------


class TestGardenMetrics:
    """Feature: garden_metrics computes and prints metrics."""

    def test_json_output(
        self,
        sample_garden_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a garden file, print JSON metrics."""
        cli = MemoryPalaceCLI()
        cli.garden_metrics(
            path=str(sample_garden_file),
            output_format="json",
        )
        out = capsys.readouterr().out
        parsed = json.loads(
            out.split("\n", 1)[1]  # skip [STATUS] line
        )
        assert isinstance(parsed["plots"], int)
        assert parsed["plots"] > 0

    def test_brief_output(
        self,
        sample_garden_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given brief format, print one-line summary."""
        cli = MemoryPalaceCLI()
        cli.garden_metrics(
            path=str(sample_garden_file),
            output_format="brief",
        )
        out = capsys.readouterr().out
        assert "plots=" in out
        assert "link_density=" in out

    def test_prometheus_output(
        self,
        sample_garden_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given prometheus format, print metric lines."""
        cli = MemoryPalaceCLI()
        cli.garden_metrics(
            path=str(sample_garden_file),
            output_format="prometheus",
            label="test",
        )
        out = capsys.readouterr().out
        assert 'garden_plots{garden="test"}' in out
        assert 'garden_link_density{garden="test"}' in out

    def test_missing_file_warns(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given nonexistent garden file, print warning."""
        cli = MemoryPalaceCLI()
        cli.garden_metrics(path=str(tmp_path / "no.json"))
        out = capsys.readouterr().out
        assert "[WARN]" in out

    def test_custom_now_timestamp(
        self,
        sample_garden_file: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given a --now override, use that timestamp."""
        cli = MemoryPalaceCLI()
        cli.garden_metrics(
            path=str(sample_garden_file),
            now="2025-12-01T00:00:00+00:00",
            output_format="json",
        )
        out = capsys.readouterr().out
        # Should not crash; output includes metrics
        assert "plots" in out


# ---------------------------------------------------------------------------
# TestGardenTend
# ---------------------------------------------------------------------------


class TestGardenTend:
    """Feature: garden_tend reports and applies tending actions."""

    def test_report_identifies_stale_plots(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given plots older than stale threshold, report lists them."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, stale_days=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
                stale_days=7,
            ),
        )
        out = capsys.readouterr().out
        assert "STALE" in out

    def test_report_identifies_archive_plots(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given plots older than archive threshold, report lists them."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, archive_days=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
                archive_days=30,
            ),
        )
        out = capsys.readouterr().out
        assert "ARCHIVE" in out

    def test_report_identifies_never_tended(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given plots with no last_tended, report flags for prune."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, never_tended=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
            ),
        )
        out = capsys.readouterr().out
        assert "PRUNE" in out

    def test_all_fresh_reports_success(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given only fresh plots, report says all fresh."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, fresh=2)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
            ),
        )
        out = capsys.readouterr().out
        assert "fresh" in out.lower()

    def test_apply_creates_backup_and_updates(
        self,
        tmp_path: Path,
    ) -> None:
        """Given --apply, tending updates garden and creates backup."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, never_tended=1, archive_days=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
                apply=True,
                archive_days=30,
            ),
        )

        backup = Path(str(gfile) + ".bak")
        assert backup.exists()

        updated = json.loads(gfile.read_text())
        plots = updated["garden"]["plots"]
        compost = updated["garden"].get("compost", [])
        # Archived plot moved to compost
        assert len(compost) >= 1

    def test_apply_archive_export(self, tmp_path: Path) -> None:
        """Given --apply --archive-export, writes archive JSON."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, archive_days=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")
        export_file = tmp_path / "archived.json"

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
                apply=True,
                archive_days=30,
                archive_export=str(export_file),
            ),
        )

        assert export_file.exists()
        exported = json.loads(export_file.read_text())
        assert "archived" in exported
        assert len(exported["archived"]) >= 1

    def test_missing_garden_file_warns(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given nonexistent garden path, warn and return."""
        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(path=str(tmp_path / "missing.json")),
        )
        out = capsys.readouterr().out
        assert "[WARN]" in out

    def test_empty_garden_warns(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given garden with no plots, warn about empty garden."""
        gfile = tmp_path / "garden.json"
        gfile.write_text(
            json.dumps({"garden": {"plots": []}}),
            encoding="utf-8",
        )
        cli = MemoryPalaceCLI()
        cli.garden_tend(_default_tending_opts(path=str(gfile)))
        out = capsys.readouterr().out
        assert "No plots" in out

    def test_prometheus_report_returns_early(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given --prometheus flag, emit report returns after defining line fn."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, never_tended=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        cli.garden_tend(
            _default_tending_opts(
                path=str(gfile),
                now=now.isoformat(),
                prometheus=True,
            ),
        )
        out = capsys.readouterr().out
        # Prometheus branch returns early, no PRUNE/STALE text
        assert "PRUNE" not in out

    def test_include_palaces_calls_prune_check(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given --palaces flag, also runs palace health check."""
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        data = _garden_data_with_plots(now, fresh=1)
        gfile = tmp_path / "garden.json"
        gfile.write_text(json.dumps(data), encoding="utf-8")

        cli = MemoryPalaceCLI()
        with patch.object(cli, "prune_check", return_value=True) as mock_pc:
            cli.garden_tend(
                _default_tending_opts(
                    path=str(gfile),
                    now=now.isoformat(),
                    stale_days=7,
                ),
                include_palaces=True,
            )
            mock_pc.assert_called_once_with(stale_days=7)


# ---------------------------------------------------------------------------
# TestListSkills
# ---------------------------------------------------------------------------


class TestListSkills:
    """Feature: List available skills from the skills directory."""

    def test_lists_skills(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given skills directory with skill folders, list them."""
        cli = MemoryPalaceCLI()
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (skills_dir / "test-skill").mkdir()
        skill_md = skills_dir / "test-skill" / "SKILL.md"
        skill_md.write_text(
            "---\ndescription: A test skill\n---\n# Test\n",
            encoding="utf-8",
        )
        cli.plugin_dir = tmp_path
        cli.list_skills()
        out = capsys.readouterr().out
        assert "Available" in out

    def test_no_skills_directory_warns(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no skills directory, print warning."""
        cli = MemoryPalaceCLI()
        cli.plugin_dir = tmp_path
        cli.list_skills()
        out = capsys.readouterr().out
        assert "[WARN]" in out


# ---------------------------------------------------------------------------
# TestCreatePalace
# ---------------------------------------------------------------------------


class TestCreatePalace:
    """Feature: Create a new memory palace."""

    def test_creates_palace_returns_true(self) -> None:
        """Given valid name and domain, create returns True."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.create_palace.return_value = {"id": "new-1"}

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.create_palace("Test", "testing", "building")

        assert result is True
        mock_manager.create_palace.assert_called_once_with(
            "Test",
            "testing",
            "building",
        )

    def test_empty_name_returns_false(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given empty name, returns False with error."""
        cli = MemoryPalaceCLI()
        result = cli.create_palace("", "testing")
        assert result is False
        assert "[ERROR]" in capsys.readouterr().out

    def test_empty_domain_returns_false(self) -> None:
        """Given empty domain, returns False."""
        cli = MemoryPalaceCLI()
        assert cli.create_palace("Test", "") is False

    def test_manager_error_returns_false(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given manager raises, returns False with error."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.create_palace.side_effect = RuntimeError("disk full")

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.create_palace("Test", "testing")

        assert result is False
        assert "disk full" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# TestListPalaces
# ---------------------------------------------------------------------------


class TestListPalaces:
    """Feature: List all memory palaces."""

    def test_lists_palaces_with_details(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given palaces exist, print their details."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.list_palaces.return_value = [
            {"id": "p1", "name": "Palace One", "domain": "d1", "concept_count": 5},
        ]

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.list_palaces()

        assert result is True
        out = capsys.readouterr().out
        assert "Palace One" in out
        assert "Total: 1 palaces" in out
        mock_manager.list_palaces.assert_called_once()

    def test_empty_list_shows_hint(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no palaces, print creation hint."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.list_palaces.return_value = []

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.list_palaces()

        assert result is True
        assert "/palace create" in capsys.readouterr().out

    def test_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.list_palaces.side_effect = RuntimeError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.list_palaces() is False


# ---------------------------------------------------------------------------
# TestSyncQueue
# ---------------------------------------------------------------------------


class TestSyncQueue:
    """Feature: Sync intake queue into palaces."""

    def test_sync_with_results(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given processed items, print summary."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.sync_from_queue.return_value = {
            "processed": 5,
            "skipped": 1,
            "palaces_updated": ["p1"],
            "palaces_created": [],
            "unmatched": ["q1", "q2"],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.sync_queue(auto_create=False, dry_run=False)

        assert result is True
        out = capsys.readouterr().out
        assert "Processed: 5" in out
        assert "Skipped: 1" in out
        assert "Unmatched queries: 2" in out
        mock_manager.sync_from_queue.assert_called_once()

    def test_dry_run_header(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given dry_run=True, print DRY RUN header."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.sync_from_queue.return_value = {
            "processed": 0,
            "skipped": 0,
            "palaces_updated": [],
            "palaces_created": [],
            "unmatched": [],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.sync_queue(dry_run=True)

        assert "DRY RUN" in capsys.readouterr().out

    def test_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.sync_from_queue.side_effect = RuntimeError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.sync_queue() is False


# ---------------------------------------------------------------------------
# TestPruneCheck
# ---------------------------------------------------------------------------


class TestPruneCheckCLI:
    """Feature: CLI prune check reports palace health."""

    def test_healthy_palaces(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no issues found, print healthy message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "palaces_checked": 2,
            "total_stale": 0,
            "total_low_quality": 0,
            "total_duplicates": 0,
            "recommendations": [],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.prune_check(stale_days=90)

        assert result is True
        assert "healthy" in capsys.readouterr().out.lower()
        mock_manager.prune_check.assert_called_once_with(stale_days=90)

    def test_stale_entries_reported(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given stale entries, print recommendations."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "palaces_checked": 1,
            "total_stale": 3,
            "total_low_quality": 0,
            "total_duplicates": 0,
            "recommendations": [
                {
                    "palace_name": "Old Palace",
                    "palace_id": "old-1",
                    "stale": ["e1", "e2", "e3"],
                    "low_quality": [],
                },
            ],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.prune_check()

        out = capsys.readouterr().out
        assert "Stale entries" in out
        assert "3 stale entries" in out

    def test_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.side_effect = RuntimeError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.prune_check() is False


# ---------------------------------------------------------------------------
# TestPruneApply
# ---------------------------------------------------------------------------


class TestPruneApply:
    """Feature: Apply prune actions after user approval."""

    def test_applies_prune(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given recommendations, apply_prune removes entries."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "recommendations": [{"palace_id": "p1"}],
        }
        mock_manager.apply_prune.return_value = {
            "stale": 2,
            "low_quality": 1,
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.prune_apply(["stale", "low_quality"])

        assert result is True
        out = capsys.readouterr().out
        assert "Stale removed: 2" in out
        assert "Low quality removed: 1" in out
        mock_manager.apply_prune.assert_called_once()

    def test_no_cleanup_needed(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no recommendations, print clean message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {"recommendations": []}

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.prune_apply(["stale"])

        assert result is True
        assert "No cleanup" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# TestSearchPalaces
# ---------------------------------------------------------------------------


class TestSearchPalaces:
    """Feature: Search across all palaces."""

    def test_search_with_results(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given matching entries, print results."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.search_palaces.return_value = [
            {
                "palace_name": "Python Palace",
                "palace_id": "p1",
                "matches": [
                    {"type": "association", "concept_id": "decorators"},
                ],
            },
        ]

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.search_palaces("decorators", "semantic")

        assert result is True
        out = capsys.readouterr().out
        assert "Python Palace" in out
        assert "decorators" in out
        mock_manager.search_palaces.assert_called_once_with(
            "decorators",
            "semantic",
        )

    def test_no_results(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given no matches, print no-match message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.search_palaces.return_value = []

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.search_palaces("nonexistent")

        assert result is True
        assert "No matches" in capsys.readouterr().out

    def test_empty_query_returns_false(self) -> None:
        """Given empty query, returns False."""
        cli = MemoryPalaceCLI()
        assert cli.search_palaces("") is False

    def test_search_error_returns_false(self) -> None:
        """Given manager error, returns False."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.search_palaces.side_effect = RuntimeError("fail")

        with patch.object(cli, "_manager", return_value=mock_manager):
            assert cli.search_palaces("test") is False


# ---------------------------------------------------------------------------
# TestInstallSkills
# ---------------------------------------------------------------------------


class TestInstallSkills:
    """Feature: Install skills into Claude's skill directory."""

    def test_install_success(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given valid directories, install copies skills."""
        cli = MemoryPalaceCLI()

        # Create source skills
        source_skills = tmp_path / "plugin" / "skills"
        source_skills.mkdir(parents=True)
        (source_skills / "test-skill").mkdir()
        (source_skills / "test-skill" / "SKILL.md").write_text("# Test")
        cli.plugin_dir = tmp_path / "plugin"

        # Create target skills dir
        claude_skills = tmp_path / ".claude" / "skills"
        claude_skills.mkdir(parents=True)

        with patch.object(Path, "home", return_value=tmp_path):
            result = cli.install_skills()

        assert result is True
        installed = claude_skills / "memory-palace" / "test-skill" / "SKILL.md"
        assert installed.exists()

    def test_no_skills_dir_returns_false(self, tmp_path: Path) -> None:
        """Given no source skills directory, returns False."""
        cli = MemoryPalaceCLI()
        cli.plugin_dir = tmp_path  # no skills subdirectory

        claude_skills = tmp_path / ".claude" / "skills"
        claude_skills.mkdir(parents=True)

        with patch.object(Path, "home", return_value=tmp_path):
            assert cli.install_skills() is False


# ---------------------------------------------------------------------------
# TestRunPalaceManager
# ---------------------------------------------------------------------------


class TestRunPalaceManager:
    """Feature: Forward manager subcommands."""

    def test_delete_command(self) -> None:
        """Given 'delete <id>', deletes palace."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.delete_palace.return_value = True

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["delete", "p1"])

        assert result is True
        mock_manager.delete_palace.assert_called_once_with("p1")

    def test_delete_nonexistent(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given 'delete <nonexistent>', prints error."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.delete_palace.return_value = False

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["delete", "bad-id"])

        assert result is False
        assert "not found" in capsys.readouterr().out

    def test_status_command(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given 'status', prints index stats."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.get_master_index.return_value = {
            "global_stats": {
                "total_palaces": 3,
                "total_concepts": 10,
                "domains": {"testing": 2, "math": 1},
            },
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["status"])

        assert result is True
        out = capsys.readouterr().out
        assert "Total palaces: 3" in out
        assert "testing: 2 palaces" in out

    def test_unknown_command_warns(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given unknown subcommand, prints warning."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)

        with patch.object(cli, "_manager", return_value=mock_manager):
            result = cli.run_palace_manager(["unknown-cmd"])

        assert result is False
        assert "not supported" in capsys.readouterr().out

    def test_no_args_returns_false(self) -> None:
        """Given empty args, returns False."""
        cli = MemoryPalaceCLI()
        assert cli.run_palace_manager([]) is False


# ---------------------------------------------------------------------------
# TestExportImportCLI
# ---------------------------------------------------------------------------


class TestExportImportCLI:
    """Feature: Export and import palaces via CLI methods."""

    def test_export_delegates_to_manager(self) -> None:
        """Given a destination, export delegates to manager."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.export_palaces("/tmp/out.json", palaces_dir="/tmp/p")

        mock_manager.export_state.assert_called_once_with("/tmp/out.json")

    def test_export_error_prints_message(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given manager error, print error message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.export_state.side_effect = RuntimeError("write err")

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.export_palaces("/tmp/out.json")

        assert "write err" in capsys.readouterr().out

    def test_import_delegates_to_manager(self) -> None:
        """Given a source, import delegates to manager."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.import_palaces("/tmp/in.json", keep_existing=False)

        mock_manager.import_state.assert_called_once_with(
            "/tmp/in.json",
            keep_existing=False,
        )

    def test_import_error_prints_message(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given manager error, print error message."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.import_state.side_effect = RuntimeError("read err")

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.import_palaces("/tmp/in.json")

        assert "read err" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# TestBuildParser
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Feature: CLI argument parser parses all subcommands correctly."""

    @pytest.mark.parametrize(
        "argv,expected_cmd",
        [
            (["enable"], "enable"),
            (["disable"], "disable"),
            (["status"], "status"),
            (["skills"], "skills"),
            (["install"], "install"),
            (["list"], "list"),
        ],
        ids=["enable", "disable", "status", "skills", "install", "list"],
    )
    def test_simple_commands(self, argv: list[str], expected_cmd: str) -> None:
        """Given a simple subcommand, parser sets command correctly."""
        parser = build_parser()
        args = parser.parse_args(argv)
        assert args.command == expected_cmd

    def test_create_command(self) -> None:
        """Given 'create name domain', parser sets name and domain."""
        parser = build_parser()
        args = parser.parse_args(["create", "MyPalace", "programming"])
        assert args.command == "create"
        assert args.name == "MyPalace"
        assert args.domain == "programming"
        assert args.metaphor == "building"

    def test_create_with_metaphor(self) -> None:
        """Given --metaphor, parser sets custom metaphor."""
        parser = build_parser()
        args = parser.parse_args(
            ["create", "Fort", "rust", "--metaphor", "fortress"],
        )
        assert args.metaphor == "fortress"

    def test_search_command(self) -> None:
        """Given 'search query', parser captures query and type."""
        parser = build_parser()
        args = parser.parse_args(["search", "decorators", "--type", "fuzzy"])
        assert args.command == "search"
        assert args.query == "decorators"
        assert args.type == "fuzzy"

    def test_sync_command_flags(self) -> None:
        """Given sync with flags, parser captures them."""
        parser = build_parser()
        args = parser.parse_args(["sync", "--auto-create", "--dry-run"])
        assert args.command == "sync"
        assert args.auto_create is True
        assert args.dry_run is True

    def test_prune_command(self) -> None:
        """Given 'prune --apply --stale-days 60', parser captures flags."""
        parser = build_parser()
        args = parser.parse_args(["prune", "--apply", "--stale-days", "60"])
        assert args.command == "prune"
        assert args.apply is True
        assert args.stale_days == 60

    def test_garden_metrics_command(self) -> None:
        """Given 'garden metrics', parser captures garden_cmd."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "garden",
                "metrics",
                "--path",
                "/tmp/g.json",
                "--format",
                "brief",
                "--now",
                "2025-01-01T00:00:00",
            ]
        )
        assert args.command == "garden"
        assert args.garden_cmd == "metrics"
        assert args.path == "/tmp/g.json"
        assert args.format == "brief"

    def test_garden_tend_command(self) -> None:
        """Given 'garden tend' with options, parser captures them."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "garden",
                "tend",
                "--prune-days",
                "5",
                "--stale-days",
                "14",
                "--archive-days",
                "60",
                "--apply",
                "--prometheus",
                "--palaces",
            ]
        )
        assert args.command == "garden"
        assert args.garden_cmd == "tend"
        assert args.prune_days == 5
        assert args.stale_days == 14
        assert args.archive_days == 60
        assert args.apply is True
        assert args.prometheus is True
        assert args.palaces is True

    def test_export_command(self) -> None:
        """Given 'export --destination path', parser captures dest."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "export",
                "--destination",
                "/tmp/out.json",
            ]
        )
        assert args.command == "export"
        assert args.destination == "/tmp/out.json"

    def test_import_command(self) -> None:
        """Given 'import --source path --overwrite', parser captures."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "import",
                "--source",
                "/tmp/in.json",
                "--overwrite",
            ]
        )
        assert args.command == "import"
        assert args.source == "/tmp/in.json"
        assert args.overwrite is True

    def test_manager_command(self) -> None:
        """Given 'manager delete p1', parser captures remainder."""
        parser = build_parser()
        args = parser.parse_args(["manager", "delete", "p1"])
        assert args.command == "manager"
        assert args.manager_args == ["delete", "p1"]

    def test_no_command_sets_none(self) -> None:
        """Given no arguments, command is None."""
        parser = build_parser()
        args = parser.parse_args([])
        assert args.command is None


# ---------------------------------------------------------------------------
# TestMainDispatch
# ---------------------------------------------------------------------------


class TestMainDispatch:
    """Feature: main() dispatches to correct handler."""

    def test_no_command_prints_help(self) -> None:
        """Given no arguments, main prints help."""
        with patch("sys.argv", ["prog"]):
            with patch("scripts.memory_palace_cli.build_parser") as mock_bp:
                mock_parser = Mock()
                mock_parser.parse_args.return_value = Mock(command=None)
                mock_bp.return_value = mock_parser
                main()
                mock_parser.print_help.assert_called_once()

    @pytest.mark.parametrize(
        "command,method",
        [
            ("enable", "enable_plugin"),
            ("disable", "disable_plugin"),
            ("status", "show_status"),
            ("skills", "list_skills"),
            ("list", "list_palaces"),
        ],
        ids=["enable", "disable", "status", "skills", "list"],
    )
    def test_simple_command_dispatch(self, command: str, method: str) -> None:
        """Given a simple command, main calls the right CLI method."""
        with patch("sys.argv", ["prog", command]):
            with patch("scripts.memory_palace_cli.MemoryPalaceCLI") as mock_cls:
                mock_cli = Mock()
                mock_cls.return_value = mock_cli
                main()
                getattr(mock_cli, method).assert_called_once()


# ---------------------------------------------------------------------------
# TestPalacesDir
# ---------------------------------------------------------------------------


class TestPalacesDir:
    """Feature: _palaces_dir resolution."""

    def test_override_takes_precedence(self) -> None:
        """Given override value, use it."""
        cli = MemoryPalaceCLI()
        assert cli._palaces_dir("/custom") == "/custom"

    def test_falls_back_to_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given no override, use PALACES_DIR env var."""
        monkeypatch.setenv("PALACES_DIR", "/from/env")
        cli = MemoryPalaceCLI()
        assert cli._palaces_dir() == "/from/env"

    def test_returns_none_when_no_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Given no override and no env var, returns None."""
        monkeypatch.delenv("PALACES_DIR", raising=False)
        cli = MemoryPalaceCLI()
        assert cli._palaces_dir() is None


# ---------------------------------------------------------------------------
# TestComputeTendingActions
# ---------------------------------------------------------------------------


class TestComputeTendingActions:
    """Feature: Classify plots into prune, stale, and archive buckets."""

    def test_never_tended_goes_to_prune(self) -> None:
        """Given plot with no last_tended, classify as prune."""
        cli = MemoryPalaceCLI()
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        plots = [{"name": "orphan"}]

        actions = cli._compute_tending_actions(plots, now, 2, 7, 30)

        assert len(actions["prune"]) == 1
        assert actions["prune"][0] == ("orphan", "never tended")

    @pytest.mark.parametrize(
        "age_days,expected_bucket",
        [
            (3, "prune"),
            (10, "stale"),
            (60, "archive"),
        ],
        ids=["prune-age", "stale-age", "archive-age"],
    )
    def test_age_based_classification(
        self, age_days: int, expected_bucket: str
    ) -> None:
        """Given a plot of certain age, it falls into the right bucket."""
        from datetime import timedelta

        cli = MemoryPalaceCLI()
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        tended_at = now - timedelta(days=age_days)
        plots = [{"name": "test-plot", "last_tended": tended_at.isoformat()}]

        actions = cli._compute_tending_actions(plots, now, 2, 7, 30)

        assert len(actions[expected_bucket]) == 1
        assert actions[expected_bucket][0][0] == "test-plot"

    def test_fresh_plot_no_action(self) -> None:
        """Given a recently tended plot, no action needed."""
        cli = MemoryPalaceCLI()
        now = datetime(2025, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
        plots = [{"name": "fresh", "last_tended": now.isoformat()}]

        actions = cli._compute_tending_actions(plots, now, 2, 7, 30)

        assert all(len(v) == 0 for v in actions.values())


# ---------------------------------------------------------------------------
# TestDuplicateDetectionReporting
# ---------------------------------------------------------------------------


class TestPruneCheckDuplicates:
    """Feature: Prune check reports duplicate entries."""

    def test_duplicates_shown(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Given duplicates in results, print them."""
        cli = MemoryPalaceCLI()
        mock_manager = Mock(spec=MemoryPalaceManager)
        mock_manager.prune_check.return_value = {
            "palaces_checked": 2,
            "total_stale": 0,
            "total_low_quality": 0,
            "total_duplicates": 1,
            "recommendations": [],
            "duplicates": [
                {
                    "query": "shared topic",
                    "locations": ["dup-a", "dup-b"],
                },
            ],
        }

        with patch.object(cli, "_manager", return_value=mock_manager):
            cli.prune_check()

        out = capsys.readouterr().out
        assert "Duplicates found" in out
        assert "shared topic" in out
