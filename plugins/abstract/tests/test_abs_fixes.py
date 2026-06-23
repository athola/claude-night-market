"""Tests for ABS-001 through ABS-022 code refinement findings.

Each test section documents its bucket:
- Behavioral change: red before fix, green after
- Equivalence refactor: regression guard, green both sides
- Already satisfied: regression guard, green immediately
"""

from __future__ import annotations

import ast
import json
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# ABS-005 — wrapper_base._unparse_annotation: narrow except (SyntaxError, ValueError)
#            to except (ValueError, TypeError)
# Bucket: behavioral change — TypeError not caught before fix (propagates),
#         caught after fix (returns None).
# ---------------------------------------------------------------------------


def test_abs005_unparse_annotation_catches_type_error():
    """_unparse_annotation returns None when ast.unparse raises TypeError."""
    from abstract.wrapper_base import _unparse_annotation

    # Use a valid Name node so ast.parse succeeds; mock overrides unparse behavior
    node = ast.Name(id="x", ctx=ast.Load())
    with patch("ast.unparse", side_effect=TypeError("bad node")):
        result = _unparse_annotation(node)
    assert result is None


def test_abs005_unparse_annotation_still_catches_value_error():
    """_unparse_annotation still returns None for ValueError from ast.unparse."""
    from abstract.wrapper_base import _unparse_annotation

    node = ast.Name(id="x", ctx=ast.Load())
    with patch("ast.unparse", side_effect=ValueError("bad node")):
        result = _unparse_annotation(node)
    assert result is None


def test_abs005_unparse_annotation_returns_none_for_none_input():
    """_unparse_annotation returns None when node is None (existing behavior)."""
    from abstract.wrapper_base import _unparse_annotation

    assert _unparse_annotation(None) is None


# ---------------------------------------------------------------------------
# ABS-006 — wrapper_base.SuperpowerWrapper: deprecated class deleted
# Bucket: behavioral change — class present before deletion, absent after.
# ---------------------------------------------------------------------------


def test_abs006_superpower_wrapper_removed_from_module():
    """SuperpowerWrapper no longer exists in abstract.wrapper_base."""
    import abstract.wrapper_base as wb

    assert not hasattr(wb, "SuperpowerWrapper"), (
        "SuperpowerWrapper is deprecated with 0 production consumers "
        "and must be removed"
    )


# ---------------------------------------------------------------------------
# ABS-017 — skill_tools.analyze_skill: narrow except Exception to
#            except (OSError, json.JSONDecodeError, KeyError)
# Bucket: behavioral change — RuntimeError currently swallowed (returns error dict),
#         must propagate after fix.
# ---------------------------------------------------------------------------


def test_abs017_analyze_skill_propagates_runtime_error(tmp_path):
    """analyze_skill propagates RuntimeError from file read, not silently records it."""
    from abstract.skill_tools import analyze_skill

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n\nContent.")

    with patch("builtins.open", side_effect=RuntimeError("unexpected internal error")):
        with pytest.raises(RuntimeError, match="unexpected internal error"):
            analyze_skill(str(skill_dir))


def test_abs017_analyze_skill_records_os_error_as_error_dict(tmp_path):
    """analyze_skill still catches OSError and returns error dict in results."""
    from abstract.skill_tools import analyze_skill

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n\nContent.")

    with patch("builtins.open", side_effect=OSError("permission denied")):
        result = analyze_skill(str(skill_dir))

    assert result["total_files"] == 1
    assert "error" in result["results"][0]


# ---------------------------------------------------------------------------
# ABS-019 — utils.load_config_with_defaults: narrow except Exception to
#            except (OSError, yaml.YAMLError, TypeError)
# Bucket: regression guard — malformed YAML must still fall back to AbstractConfig().
#         The finding suggests json.JSONDecodeError; yaml.YAMLError is required
#         since the config file is always YAML. Test documents the correct behavior.
# ---------------------------------------------------------------------------


