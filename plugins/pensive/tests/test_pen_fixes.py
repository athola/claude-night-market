"""Regression tests for PEN-003..PEN-010, PEN-012, PEN-015.

Each class is named after the finding it covers so failures are easy
to triage.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import psutil
import pytest

from pensive.analysis.repository_analyzer import RepositoryAnalyzer
from pensive.config.configuration import Configuration
from pensive.exceptions import AnalysisError
from pensive.skills.base import AnalysisResult
from pensive.skills.makefile_review import MakefileReviewSkill
from pensive.skills.math_review import MathReviewSkill
from pensive.skills.rust_review.cargo import CargoBuildMixin
from pensive.skills.unified_review import UnifiedReviewSkill, dispatch_agent
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
# PEN-003: CodeReviewWorkflow.run stub removed
# ---------------------------------------------------------------------------


class TestPen003RunStubRemoved:
    """execute_full_review is the only entry point (PEN-003)."""

    def test_workflow_has_no_run_stub(self):
        assert not hasattr(CodeReviewWorkflow, "run")


# ---------------------------------------------------------------------------
# PEN-004: dispatch_agent runs the real skill
# ---------------------------------------------------------------------------


class TestPen004DispatchAgentRunsRealSkill:
    """dispatch_agent resolves and runs a skill instead of returning a string."""

    def test_unknown_skill_returns_none(self):
        assert dispatch_agent("no-such-skill", Mock()) is None

    def test_unified_review_returns_analysis_result(self):
        ctx = Mock()
        ctx.get_files.return_value = []
        result = dispatch_agent("unified-review", ctx)
        assert isinstance(result, AnalysisResult)
        assert result.warnings == ["No code files found in the repository"]


# ---------------------------------------------------------------------------
# PEN-006: skill selection owned by UnifiedReviewSkill.select_review_skills
# ---------------------------------------------------------------------------


class TestPen006SkillSelectionOwnedByUnifiedReview:
    """_determine_skills delegates to select_review_skills (PEN-006)."""

    def test_determine_skills_delegates_to_select_review_skills(self, tmp_path):
        wf = CodeReviewWorkflow()
        with patch.object(
            UnifiedReviewSkill,
            "select_review_skills",
            return_value=["code-reviewer", "makefile-review"],
        ):
            selected = wf._determine_skills(tmp_path, ["Makefile"])
        assert selected == ["unified-review", "makefile-review"]

    def test_select_review_skills_adds_api_review_for_api_files(self):
        ctx = Mock()
        ctx.get_files.return_value = ["src/api/routes.py"]
        ctx.get_file_content.return_value = ""
        assert "api-review" in UnifiedReviewSkill().select_review_skills(ctx)

    def test_workflow_resolves_makefile_and_math_review(self):
        wf = CodeReviewWorkflow()
        assert isinstance(wf._get_skill("makefile-review"), MakefileReviewSkill)
        assert isinstance(wf._get_skill("math-review"), MathReviewSkill)


# ---------------------------------------------------------------------------
# PEN-007: CodeReviewWorkflow catches (AnalysisError, OSError) only
# ---------------------------------------------------------------------------


class TestPen007ExceptionNarrowing:
    """Runtime failures are recorded; programming errors propagate (PEN-007).

    Supersedes the earlier fix that only let MemoryError through.
    """

    def _workflow(self, exc):
        wf = CodeReviewWorkflow()
        mock_skill = Mock()
        mock_skill.analyze.side_effect = exc
        wf.register_skill("probe", mock_skill)
        return wf

    def test_analysis_error_caught_returns_none(self):
        wf = self._workflow(AnalysisError("cargo missing"))
        result = wf.execute_skills(["probe"], Mock())
        assert result == [None]

    def test_oserror_caught_returns_none(self):
        wf = self._workflow(OSError("io"))
        result = wf.execute_skills(["probe"], Mock())
        assert result == [None]

    def test_value_error_propagates(self):
        wf = self._workflow(ValueError("bad"))
        with pytest.raises(ValueError, match="bad"):
            wf.execute_skills(["probe"], Mock())

    def test_attribute_error_propagates(self):
        wf = self._workflow(AttributeError("attr"))
        with pytest.raises(AttributeError):
            wf.execute_skills(["probe"], Mock())

    def test_runtime_error_propagates(self):
        wf = self._workflow(RuntimeError("rt"))
        with pytest.raises(RuntimeError):
            wf.execute_skills(["probe"], Mock())

    def test_memory_error_propagates(self):
        wf = self._workflow(MemoryError("oom"))
        with pytest.raises(MemoryError):
            wf.execute_skills(["probe"], Mock())

    def test_continues_after_error(self):
        wf = CodeReviewWorkflow()
        fail_skill = Mock()
        fail_skill.analyze.side_effect = AnalysisError("fail")
        ok_skill = Mock()
        ok_skill.analyze.return_value = "ok"
        wf.register_skill("fail", fail_skill)
        wf.register_skill("ok", ok_skill)
        result = wf.execute_skills(["fail", "ok"], Mock())
        assert result == [None, "ok"]

    def test_full_review_records_analysis_error_and_continues(self, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n")
        wf = CodeReviewWorkflow()
        broken = Mock()
        broken.analyze.side_effect = AnalysisError("toolchain missing")
        wf.register_skill("unified-review", broken)
        result = wf.execute_full_review(tmp_path)
        assert "unified-review" in result["skipped_skills"]
        assert any("toolchain missing" in err for err in result["errors"])

    def test_full_review_propagates_type_error(self, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n")
        wf = CodeReviewWorkflow()
        broken = Mock()
        broken.analyze.side_effect = TypeError("bad skill")
        wf.register_skill("unified-review", broken)
        with pytest.raises(TypeError, match="bad skill"):
            wf.execute_full_review(tmp_path)


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
        assert result == {
            "files": [],
            "languages": {},
            "build_systems": [],
            "test_frameworks": [],
            "file_count": 0,
            "findings": [],
        }


class TestFullReviewSeesBuildFilesAndSkipsVendoredTrees:
    """_collect_files kept only code suffixes, so `Makefile` and
    `Cargo.toml` never reached selection, and `.venv` was walked.
    """

    def test_full_review_selects_makefile_review_for_repo_with_makefile(self, tmp_path):
        (tmp_path / "Makefile").write_text("all:\n\ttrue\n")
        (tmp_path / "a.py").write_text("x = 1\n")
        wf = CodeReviewWorkflow()
        files = wf._collect_files(tmp_path)
        assert "makefile-review" in wf._determine_skills(tmp_path, files)

    def test_nested_cargo_toml_selects_rust_review(self, tmp_path):
        (tmp_path / "crates" / "x").mkdir(parents=True)
        (tmp_path / "crates" / "x" / "Cargo.toml").write_text("[package]\n")
        wf = CodeReviewWorkflow()
        files = wf._collect_files(tmp_path)
        assert "rust-review" in wf._determine_skills(tmp_path, files)

    def test_collect_files_skips_venv(self, tmp_path):
        (tmp_path / ".venv" / "lib").mkdir(parents=True)
        (tmp_path / ".venv" / "lib" / "dep.py").write_text("x = 1\n")
        (tmp_path / "own.py").write_text("x = 1\n")
        assert CodeReviewWorkflow()._collect_files(tmp_path) == ["own.py"]


class TestWorkflowHonorsConfiguration:
    """Configuration's exclude and skills were read by nothing, and
    configure() broke on a Configuration (PEN-8).
    """

    def test_workflow_honors_exclude_patterns(self, tmp_path):

        (tmp_path / "vendor").mkdir()
        (tmp_path / "vendor" / "a.py").write_text("x = 1\n")
        (tmp_path / "own.py").write_text("x = 1\n")
        wf = CodeReviewWorkflow(Configuration({"pensive": {"exclude": ["vendor/**"]}}))
        assert wf._collect_files(tmp_path) == ["own.py"]

    def test_enabled_skills_limit_the_selection(self, tmp_path):

        (tmp_path / "Makefile").write_text("all:\n\ttrue\n")
        wf = CodeReviewWorkflow(
            Configuration({"pensive": {"skills": ["makefile-review"]}})
        )
        assert wf._determine_skills(tmp_path, ["Makefile"]) == ["makefile-review"]

    def test_leading_double_star_exclude_matches_a_top_level_directory(self, tmp_path):
        """fnmatch needs the separator, so ``tests/a.py`` slipped past."""
        for rel in ("tests/a.py", "pkg/tests/b.py", "own.py"):
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / rel).write_text("x = 1\n")
        wf = CodeReviewWorkflow(
            Configuration({"pensive": {"exclude": ["**/tests/**"]}})
        )
        assert wf._collect_files(tmp_path) == ["own.py"]

    def test_a_dict_config_honors_exclude_and_skills(self, tmp_path):
        """``run_code_review`` passes a plain dict, which dropped both settings."""
        (tmp_path / "gen").mkdir()
        (tmp_path / "gen" / "lib.py").write_text("x = 1\n")
        (tmp_path / "app.py").write_text("x = 1\n")
        (tmp_path / "Makefile").write_text("all:\n\ttrue\n")
        wf = CodeReviewWorkflow(
            {"pensive": {"exclude": ["gen/*"], "skills": ["makefile-review"]}}
        )
        files = wf._collect_files(tmp_path)
        assert "gen/lib.py" not in files
        assert wf._determine_skills(tmp_path, files) == ["makefile-review"]

    def test_a_skills_filter_matching_nothing_falls_back_to_the_default(
        self, tmp_path, caplog
    ):
        """``skills: ["bug-review"]`` filtered a plain repo's selection to
        nothing, so the review ran no skill at all.
        """
        (tmp_path / "app.py").write_text("x = 1\n")
        wf = CodeReviewWorkflow(Configuration({"pensive": {"skills": ["bug-review"]}}))
        default = CodeReviewWorkflow()._determine_skills(tmp_path, ["app.py"])

        with caplog.at_level("WARNING"):
            report = wf.execute_full_review(tmp_path)

        assert report["metrics"]["skills_executed"] == len(default) > 0
        assert "bug-review" in caplog.text
        (warning,) = report["warnings"]
        assert "bug-review" in warning and "default selection" in warning

    def test_a_matching_skills_filter_reports_no_warning(self, tmp_path):
        (tmp_path / "Makefile").write_text("all:\n\ttrue\n")
        wf = CodeReviewWorkflow(
            Configuration({"pensive": {"skills": ["makefile-review"]}})
        )
        assert wf.execute_full_review(tmp_path)["warnings"] is None

    def test_collect_files_reviews_a_source_package_named_build(self, tmp_path):
        """The harden skip list dropped ``build``, ``dist`` and ``vendor``,
        so a source package ``src/build/`` was never reviewed.
        """
        for rel in ("src/build/m.py", "dist/d.py", "node_modules/x/i.js"):
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / rel).write_text("x = 1\n")
        assert sorted(CodeReviewWorkflow()._collect_files(tmp_path)) == [
            "dist/d.py",
            "src/build/m.py",
        ]

    def test_configure_accepts_a_configuration(self):

        wf = CodeReviewWorkflow(Configuration({}))
        wf.configure({"pensive": {"exclude": ["build/**"]}})
        assert wf.config.exclude_patterns == ["build/**"]
