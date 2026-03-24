"""Shared fixtures and helpers for memory-palace scripts tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from scripts.memory_palace_cli import TendingOptions


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