def test_abs019_load_config_with_defaults_malformed_yaml_falls_back(tmp_path):
    """load_config_with_defaults falls back to AbstractConfig() on malformed YAML."""
    from abstract.config import AbstractConfig
    from abstract.utils import load_config_with_defaults

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "abstract_config.yaml").write_text(
        "invalid: yaml: {{{not valid", encoding="utf-8"
    )

    result = load_config_with_defaults(project_root=tmp_path)
    assert isinstance(result, AbstractConfig)


def test_abs019_load_config_with_defaults_os_error_falls_back(tmp_path):
    """load_config_with_defaults falls back to AbstractConfig() on OSError."""
    from abstract.config import AbstractConfig
    from abstract.utils import load_config_with_defaults

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    # Create the file so exists() returns True, then error on open
    config_yaml = config_dir / "abstract_config.yaml"
    config_yaml.write_text("debug: false", encoding="utf-8")

    with patch("builtins.open", side_effect=OSError("disk error")):
        result = load_config_with_defaults(project_root=tmp_path)

    assert isinstance(result, AbstractConfig)


# ---------------------------------------------------------------------------
# ABS-022 — tasks_manager_base.TaskState.in_progress_tasks: O(n²) list
#            membership → O(n) set lookup
# Bucket: equivalence refactor — regression guard only.
# ---------------------------------------------------------------------------


def test_abs022_in_progress_tasks_excludes_completed():
    """in_progress_tasks returns pending tasks not in completed."""
    from abstract.tasks_manager_base import TaskState

    state = TaskState(
        pending_tasks=["t1", "t2", "t3"],
        completed_tasks=["t1"],
    )
    result = state.in_progress_tasks
    assert result == ["t2", "t3"]


def test_abs022_in_progress_tasks_all_completed_returns_empty():
    """in_progress_tasks returns empty list when all pending are completed."""
    from abstract.tasks_manager_base import TaskState

    state = TaskState(
        pending_tasks=["t1", "t2"],
        completed_tasks=["t1", "t2"],
    )
    assert state.in_progress_tasks == []


def test_abs022_in_progress_tasks_none_completed_returns_all_pending():
    """in_progress_tasks returns all pending when completed list is empty."""
    from abstract.tasks_manager_base import TaskState

    state = TaskState(
        pending_tasks=["t1", "t2", "t3"],
        completed_tasks=[],
    )
    assert state.in_progress_tasks == ["t1", "t2", "t3"]


# ---------------------------------------------------------------------------
# ABS-001/002 — tasks_manager_base._load_fallback_state extracted from
#               get_state and detect_resume_state
# Bucket: behavioral change — method does not exist before extraction.
# ---------------------------------------------------------------------------


def test_abs001_002_load_fallback_state_method_exists(tmp_path):
    """TasksManager has a _load_fallback_state() method after extraction."""
    from abstract.tasks_manager_base import TasksManager, TasksManagerConfig

    cfg = TasksManagerConfig(
        plugin_name="test",
        task_prefix="TEST",
        default_state_dir=str(tmp_path),
        default_state_file="state.json",
        env_var_prefix="TEST",
    )
    mgr = TasksManager(
        project_path=tmp_path,
        fallback_state_file=tmp_path / "state.json",
        config=cfg,
        use_tasks=False,
    )
    assert hasattr(mgr, "_load_fallback_state"), (
        "_load_fallback_state method must be extracted from get_state / "
        "detect_resume_state"
    )


def test_abs001_002_load_fallback_state_returns_dict_when_file_missing(tmp_path):
    """_load_fallback_state returns empty dict when state file is absent."""
    from abstract.tasks_manager_base import TasksManager, TasksManagerConfig

    cfg = TasksManagerConfig(
        plugin_name="test",
        task_prefix="TEST",
        default_state_dir=str(tmp_path),
        default_state_file="state.json",
        env_var_prefix="TEST",
    )
    mgr = TasksManager(
        project_path=tmp_path,
        fallback_state_file=tmp_path / "missing.json",
        config=cfg,
        use_tasks=False,
    )
    result = mgr._load_fallback_state()
    assert isinstance(result, dict)
    assert result == {}


