"""Tests for tasks_manager.py script."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "tasks_manager.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("sanctum_tasks_manager", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_tasks_manager"] = module
    spec.loader.exec_module(module)
    return module


def test_module_imports_cleanly():
    module = _load_script()
    assert module is not None


def test_plugin_name_is_sanctum():
    module = _load_script()
    assert module.PLUGIN_NAME == "sanctum"


def test_task_prefix_uppercase():
    module = _load_script()
    assert module.TASK_PREFIX == "SANCTUM"


def test_default_state_directory_hidden():
    module = _load_script()
    assert module.DEFAULT_STATE_DIR.startswith(".")


def test_default_state_file_is_json():
    module = _load_script()
    assert module.DEFAULT_STATE_FILE.endswith(".json")


def test_env_var_prefix_namespaced():
    module = _load_script()
    assert "CLAUDE_CODE_TASK" in module.ENV_VAR_PREFIX


def test_thresholds_are_positive_ints():
    module = _load_script()
    assert isinstance(module.LARGE_SCOPE_TOKEN_THRESHOLD, int)
    assert isinstance(module.LARGE_SCOPE_WORD_THRESHOLD, int)
    assert module.LARGE_SCOPE_TOKEN_THRESHOLD > 0
    assert module.LARGE_SCOPE_WORD_THRESHOLD > 0


def test_thresholds_respect_env_overrides(monkeypatch):
    monkeypatch.setenv("SANCTUM_LARGE_SCOPE_TOKEN_THRESHOLD", "1234")
    monkeypatch.setenv("SANCTUM_LARGE_SCOPE_WORD_THRESHOLD", "55")
    sys.modules.pop("sanctum_tasks_manager", None)
    module = _load_script()
    assert module.LARGE_SCOPE_TOKEN_THRESHOLD == 1234
    assert module.LARGE_SCOPE_WORD_THRESHOLD == 55


def test_cross_cutting_keywords_cover_pr_workflow():
    module = _load_script()
    flat = " ".join(module.CROSS_CUTTING_KEYWORDS).lower()
    for term in ("review", "rebase", "merge", "docs", "codebase"):
        assert term in flat, term


def test_sanctum_config_carries_plugin_name():
    module = _load_script()
    cfg = module.SANCTUM_CONFIG
    assert getattr(cfg, "plugin_name", None) == "sanctum"


def test_public_api_exports_expected_names():
    module = _load_script()
    expected = {
        "AmbiguityResult",
        "AmbiguityType",
        "CROSS_CUTTING_KEYWORDS",
        "ResumeState",
        "SANCTUM_CONFIG",
        "TasksManager",
        "TasksManagerConfig",
        "TaskState",
        "detect_ambiguity",
        "get_claude_code_version",
        "is_tasks_available",
    }
    assert set(module.__all__) == expected


def test_all_exported_symbols_resolve():
    module = _load_script()
    for name in module.__all__:
        assert hasattr(module, name), name
