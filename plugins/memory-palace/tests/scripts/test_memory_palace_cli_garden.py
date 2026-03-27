"""Tests for MemoryPalaceCLI garden operations.

Covers:
- garden_metrics() (JSON, brief, prometheus, missing file, custom timestamp)
- garden_tend() (report modes, apply, archive export, edge cases)
- _compute_tending_actions() classification
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.memory_palace_cli import MemoryPalaceCLI

from .conftest import _default_tending_opts, _garden_data_with_plots


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
        updated["garden"]["plots"]
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
