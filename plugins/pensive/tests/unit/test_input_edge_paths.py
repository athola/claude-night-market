"""Branches reached only by unusual input: odd locations, unreadable files,
missing optional packages, and report shapes the happy-path tests never build.
"""

from __future__ import annotations

import json
import os
import sys
from importlib import metadata
from typing import TYPE_CHECKING

import pytest

import pensive
from pensive.plugin.loader import discover_plugins
from pensive.reporting import formatters
from pensive.reporting.formatters import SarifFormatter
from pensive.skills.api_review import ApiReviewSkill
from pensive.skills.architecture_review import ArchitectureReviewSkill
from pensive.skills.base import AnalysisResult
from pensive.workflows.code_review import CodeReviewWorkflow

if TYPE_CHECKING:
    from pathlib import Path


class _Context:
    """Review context backed by a dict; ``broken`` paths raise on read."""

    def __init__(
        self,
        files: dict[str, str],
        broken: tuple[str, ...] = (),
        default_error: type[Exception] | None = None,
    ) -> None:
        self._files = files
        self._broken = broken
        self._default_error = default_error

    def get_files(self) -> list[str]:
        return [*self._broken, *self._files]

    def get_file_content(self, path: str) -> str:
        if path == "" and self._default_error is not None:
            raise self._default_error("no default file")
        if path in self._broken:
            raise OSError(f"cannot read {path}")
        return self._files.get(path, "")


class TestSarifLocations:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("location", "uri", "line"),
        [
            ("src/a.py:42", "src/a.py", 42),
            ("src/a.py:abc", "src/a.py", 1),
            ("src/a.py", "src/a.py", 1),
        ],
    )
    def test_location_is_split_into_uri_and_start_line(
        self, location: str, uri: str, line: int
    ) -> None:
        sarif = json.loads(SarifFormatter().format([{"location": location}]))
        physical = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]
        assert physical["artifactLocation"]["uri"] == uri
        assert physical["region"]["startLine"] == line

    @pytest.mark.unit
    def test_tool_version_falls_back_to_module_version_when_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def not_installed(name: str) -> str:
            raise metadata.PackageNotFoundError(name)

        monkeypatch.setattr(formatters.metadata, "version", not_installed)
        sarif = json.loads(SarifFormatter().format([]))
        assert sarif["runs"][0]["tool"]["driver"]["version"] == formatters.__version__


class TestDiscoverPlugins:
    @pytest.mark.unit
    def test_missing_path_yields_no_plugins(self, tmp_path: Path) -> None:
        assert discover_plugins(tmp_path / "absent") == []

    @pytest.mark.unit
    def test_file_path_yields_no_plugins(self, tmp_path: Path) -> None:
        target = tmp_path / "file.txt"
        target.write_text("x")
        assert discover_plugins(target) == []

    @pytest.mark.unit
    def test_classifies_json_and_python_plugins_and_skips_others(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "jsonplug").mkdir()
        (tmp_path / "jsonplug" / "plugin.json").write_text("{}")
        (tmp_path / "pyplug").mkdir()
        (tmp_path / "pyplug" / "__init__.py").write_text("")
        (tmp_path / "plain").mkdir()
        (tmp_path / "loose.py").write_text("")

        found = sorted(discover_plugins(str(tmp_path)), key=lambda p: p["name"])

        assert found == [
            {
                "name": "jsonplug",
                "path": str(tmp_path / "jsonplug"),
                "type": "json",
            },
            {"name": "pyplug", "path": str(tmp_path / "pyplug"), "type": "python"},
        ]

    @pytest.mark.unit
    @pytest.mark.skipif(
        sys.platform == "win32" or (hasattr(os, "geteuid") and os.geteuid() == 0),
        reason="POSIX permission bits that root ignores are required",
    )
    def test_unreadable_directory_yields_no_plugins(self, tmp_path: Path) -> None:
        locked = tmp_path / "locked"
        locked.mkdir()
        (locked / "plug").mkdir()
        (locked / "plug" / "plugin.json").write_text("{}")
        locked.chmod(0o000)
        try:
            assert discover_plugins(locked) == []
        finally:
            locked.chmod(0o755)