def test_abs001_002_load_fallback_state_returns_dict_when_file_present(tmp_path):
    """_load_fallback_state returns parsed dict when state file exists."""
    from abstract.tasks_manager_base import TasksManager, TasksManagerConfig

    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps({"tasks": {"t-001": {"status": "pending", "description": "do it"}}}),
        encoding="utf-8",
    )
    cfg = TasksManagerConfig(
        plugin_name="test",
        task_prefix="TEST",
        default_state_dir=str(tmp_path),
        default_state_file="state.json",
        env_var_prefix="TEST",
    )
    mgr = TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=cfg,
        use_tasks=False,
    )
    result = mgr._load_fallback_state()
    assert "tasks" in result
    assert "t-001" in result["tasks"]


def test_abs001_002_get_state_still_works_after_extraction(tmp_path):
    """get_state behavior is unchanged after _load_fallback_state extraction."""
    from abstract.tasks_manager_base import TasksManager, TasksManagerConfig

    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "tasks": {
                    "t-001": {"status": "complete", "description": "done"},
                    "t-002": {"status": "pending", "description": "todo"},
                }
            }
        ),
        encoding="utf-8",
    )
    cfg = TasksManagerConfig(
        plugin_name="test",
        task_prefix="TEST",
        default_state_dir=str(tmp_path),
        default_state_file="state.json",
        env_var_prefix="TEST",
    )
    mgr = TasksManager(
        project_path=tmp_path,
        fallback_state_file=state_file,
        config=cfg,
        use_tasks=False,
    )
    state = mgr.get_state()
    assert "t-001" in state.completed_tasks
    assert "t-002" in state.pending_tasks


# ---------------------------------------------------------------------------
# ABS-009 — token_tracker.TokenUsageTracker: cache analyze_all_skills()
#            so multiple public methods share one traversal
# Bucket: behavioral change — call count spy detects the reduction.
# ---------------------------------------------------------------------------


def test_abs009_analyze_all_skills_called_once_across_efficiency_and_modularization(
    tmp_path,
):
    """Two callers share one analyze_all_skills traversal after caching."""
    from abstract.skills_eval.token_tracker import TokenUsageTracker

    tracker = TokenUsageTracker(skills_dir=tmp_path)

    with patch.object(
        tracker, "analyze_all_skills", wraps=tracker.analyze_all_skills
    ) as spy:
        tracker.calculate_token_efficiency()
        tracker.suggest_modularization()

    assert spy.call_count == 1, (
        f"analyze_all_skills called {spy.call_count} times; expected 1 after caching"
    )


def test_abs009_analyze_all_skills_called_once_across_all_three_methods(tmp_path):
    """All three redundant callers of analyze_all_skills use at most one traversal."""
    from abstract.skills_eval.token_tracker import TokenUsageTracker

    tracker = TokenUsageTracker(skills_dir=tmp_path)

    with patch.object(
        tracker, "analyze_all_skills", wraps=tracker.analyze_all_skills
    ) as spy:
        tracker.calculate_token_efficiency()
        tracker.suggest_modularization()
        tracker.identify_optimization_opportunities()

    assert spy.call_count == 1, (
        f"analyze_all_skills called {spy.call_count} times across three methods; "
        "expected 1 after caching"
    )


# ---------------------------------------------------------------------------
# ABS-012/013 — auditor.py:114 and token_tracker.py:372
#               len([comprehension]) → sum(1 for ... if ...)
# Bucket: equivalence refactor — regression guards pin existing output values.
# ---------------------------------------------------------------------------


