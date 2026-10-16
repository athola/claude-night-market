"""The query flags of the usage_logger CLI must print what they query."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import usage_logger as _ul_mod
from usage_logger import UsageEvent, UsageLogger, main


@pytest.fixture
def seeded_service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """Point the CLI at a temp store holding one failure and one success."""
    original_init = _ul_mod.UsageLogger.__init__

    def _init(
        self: UsageLogger,
        service: str,
        storage_dir: Path | None = None,
        session_id: str | None = None,
    ) -> None:
        original_init(self, service, storage_dir=tmp_path, session_id=session_id)

    monkeypatch.setattr(_ul_mod.UsageLogger, "__init__", _init)
    seeder = UsageLogger(service="svc", storage_dir=tmp_path)
    seeder.log_usage(UsageEvent("ok-op", tokens=1500, success=True, duration=1.0))
    seeder.log_usage(
        UsageEvent(
            "bad-op",
            success=False,
            error_type="Boom",
            error_message="exploded",
        )
    )
    return "svc"


def test_summary_flag_prints_totals(
    seeded_service: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["usage_logger", seeded_service, "--summary"])

    main()

    out = capsys.readouterr().out
    assert "Operations: 2" in out
    assert "1,500" in out


def test_errors_flag_prints_each_error(
    seeded_service: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["usage_logger", seeded_service, "--errors", "5"])

    main()

    out = capsys.readouterr().out
    assert "Boom" in out
    assert "exploded" in out


def test_default_listing_prints_recent_operations(
    seeded_service: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["usage_logger", seeded_service])

    main()

    out = capsys.readouterr().out
    assert "ok-op" in out
    assert "bad-op" in out