class TestCodeReviewWorkflowReporting:
    @pytest.mark.unit
    def test_summary_counts_findings_by_severity(self, tmp_path: Path) -> None:
        (tmp_path / "app.py").write_text("x = 1\n")
        findings = [
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "low"},
        ]

        class _Skill:
            def analyze(self, _context: object, _path: str) -> AnalysisResult:
                return AnalysisResult(info={"findings": findings})

        workflow = CodeReviewWorkflow()
        workflow._skill_registry["unified-review"] = _Skill()
        report = workflow.execute_full_review(tmp_path)

        assert report["summary"] == (
            "Found 4 issues: 1 critical, 2 high, 0 medium, 1 low"
        )
        assert report["recommendations"] == [
            "Address critical security issues immediately",
            "Review and fix high-priority issues",
        ]

    @pytest.mark.unit
    def test_skill_whose_module_fails_to_import_is_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        (tmp_path / "app.py").write_text("x = 1\n")
        monkeypatch.setitem(sys.modules, "pensive.skills.unified_review", None)

        report = CodeReviewWorkflow().execute_full_review(tmp_path)

        assert "unified-review" in report["skipped_skills"]

    @pytest.mark.unit
    def test_execute_skills_returns_none_for_unknown_skill(self) -> None:
        results = CodeReviewWorkflow().execute_skills(["no-such-review"], _Context({}))
        assert results == [None]

    @pytest.mark.unit
    def test_configure_merges_settings(self) -> None:
        workflow = CodeReviewWorkflow({"a": 1})
        workflow.configure({"b": 2})
        assert workflow.config == {"a": 1, "b": 2}


class TestArchitectureContentFallback:
    """Scalability and security checks read whichever file has content."""

    _SINGLETON = "class S:\n    def get(cls):\n        return cls._instance\n"

    @pytest.mark.unit
    @pytest.mark.parametrize("default_error", [OSError, NotImplementedError])
    def test_falls_back_to_per_file_reads_when_default_read_fails(
        self, default_error: type[Exception]
    ) -> None:
        context = _Context(
            {"svc.py": self._SINGLETON},
            broken=("unreadable.py",),
            default_error=default_error,
        )
        result = ArchitectureReviewSkill().analyze_scalability_patterns(context)
        assert [b["type"] for b in result["bottlenecks"]] == ["stateful_singleton"]

    @pytest.mark.unit
    def test_unreadable_files_only_yield_no_bottlenecks(self) -> None:
        context = _Context({}, broken=("a.py", "b.py"), default_error=OSError)
        result = ArchitectureReviewSkill().analyze_scalability_patterns(context)
        assert result["bottlenecks"] == []

    @pytest.mark.unit
    def test_flags_blocking_io_inside_a_loop_as_sequential(self) -> None:
        code = "for item in items:\n    requests.get(item)\n"
        result = ArchitectureReviewSkill().analyze_scalability_patterns(
            _Context({"": code})
        )
        assert "sequential_processing" in [b["type"] for b in result["bottlenecks"]]

    @pytest.mark.unit
    def test_flags_formatted_sql_passed_to_execute(self) -> None:
        code = 'cursor.execute(f"SELECT * FROM t WHERE id = {uid}")\n'
        result = ArchitectureReviewSkill().analyze_security_architecture(
            _Context({"": code})
        )
        assert "sql_injection" in [v["type"] for v in result["vulnerabilities"]]

    @pytest.mark.unit
    def test_parameterized_execute_is_not_flagged_as_sql_injection(self) -> None:
        code = 'cursor.execute("SELECT * FROM t WHERE id = ?", (uid,))\n'
        result = ArchitectureReviewSkill().analyze_security_architecture(
            _Context({"": code})
        )
        assert "sql_injection" not in [v["type"] for v in result["vulnerabilities"]]


class TestRustApiCounts:
    @pytest.mark.unit
    def test_constructors_count_as_methods_but_not_functions(self) -> None:
        code = (
            "pub struct Point { x: i32 }\n"
            "impl Point {\n"
            "    pub fn new() -> Self { Point { x: 0 } }\n"
            "    pub fn x(&self) -> i32 { self.x }\n"
            "}\n"
            "pub fn origin() -> Point { Point::new() }\n"
        )
        counts = ApiReviewSkill().analyze_rust_api(_Context({"lib.rs": code}), "lib.rs")
        assert counts == {"structs": 1, "functions": 2, "public_methods": 3}


class TestLazyPackageExports:
    @pytest.mark.unit
    def test_unknown_attribute_raises_attribute_error(self) -> None:
        with pytest.raises(AttributeError, match="no_such_export"):
            _ = pensive.no_such_export

    @pytest.mark.unit
    def test_dir_lists_lazy_exports(self) -> None:
        assert set(pensive._EXPORTS) <= set(dir(pensive))