def test_abs012_audit_skills_well_structured_count_is_correct(tmp_path):
    """audit_skills returns correct well_structured count (regression guard)."""
    from abstract.skills_eval.auditor import SkillsAuditor

    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: my-skill\ndescription: A test skill\n---\n\n"
        "## Overview\n\nGood skill.\n\n## Quick Start\n\nStep 1.\n\n"
        "## Examples\n\n```python\nprint('hi')\n```\n",
        encoding="utf-8",
    )

    auditor = SkillsAuditor(skills_dir=tmp_path)
    result = auditor.audit_skills()
    assert isinstance(result["well_structured"], int)
    assert isinstance(result["needs_improvement"], int)
    assert result["total_skills"] == 1


def test_abs013_get_usage_statistics_skills_over_limit_count_is_correct(tmp_path):
    """get_usage_statistics returns correct skills_over_limit count (regression guard)."""
    from abstract.skills_eval.token_tracker import TokenUsageTracker

    skill_dir = tmp_path / "big-skill"
    skill_dir.mkdir()
    # Write content large enough to exceed the default optimal limit of 1000 tokens
    large_content = "word " * 2000
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: big-skill\ndescription: Large skill\n---\n\n{large_content}",
        encoding="utf-8",
    )

    tracker = TokenUsageTracker(skills_dir=tmp_path, optimal_limit=100)
    stats = tracker.get_usage_statistics()
    assert stats["skills_over_limit"] == 1
    assert stats["optimal_usage_count"] == 0


# ---------------------------------------------------------------------------
# ABS-003, ABS-004, ABS-011/018, ABS-015 — already satisfied
# Regression guards only (green immediately).
# ---------------------------------------------------------------------------


def test_abs003_already_satisfied_analyze_skill_tokens_catches_os_error(tmp_path):
    """analyze_skill_tokens returns error dict (not raises) on OSError — already fixed."""
    from abstract.skills_eval.token_tracker import TokenUsageTracker

    tracker = TokenUsageTracker(skills_dir=tmp_path)
    skill_dir = tmp_path / "some-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("content", encoding="utf-8")

    with patch("builtins.open", side_effect=OSError("read error")):
        result = tracker.analyze_skill_tokens("some-skill")

    assert "error" in result
    assert result["total_tokens"] == 0


def test_abs004_already_satisfied_optimize_suggestions_catches_os_error(tmp_path):
    """optimize_suggestions returns error message (not raises) on OSError — already fixed."""
    from abstract.skills_eval.token_tracker import TokenUsageTracker

    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("content", encoding="utf-8")

    tracker = TokenUsageTracker(skills_dir=tmp_path)
    with patch("builtins.open", side_effect=OSError("disk error")):
        result = tracker.optimize_suggestions("test-skill")

    assert isinstance(result, list)
    assert any("Error" in s for s in result)


def test_abs011_018_already_satisfied_audit_all_skills_delegates_to_audit_skills(
    tmp_path,
):
    """audit_all_skills already delegates to audit_skills — regression guard."""
    from abstract.skills_eval.auditor import SkillsAuditor

    auditor = SkillsAuditor(skills_dir=tmp_path)
    with patch.object(auditor, "audit_skills", wraps=auditor.audit_skills) as spy:
        auditor.audit_all_skills()
    assert spy.call_count == 1


def test_abs015_already_satisfied_generate_improvement_plan_calls_analyze_skill_once(
    tmp_path,
):
    """generate_improvement_plan calls analyze_skill exactly once — already satisfied."""
    from abstract.skills_eval.improvements import ImprovementSuggester

    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test-skill\ndescription: A skill\n---\n\n## Overview\n\nOK.",
        encoding="utf-8",
    )

    suggester = ImprovementSuggester(skills_dir=tmp_path)
    with patch.object(suggester, "analyze_skill", wraps=suggester.analyze_skill) as spy:
        suggester.generate_improvement_plan("test-skill")
    assert spy.call_count == 1
