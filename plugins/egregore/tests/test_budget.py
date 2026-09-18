"""Tests for egregore budget module."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from budget import Budget, is_in_cooldown, load_budget, save_budget


class TestNewBudget:
    """Test creating a new Budget with defaults."""

    def test_default_window_type(self) -> None:
        b = Budget()
        assert b.window_type == "5h"

    def test_default_window_started_at(self) -> None:
        b = Budget()
        assert b.window_started_at is None

    def test_default_estimated_tokens_used(self) -> None:
        b = Budget()
        assert b.estimated_tokens_used == 0

    def test_default_session_count(self) -> None:
        b = Budget()
        assert b.session_count == 0

    def test_default_last_rate_limit_at(self) -> None:
        b = Budget()
        assert b.last_rate_limit_at is None

    def test_default_cooldown_until(self) -> None:
        b = Budget()
        assert b.cooldown_until is None


class TestRecordRateLimit:
    """Test recording a rate limit event."""

    def test_sets_last_rate_limit_at(self) -> None:
        b = Budget()
        b.record_rate_limit(cooldown_minutes=15)
        assert b.last_rate_limit_at is not None

    def test_sets_cooldown_until(self) -> None:
        b = Budget()
        b.record_rate_limit(cooldown_minutes=15)
        assert b.cooldown_until is not None

    def test_cooldown_is_in_future(self) -> None:
        b = Budget()
        b.record_rate_limit(cooldown_minutes=15)
        cooldown = datetime.fromisoformat(b.cooldown_until)
        now = datetime.now(timezone.utc)
        assert cooldown > now

    def test_cooldown_duration_matches(self) -> None:
        b = Budget()
        b.record_rate_limit(cooldown_minutes=30)
        cooldown = datetime.fromisoformat(b.cooldown_until)
        rate_limit = datetime.fromisoformat(b.last_rate_limit_at)
        delta = cooldown - rate_limit
        # Allow 2 seconds of tolerance
        assert abs(delta.total_seconds() - 1800) < 2


class TestIncrementSession:
    """Test incrementing the session count."""

    def test_increments_from_zero(self) -> None:
        b = Budget()
        b.increment_session()
        assert b.session_count == 1

    def test_increments_multiple_times(self) -> None:
        b = Budget()
        b.increment_session()
        b.increment_session()
        b.increment_session()
        assert b.session_count == 3


class TestIsInCooldown:
    """Test is_in_cooldown function."""

    def test_no_cooldown_set(self) -> None:
        b = Budget()
        assert is_in_cooldown(b) is False

    def test_cooldown_in_future(self) -> None:
        b = Budget()
        future = datetime.now(timezone.utc) + timedelta(minutes=30)
        b.cooldown_until = future.isoformat()
        assert is_in_cooldown(b) is True

    def test_cooldown_in_past(self) -> None:
        b = Budget()
        past = datetime.now(timezone.utc) - timedelta(minutes=30)
        b.cooldown_until = past.isoformat()
        assert is_in_cooldown(b) is False


class TestSaveLoadBudget:
    """Test save/load roundtrip for budget."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        b = Budget()
        path = tmp_path / "budget.json"
        save_budget(b, path)
        assert path.exists()

    def test_save_produces_valid_json(self, tmp_path: Path) -> None:
        b = Budget()
        path = tmp_path / "budget.json"
        save_budget(b, path)
        data = json.loads(path.read_text())
        assert isinstance(data, dict)
        assert "window_type" in data

    def test_roundtrip_preserves_defaults(self, tmp_path: Path) -> None:
        b = Budget()
        path = tmp_path / "budget.json"
        save_budget(b, path)
        loaded = load_budget(path)

        assert loaded.window_type == b.window_type
        assert loaded.window_started_at == b.window_started_at
        assert loaded.estimated_tokens_used == b.estimated_tokens_used
        assert loaded.session_count == b.session_count
        assert loaded.last_rate_limit_at == b.last_rate_limit_at
        assert loaded.cooldown_until == b.cooldown_until

    def test_roundtrip_preserves_recorded_state(self, tmp_path: Path) -> None:
        b = Budget()
        b.record_rate_limit(cooldown_minutes=20)
        b.increment_session()
        b.increment_session()
        b.estimated_tokens_used = 50000

        path = tmp_path / "budget.json"
        save_budget(b, path)
        loaded = load_budget(path)

        assert loaded.session_count == 2
        assert loaded.estimated_tokens_used == 50000
        assert loaded.last_rate_limit_at == b.last_rate_limit_at
        assert loaded.cooldown_until == b.cooldown_until

    def test_load_missing_file_returns_default(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        loaded = load_budget(path)
        assert loaded.window_type == "5h"
        assert loaded.session_count == 0
        assert loaded.cooldown_until is None

    def test_load_ignores_unknown_fields(self, tmp_path: Path) -> None:
        """Future versions may add fields; loading should not crash."""
        path = tmp_path / "budget.json"
        data = {
            "window_type": "5h",
            "window_started_at": None,
            "estimated_tokens_used": 100,
            "session_count": 2,
            "last_rate_limit_at": None,
            "cooldown_until": None,
            "future_field": "unknown_value",
            "another_new_thing": 42,
        }
        path.write_text(json.dumps(data))
        loaded = load_budget(path)
        assert loaded.window_type == "5h"
        assert loaded.session_count == 2
        assert loaded.estimated_tokens_used == 100


class TestAtomicBudgetWrite:
    """The watchdog reads this file to decide whether to relaunch.

    ``path.write_text`` truncates first, so an interrupted save leaves a
    file that exists and holds invalid JSON. A truncated read there costs
    a whole night's run.

    The failure is injected at ``os.replace``, which is the last step of
    the atomic path and does not exist on the truncating one. Injecting it
    earlier, at ``json.dumps``, does not discriminate: that raises before
    ``write_text`` opens the file, so the old content survives either way.
    """

    def test_a_failed_save_leaves_the_previous_budget_readable(
        self, tmp_path, monkeypatch
    ):
        """A save that fails at the last step must not damage the old one."""
        path = tmp_path / "budget.json"
        save_budget(Budget(estimated_tokens_used=42), path)

        def explode(*args, **kwargs):
            raise OSError("cross-device link")

        monkeypatch.setattr(os, "replace", explode)
        with pytest.raises(OSError):
            save_budget(Budget(estimated_tokens_used=99), path)

        assert load_budget(path).estimated_tokens_used == 42, (
            "the previous budget was destroyed by a failed save; the "
            "watchdog reads this file to decide whether to relaunch"
        )

    def test_a_failed_save_leaves_no_temporary_file(self, tmp_path, monkeypatch):
        """The directory does not accumulate partial writes."""
        path = tmp_path / "budget.json"
        save_budget(Budget(estimated_tokens_used=42), path)

        def explode(*args, **kwargs):
            raise OSError("cross-device link")

        monkeypatch.setattr(os, "replace", explode)
        with pytest.raises(OSError):
            save_budget(Budget(), path)

        assert [entry.name for entry in tmp_path.iterdir()] == ["budget.json"]

    def test_a_successful_save_round_trips(self, tmp_path):
        """The happy path still writes what was asked for."""
        path = tmp_path / "budget.json"
        save_budget(Budget(estimated_tokens_used=7), path)
        assert load_budget(path).estimated_tokens_used == 7
