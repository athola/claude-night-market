"""The usage-logging skill's quick start runs as written."""

from __future__ import annotations

from pathlib import Path

from leyline.usage_logger import UsageEvent, UsageLogger


def test_a_logged_operation_is_read_back(tmp_path: Path) -> None:
    logger = UsageLogger(service="my-service", storage_dir=tmp_path)

    logger.log_usage(UsageEvent("analyze_files", tokens=5000, duration=2.5))

    recent = logger.get_recent_operations(hours=24)
    assert [op["operation"] for op in recent] == ["analyze_files"]
    assert recent[0]["tokens"] == 5000
