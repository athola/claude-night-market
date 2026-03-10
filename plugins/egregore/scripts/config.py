"""Egregore configuration management.

Provides nested dataclass configuration for the egregore plugin,
with JSON serialization and deserialization.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class OverseerConfig:
    """Configuration for the human overseer notification channel."""

    method: str = "github-repo-owner"
    email: str | None = None
    webhook_url: str | None = None
    webhook_format: str = "generic"


@dataclass
class AlertsConfig:
    """Configuration for which events trigger alerts."""

    on_crash: bool = True
    on_rate_limit: bool = True
    on_pipeline_failure: bool = True
    on_completion: bool = True
    on_watchdog_relaunch: bool = True


@dataclass
class PipelineConfig:
    """Configuration for the issue processing pipeline."""

    max_attempts_per_step: int = 3
    skip_brainstorm_for_issues: bool = True
    auto_merge: bool = False


@dataclass
class BudgetConfig:
    """Configuration for token budget tracking."""

    window_type: str = "5h"
    cooldown_padding_minutes: int = 10


@dataclass
class EgregoreConfig:
    """Top-level egregore configuration."""

    overseer: OverseerConfig = field(default_factory=OverseerConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    budget: BudgetConfig = field(default_factory=BudgetConfig)


def save_config(cfg: EgregoreConfig, path: Path) -> None:
    """Serialize an EgregoreConfig to a JSON file.

    Args:
        cfg: The configuration to save.
        path: File path to write JSON to.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(cfg)
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_config(path: Path) -> EgregoreConfig:
    """Load an EgregoreConfig from a JSON file.

    If the file does not exist, returns a default configuration.

    Args:
        path: File path to read JSON from.

    Returns:
        An EgregoreConfig instance.

    """
    if not path.exists():
        return EgregoreConfig()

    data = json.loads(path.read_text())
    return EgregoreConfig(
        overseer=OverseerConfig(**data.get("overseer", {})),
        alerts=AlertsConfig(**data.get("alerts", {})),
        pipeline=PipelineConfig(**data.get("pipeline", {})),
        budget=BudgetConfig(**data.get("budget", {})),
    )
