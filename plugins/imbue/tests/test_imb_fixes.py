"""Tests for IMB-009: _load_state bare-except narrowed to (ValueError, TypeError) with WARN.

IMB-009: guard_scope_ramp._load_state previously used bare `except Exception:` which
silently swallowed all errors. After the fix, only (ValueError, TypeError) are caught and
a WARN is printed to stderr. Other exceptions propagate.
"""

from __future__ import annotations

import importlib.util
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def guard_hook():
    """Import guard_scope_ramp hook module via importlib.

    The hook module sets sys.path on load so 'shared.*' imports resolve.
    """
    hooks_path = Path(__file__).resolve().parent.parent / "hooks"
    module_path = hooks_path / "guard_scope_ramp.py"
    spec = importlib.util.spec_from_file_location("guard_scope_ramp_test", module_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestIMB009LoadStateNarrowedExcept:
    """IMB-009: _load_state prints WARN when JSON is corrupt.

    Before fix: bare `except Exception:` silently returned default, no WARN.
    After fix: `except (ValueError, TypeError):` prints WARN and returns default.
    """

    @pytest.mark.unit
    def test_corrupt_json_prints_warn_to_stderr(self, guard_hook, tmp_path):
        """WARN is printed to stderr when state file contains invalid JSON."""
        state_file = tmp_path / "state.json"
        state_file.write_text("NOT VALID JSON!!!")

        stderr_capture = StringIO()
        with patch("sys.stderr", stderr_capture):
            result = guard_hook._load_state(state_file)

        output = stderr_capture.getvalue()
        assert "WARN" in output, f"Expected WARN in stderr, got: {output!r}"
        assert result == {"rung": guard_hook.RUNG_START, "increments": 0}

    @pytest.mark.unit
    def test_missing_file_returns_default_without_warn(self, guard_hook, tmp_path):
        """Missing state file returns default silently (OSError caught separately)."""
        state_file = tmp_path / "nonexistent.json"

        stderr_capture = StringIO()
        with patch("sys.stderr", stderr_capture):
            result = guard_hook._load_state(state_file)

        # OSError (missing file) is caught in the outer try-except OSError, no WARN
        assert result == {"rung": guard_hook.RUNG_START, "increments": 0}

    @pytest.mark.unit
    def test_valid_json_returns_state(self, guard_hook, tmp_path):
        """Valid JSON state file is loaded and returned correctly."""
        state_file = tmp_path / "state.json"
        state_file.write_text('{"rung": 3, "increments": 2}')

        result = guard_hook._load_state(state_file)

        assert result == {"rung": 3, "increments": 2}
