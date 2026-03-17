"""Tests for egregore config module."""

from __future__ import annotations

import json
from pathlib import Path

from config import (
    AlertsConfig,
    BudgetConfig,
    EgregoreConfig,
    OverseerConfig,
    PipelineConfig,
    load_config,
    save_config,
)


class TestDefaultConfig:
    """Test EgregoreConfig returns correct defaults."""

    def test_returns_egregore_config(self) -> None:
        cfg = EgregoreConfig()
        assert isinstance(cfg, EgregoreConfig)

    def test_overseer_defaults(self) -> None:
        cfg = EgregoreConfig()
        assert isinstance(cfg.overseer, OverseerConfig)
        assert cfg.overseer.method == "github-repo-owner"
        assert cfg.overseer.email is None
        assert cfg.overseer.webhook_url is None
        assert cfg.overseer.webhook_format == "generic"

    def test_alerts_defaults(self) -> None:
        cfg = EgregoreConfig()
        assert isinstance(cfg.alerts, AlertsConfig)
        assert cfg.alerts.on_crash is True
        assert cfg.alerts.on_rate_limit is True
        assert cfg.alerts.on_pipeline_failure is True
        assert cfg.alerts.on_completion is True
        assert cfg.alerts.on_watchdog_relaunch is True

    def test_pipeline_defaults(self) -> None:
        cfg = EgregoreConfig()
        assert isinstance(cfg.pipeline, PipelineConfig)
        assert cfg.pipeline.max_attempts_per_step == 3
        assert cfg.pipeline.skip_brainstorm_for_issues is True
        assert cfg.pipeline.auto_merge is False

    def test_budget_defaults(self) -> None:
        cfg = EgregoreConfig()
        assert isinstance(cfg.budget, BudgetConfig)
        assert cfg.budget.window_type == "5h"
        assert cfg.budget.cooldown_padding_minutes == 10


class TestSaveLoadConfig:
    """Test save/load roundtrip for config."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        cfg = EgregoreConfig()
        path = tmp_path / "config.json"
        save_config(cfg, path)
        assert path.exists()

    def test_save_produces_valid_json(self, tmp_path: Path) -> None:
        cfg = EgregoreConfig()
        path = tmp_path / "config.json"
        save_config(cfg, path)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)
        assert "overseer" in data
        assert "alerts" in data
        assert "pipeline" in data
        assert "budget" in data

    def test_roundtrip_preserves_values(self, tmp_path: Path) -> None:
        cfg = EgregoreConfig()
        path = tmp_path / "config.json"
        save_config(cfg, path)
        loaded = load_config(path)

        assert loaded.overseer.method == cfg.overseer.method
        assert loaded.overseer.email == cfg.overseer.email
        assert loaded.overseer.webhook_url == cfg.overseer.webhook_url
        assert loaded.overseer.webhook_format == cfg.overseer.webhook_format

        assert loaded.alerts.on_crash == cfg.alerts.on_crash
        assert loaded.alerts.on_rate_limit == cfg.alerts.on_rate_limit
        assert loaded.alerts.on_pipeline_failure == cfg.alerts.on_pipeline_failure
        assert loaded.alerts.on_completion == cfg.alerts.on_completion
        assert loaded.alerts.on_watchdog_relaunch == cfg.alerts.on_watchdog_relaunch

        assert (
            loaded.pipeline.max_attempts_per_step == cfg.pipeline.max_attempts_per_step
        )
        assert (
            loaded.pipeline.skip_brainstorm_for_issues
            == cfg.pipeline.skip_brainstorm_for_issues
        )
        assert loaded.pipeline.auto_merge == cfg.pipeline.auto_merge

        assert loaded.budget.window_type == cfg.budget.window_type
        assert (
            loaded.budget.cooldown_padding_minutes
            == cfg.budget.cooldown_padding_minutes
        )

    def test_roundtrip_with_custom_values(self, tmp_path: Path) -> None:
        cfg = EgregoreConfig(
            overseer=OverseerConfig(
                method="email",
                email="test@example.com",
                webhook_url="https://hooks.example.com/notify",
                webhook_format="slack",
            ),
            alerts=AlertsConfig(
                on_crash=False,
                on_rate_limit=False,
                on_pipeline_failure=True,
                on_completion=False,
                on_watchdog_relaunch=True,
            ),
            pipeline=PipelineConfig(
                max_attempts_per_step=5,
                skip_brainstorm_for_issues=False,
                auto_merge=True,
            ),
            budget=BudgetConfig(
                window_type="24h",
                cooldown_padding_minutes=30,
            ),
        )
        path = tmp_path / "config.json"
        save_config(cfg, path)
        loaded = load_config(path)

        assert loaded.overseer.method == "email"
        assert loaded.overseer.email == "test@example.com"
        assert loaded.overseer.webhook_url == "https://hooks.example.com/notify"
        assert loaded.overseer.webhook_format == "slack"
        assert loaded.alerts.on_crash is False
        assert loaded.pipeline.max_attempts_per_step == 5
        assert loaded.pipeline.auto_merge is True
        assert loaded.budget.window_type == "24h"
        assert loaded.budget.cooldown_padding_minutes == 30

    def test_load_missing_file_returns_default(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        cfg = load_config(path)
        default = EgregoreConfig()

        assert cfg.overseer.method == default.overseer.method
        assert cfg.alerts.on_crash == default.alerts.on_crash
        assert (
            cfg.pipeline.max_attempts_per_step == default.pipeline.max_attempts_per_step
        )
        assert cfg.budget.window_type == default.budget.window_type

    def test_load_ignores_unknown_fields_in_nested_dataclasses(
        self, tmp_path: Path
    ) -> None:
        """Future versions may add fields; loading should not crash."""
        path = tmp_path / "config.json"
        data = {
            "overseer": {
                "method": "email",
                "email": "a@b.com",
                "new_overseer_field": True,
            },
            "alerts": {
                "on_crash": False,
                "future_alert": "yes",
            },
            "pipeline": {
                "max_attempts_per_step": 5,
                "experimental_flag": 99,
            },
            "budget": {
                "window_type": "24h",
                "unknown_budget_key": [1, 2, 3],
            },
        }
        path.write_text(json.dumps(data))
        cfg = load_config(path)
        assert cfg.overseer.method == "email"
        assert cfg.overseer.email == "a@b.com"
        assert cfg.alerts.on_crash is False
        assert cfg.pipeline.max_attempts_per_step == 5
        assert cfg.budget.window_type == "24h"
