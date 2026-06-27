"""Regression tests for PEN-005, PEN-007..PEN-010, PEN-012, PEN-015.

Each class is named after the finding it covers so failures are easy
to triage.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import psutil
import pytest

from pensive.analysis.repository_analyzer import RepositoryAnalyzer
from pensive.skills.rust_review.cargo import CargoBuildMixin
from pensive.skills.unified_review import UnifiedReviewSkill
from pensive.workflows.code_review import CodeReviewWorkflow
from pensive.workflows.memory_manager import get_optimal_strategy

# ---------------------------------------------------------------------------
# PEN-005 / PEN-015: RepositoryAnalyzer.detect_build_systems_from_files
# ---------------------------------------------------------------------------


class TestRepositoryAnalyzerDetectBuildSystemsFromFiles:
    """detect_build_systems_from_files classmethod (PEN-005)."""

    def _fn(self, files):
        return RepositoryAnalyzer.detect_build_systems_from_files(files)

    def test_makefile_maps_to_make(self):
        result = self._fn(["Makefile"])
        assert "make" in result

    def test_lowercase_makefile(self):
        result = self._fn(["makefile"])
        assert "make" in result

    def test_cmake_detected(self):
        result = self._fn(["CMakeLists.txt"])
        assert "cmake" in result

    def test_empty_list(self):
        assert self._fn([]) == []

    def test_deduplication(self):
        result = self._fn(["Makefile", "makefile"])
        assert result.count("make") == 1


class TestPen005DetectBuildSystems:
    """UnifiedReviewSkill.detect_build_systems delegates correctly (PEN-005)."""

    def setup_method(self):
        self.skill = UnifiedReviewSkill()

    def _ctx(self, files):
        ctx = Mock()
        ctx.get_files.return_value = files
        return ctx

    def test_makefile_no_duplicate_label(self):
        result = self.skill.detect_build_systems(self._ctx(["Makefile", "src/main.c"]))
        assert "make" in result
        assert "makefile" not in result

    def test_cargo_toml_detected(self):
        result = self.skill.detect_build_systems(self._ctx(["Cargo.toml"]))
        assert "cargo" in result

    def test_no_duplicates(self):
        result = self.skill.detect_build_systems(self._ctx(["Makefile", "makefile"]))
        assert result.count("make") == 1


# ---------------------------------------------------------------------------
# PEN-007: CodeReviewWorkflow.execute_skills MemoryError propagation
# ---------------------------------------------------------------------------


class TestPen007ExceptionNarrowing:
    """execute_skills catches non-fatal exceptions and propagates MemoryError (PEN-007)."""

    def _workflow(self, exc):
        wf = CodeReviewWorkflow()
        mock_skill = Mock()
        mock_skill.analyze.side_effect = exc
        wf.register_skill("probe", mock_skill)
        return wf

    def test_value_error_caught_returns_none(self):
        wf = self._workflow(ValueError("bad"))
        result = wf.execute_skills(["probe"], Mock())
        assert result == [None]

    def test_attribute_error_caught_returns_none(self):
        wf = self._workflow(AttributeError("attr"))
        result = wf.execute_skills(["probe"], Mock())
        assert result == [None]

    def test_oserror_caught_returns_none(self):
        wf = self._workflow(OSError("io"))
        result = wf.execute_skills(["probe"], Mock())
        assert result == [None]

    def test_runtime_error_caught_returns_none(self):
        wf = self._workflow(RuntimeError("rt"))
        result = wf.execute_skills(["probe"], Mock())
        assert result == [None]

    def test_memory_error_propagates(self):
        wf = self._workflow(MemoryError("oom"))
        with pytest.raises(MemoryError):
            wf.execute_skills(["probe"], Mock())

    def test_continues_after_error(self):
        wf = CodeReviewWorkflow()
        fail_skill = Mock()
        fail_skill.analyze.side_effect = ValueError("fail")
        ok_skill = Mock()
        ok_skill.analyze.return_value = "ok"
        wf.register_skill("fail", fail_skill)
        wf.register_skill("ok", ok_skill)
        result = wf.execute_skills(["fail", "ok"], Mock())
        assert result == [None, "ok"]


# ---------------------------------------------------------------------------
# PEN-008: memory_manager.get_optimal_strategy exception narrowing
# ---------------------------------------------------------------------------


class TestPen008MemoryManagerExceptionNarrowing:
    """get_optimal_strategy catches psutil OSError/AttributeError (PEN-008)."""

    def _call(self, exc):
        with patch.object(psutil, "virtual_memory", side_effect=exc):
            return get_optimal_strategy(10)

    def test_oserror_does_not_crash(self):
        result = self._call(OSError("no psutil"))
        assert result is not None
        assert "concurrent" in result

    def test_attribute_error_does_not_crash(self):
        result = self._call(AttributeError("attr"))
        assert result is not None
        assert "concurrent" in result

    def test_runtime_error_propagates(self):
        with pytest.raises(RuntimeError):
            self._call(RuntimeError("unexpected"))


# ---------------------------------------------------------------------------
# PEN-009: CargoBuildMixin.analyze_dependencies exception narrowing
# ---------------------------------------------------------------------------


class TestPen009CargoExceptionNarrowing:
    """analyze_dependencies returns empty dict on IO errors (PEN-009)."""

    def _mixin(self):
        return CargoBuildMixin()

    def test_file_not_found_returns_empty(self):
        ctx = Mock()
        ctx.get_file_content.side_effect = FileNotFoundError("no file")
        result = self._mixin().analyze_dependencies(ctx)
        assert result == {
            "dependencies": [],
            "version_issues": [],
            "security_concerns": [],
            "feature_analysis": [],
        }

    def test_oserror_returns_empty(self):
        ctx = Mock()
        ctx.get_file_content.side_effect = OSError("io")
        result = self._mixin().analyze_dependencies(ctx)
        assert result["dependencies"] == []

    def test_attribute_error_returns_empty(self):
        ctx = Mock()
        ctx.get_file_content.side_effect = AttributeError("attr")
        result = self._mixin().analyze_dependencies(ctx)
        assert result["dependencies"] == []

    def test_runtime_error_propagates(self):
        ctx = Mock()
        ctx.get_file_content.side_effect = RuntimeError("unexpected")
        with pytest.raises(RuntimeError):
            self._mixin().analyze_dependencies(ctx)


# ---------------------------------------------------------------------------
# PEN-010: UnifiedReviewSkill.detect_api_surface callable guard removed
# ---------------------------------------------------------------------------


class TestPen010DetectApiSurface:
    """detect_api_surface calls get_file_content as a method (PEN-010)."""

    def setup_method(self):
        self.skill = UnifiedReviewSkill()

    def test_calls_get_file_content_as_method(self):
        ctx = Mock()
        ctx.get_files.return_value = ["api.ts"]
        ctx.get_file_content.return_value = "export function foo() {}"
        self.skill.detect_api_surface(ctx)
        ctx.get_file_content.assert_called_once_with("api.ts")

    def test_function_count(self):
        ctx = Mock()
        ctx.get_files.return_value = ["mod.ts"]
        ctx.get_file_content.return_value = (
            "export function a() {}\nexport function b() {}"
        )
        result = self.skill.detect_api_surface(ctx)
        assert result["functions"] == 2

    def test_missing_method_skipped(self):
        ctx = Mock()
        ctx.get_files.return_value = ["api.ts"]
        ctx.get_file_content.side_effect = AttributeError("no method")
        result = self.skill.detect_api_surface(ctx)
        assert result["functions"] == 0


# ---------------------------------------------------------------------------
# PEN-012: detect_languages O(F) single pass (characterization)
# ---------------------------------------------------------------------------


class TestPen012DetectLanguagesCorrectness:
    """detect_languages returns accurate language metadata (PEN-012)."""

    def setup_method(self):
        self.skill = UnifiedReviewSkill()

    def _ctx(self, files):
        ctx = Mock()
        ctx.get_files.return_value = files
        return ctx

    def test_rust_detected_from_rs_files(self):
        result = self.skill.detect_languages(self._ctx(["src/main.rs"]))
        assert "rust" in result

    def test_python_detected_from_py_files(self):
        result = self.skill.detect_languages(self._ctx(["app.py"]))
        assert "python" in result

    def test_javascript_detected_from_js_files(self):
        result = self.skill.detect_languages(self._ctx(["index.js"]))
        assert "javascript" in result

    def test_no_languages_for_empty_files(self):
        result = self.skill.detect_languages(self._ctx([]))
        assert result == {}

    def test_cargo_toml_sets_flag(self):
        result = self.skill.detect_languages(self._ctx(["Cargo.toml", "src/lib.rs"]))
        assert result.get("rust", {}).get("cargo_toml") is True

    def test_test_files_flag_for_python(self):
        result = self.skill.detect_languages(self._ctx(["test_app.py", "app.py"]))
        assert result.get("python", {}).get("test_files") is True

    def test_multiple_languages(self):
        result = self.skill.detect_languages(
            self._ctx(["main.py", "main.rs", "index.js"])
        )
        assert "python" in result
        assert "rust" in result
        assert "javascript" in result


# ---------------------------------------------------------------------------
# PEN-015: RepositoryAnalyzer.analyze delegates to analyze_repository
# ---------------------------------------------------------------------------


class TestPen015AnalyzeDelegates:
    """analyze() must delegate to analyze_repository() (PEN-015)."""

    def test_analyze_calls_analyze_repository(self, tmp_path):
        analyzer = RepositoryAnalyzer(tmp_path)
        with patch.object(
            analyzer,
            "analyze_repository",
            return_value={
                "languages": {},
                "build_systems": [],
                "test_frameworks": [],
                "file_count": 0,
            },
        ) as mock_ar:
            analyzer.analyze()
            mock_ar.assert_called_once_with(tmp_path)

    def test_analyze_no_repo_path_returns_empty(self):
        analyzer = RepositoryAnalyzer()
        result = analyzer.analyze()
        assert result == {"files": [], "languages": [], "findings": []}
