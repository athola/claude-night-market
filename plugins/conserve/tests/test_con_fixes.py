"""Tests for CON-001..022 refactors.

Each test name describes the behavior verified, not the implementation detail.
"""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Module loaders (avoid import-side-effects from sys.path mutation)
# ---------------------------------------------------------------------------

_PLUGIN_ROOT = Path(__file__).parent.parent


def _load_module(rel_path: str) -> types.ModuleType:
    """Load a module by path without polluting sys.modules permanently."""
    abs_path = _PLUGIN_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(abs_path.stem, abs_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr] - loader is None only when spec is None, guarded by assert above
    return mod


_gc_mod = _load_module("scripts/growth_controller.py")
GrowthController = _gc_mod.GrowthController
_ts_mod = _load_module("hooks/tool_output_summarizer.py")

# ecosystems is part of the context_scanner package; add scripts/ to path
_scripts_dir = str(_PLUGIN_ROOT / "scripts")
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
import context_scanner.ecosystems as _eco_mod  # noqa: E402 - must come after sys.path.insert above

scan_directory = _eco_mod.scan_directory

# ---------------------------------------------------------------------------
# CON-005: _STRATEGY_TYPES is a class-level attribute
# ---------------------------------------------------------------------------


def test_strategy_types_is_class_attribute():
    assert hasattr(GrowthController, "_STRATEGY_TYPES"), (
        "_STRATEGY_TYPES must be a class-level attribute"
    )


def test_strategy_types_shared_across_instances():
    a = GrowthController()
    b = GrowthController()
    assert a._STRATEGY_TYPES is b._STRATEGY_TYPES, (
        "Class constant must be shared, not copied per instance"
    )


def test_strategy_types_backward_compat_instance_attr():
    c = GrowthController()
    assert hasattr(c, "strategy_types"), (
        "Instance must still expose strategy_types for backward compatibility"
    )


def test_strategy_types_contains_conservative():
    c = GrowthController()
    assert "conservative" in c.strategy_types


def test_strategy_types_contains_moderate():
    c = GrowthController()
    assert "moderate" in c.strategy_types


def test_strategy_types_contains_aggressive():
    c = GrowthController()
    assert "aggressive" in c.strategy_types


# ---------------------------------------------------------------------------
# CON-006: unknown strategy raises ValueError (not KeyError / silent)
# ---------------------------------------------------------------------------


def test_generate_plan_unknown_strategy_raises_value_error():
    c = GrowthController()
    with pytest.raises(ValueError, match="Invalid strategy type"):
        c._generate_implementation_plan("bogus")


def test_generate_plan_unknown_strategy_message_includes_name():
    c = GrowthController()
    with pytest.raises(ValueError, match="bogus"):
        c._generate_implementation_plan("bogus")


# ---------------------------------------------------------------------------
# CON-007: _IMPLEMENTATION_PLANS is a class-level attribute
# ---------------------------------------------------------------------------


def test_implementation_plans_is_class_attribute():
    assert hasattr(GrowthController, "_IMPLEMENTATION_PLANS"), (
        "_IMPLEMENTATION_PLANS must be a class-level attribute"
    )


def test_conservative_plan_phase1_priority_low():
    c = GrowthController()
    plan = c._generate_implementation_plan("conservative")
    assert plan["phase_1"]["priority"] == "Low"


def test_conservative_plan_phase3_priority_low():
    c = GrowthController()
    plan = c._generate_implementation_plan("conservative")
    assert plan["phase_3"]["priority"] == "Low"


def test_moderate_plan_phase1_priority_high():
    c = GrowthController()
    plan = c._generate_implementation_plan("moderate")
    assert plan["phase_1"]["priority"] == "High"


def test_moderate_plan_phase3_priority_medium():
    c = GrowthController()
    plan = c._generate_implementation_plan("moderate")
    assert plan["phase_3"]["priority"] == "Medium"


def test_aggressive_plan_phase1_priority_critical():
    c = GrowthController()
    plan = c._generate_implementation_plan("aggressive")
    assert plan["phase_1"]["priority"] == "Critical"


def test_aggressive_plan_phase2_priority_critical():
    c = GrowthController()
    plan = c._generate_implementation_plan("aggressive")
    assert plan["phase_2"]["priority"] == "Critical"


def test_aggressive_plan_phase3_priority_high():
    c = GrowthController()
    plan = c._generate_implementation_plan("aggressive")
    assert plan["phase_3"]["priority"] == "High"


# ---------------------------------------------------------------------------
# CON-009: main() propagates FileNotFoundError and JSONDecodeError
# ---------------------------------------------------------------------------


def test_main_propagates_file_not_found(tmp_path):
    missing = str(tmp_path / "nonexistent.json")
    with patch("sys.argv", ["gc", "--analysis-file", missing]):
        with pytest.raises(FileNotFoundError):
            _gc_mod.main()


def test_main_propagates_json_decode_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    with patch("sys.argv", ["gc", "--analysis-file", str(bad)]):
        with pytest.raises(json.JSONDecodeError):
            _gc_mod.main()


# ---------------------------------------------------------------------------
# CON-002: _get_ccr_int_setting helper extracted from duplicated CCR getters
# ---------------------------------------------------------------------------


def test_ts_has_get_ccr_int_setting_helper():
    ts = _ts_mod
    assert hasattr(ts, "_get_ccr_int_setting"), (
        "_get_ccr_int_setting must be a module-level helper"
    )


def test_get_ccr_int_setting_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("CONSERVE_CCR_THRESHOLD", raising=False)
    result = _ts_mod._get_ccr_int_setting(
        "CONSERVE_CCR_THRESHOLD", 999, "CONSERVE_CCR_THRESHOLD"
    )
    assert result == 999


def test_get_ccr_int_setting_parses_valid_int(monkeypatch):
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", "12345")
    result = _ts_mod._get_ccr_int_setting(
        "CONSERVE_CCR_THRESHOLD", 999, "CONSERVE_CCR_THRESHOLD"
    )
    assert result == 12345


def test_get_ccr_int_setting_returns_default_on_invalid(monkeypatch):
    monkeypatch.setenv("CONSERVE_CCR_THRESHOLD", "not-a-number")
    result = _ts_mod._get_ccr_int_setting(
        "CONSERVE_CCR_THRESHOLD", 999, "CONSERVE_CCR_THRESHOLD"
    )
    assert result == 999


# ---------------------------------------------------------------------------
# CON-001: inner _walk removed from scan_directory (uses _walk_limited only)
# ---------------------------------------------------------------------------


def test_scan_directory_source_has_no_inner_walk_function():
    source = inspect.getsource(scan_directory)
    assert "def _walk(" not in source, (
        "Inner _walk nested function must be removed; use _walk_limited instead"
    )


# ---------------------------------------------------------------------------
# CON-003 / models exclusions: ScanResult.exclusions populated
# ---------------------------------------------------------------------------


def test_scan_directory_result_exclusions_not_none(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    result = scan_directory(tmp_path)
    assert result.exclusions is not None


def test_scan_directory_result_exclusions_is_list(tmp_path):
    (tmp_path / "main.py").write_text("print('hello')")
    result = scan_directory(tmp_path)
    assert isinstance(result.exclusions, list)
