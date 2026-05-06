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


# ----- Behavioral tests (C4 from PR #470 review) -------------------
# The constant-only tests above lock down configuration but do not
# verify any logic. The tests below exercise detect_ambiguity and the
# TasksManager fallback-state lifecycle so that reverting the SUT in
# abstract.tasks_manager_base would actually fail this suite.


def test_detect_ambiguity_clean_short_task():
    module = _load_script()
    result = module.detect_ambiguity("rename foo to bar")
    assert result.is_ambiguous is False


def test_detect_ambiguity_flags_large_word_count():
    module = _load_script()
    long_desc = " ".join(["word"] * 60)
    result = module.detect_ambiguity(long_desc)
    assert result.is_ambiguous is True
    assert result.ambiguity_type == module.AmbiguityType.LARGE_SCOPE


def test_detect_ambiguity_flags_multiple_components():
    module = _load_script()
    files = [f"plugins/p{i}/SKILL.md" for i in range(10)]
    result = module.detect_ambiguity(
        "edit a file",
        context={"files_touched": files},
    )
    assert result.is_ambiguous is True
    assert result.ambiguity_type == module.AmbiguityType.MULTIPLE_COMPONENTS


def test_detect_ambiguity_flags_cross_cutting_keyword():
    module = _load_script()
    result = module.detect_ambiguity(
        "review the codebase for issues",
        cross_cutting_keywords=["codebase"],
    )
    assert result.is_ambiguous is True
    assert result.ambiguity_type == module.AmbiguityType.CROSS_CUTTING


def test_tasks_manager_fallback_lifecycle(tmp_path):
    """Lifecycle smoke: create manager in fallback mode, load a plan,
    confirm pending_count tracks the plan size."""
    module = _load_script()
    state_file = tmp_path / "tasks-state.json"
    manager = module.TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=module.SANCTUM_CONFIG,
        use_tasks=False,  # Force fallback path; no Claude Code Tasks needed.
    )
    assert manager.pending_count == 0
    manager.load_plan(["task A", "task B", "task C"])
    assert manager.pending_count == 3
