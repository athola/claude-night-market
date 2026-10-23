"""Regression tests for verified API-review findings in pensive."""

from __future__ import annotations

import json
from importlib import metadata
from typing import TYPE_CHECKING

import pytest

from pensive import harden
from pensive.analysis.repository_analyzer import RepositoryAnalyzer
from pensive.config.configuration import Configuration
from pensive.reporting.formatters import MarkdownFormatter, SarifFormatter
from pensive.skills import architecture_review as pkg
from pensive.skills.architecture_review import _constants
from pensive.skills.makefile_review import MakefileReviewSkill
from pensive.skills.unified_review import UnifiedReviewSkill
from pensive.utils import content_parser
from pensive.utils.severity_mapper import count_by_severity
from pensive.workflows.code_review import CodeReviewWorkflow, _ReviewContext

if TYPE_CHECKING:
    from pathlib import Path


def test_context_get_file_content_without_name_returns_first_file(tmp_path: Path):
    (tmp_path / "Makefile").write_text("all:\n\techo hi\n")
    ctx = _ReviewContext(tmp_path, ["Makefile"])
    assert content_parser.get_file_content(ctx) == "all:\n\techo hi\n"
    assert "all:" in MakefileReviewSkill()._get_makefile_content(ctx)


def test_context_get_file_content_without_name_and_no_files_is_empty(tmp_path: Path):
    assert _ReviewContext(tmp_path, []).get_file_content() == ""


def test_full_review_survives_non_utf8_source(tmp_path: Path):
    (tmp_path / "b.py").write_bytes(b"\xff\xfe\x00")
    result = CodeReviewWorkflow().execute_full_review(tmp_path)
    assert "findings" in result


def test_merge_scalar_override_replaces_dict_value():
    merged = Configuration({"a": {"x": 1}}).merge(Configuration({"a": None}))
    assert merged._config["a"] is None


def test_analyze_without_repo_path_has_same_shape_as_with_path():
    empty = RepositoryAnalyzer().analyze()
    assert empty["languages"] == {}
    assert empty["build_systems"] == []
    assert empty["test_frameworks"] == []
    assert empty["file_count"] == 0


def test_architecture_review_all_excludes_private_names():
    assert not [n for n in pkg.__all__ if n.startswith("_")]
    assert not [n for n in _constants.__all__ if n.startswith("_")]


def test_harden_package_exports_documented_functions():
    for name in ("scan_source", "scan_path", "scan_directory", "run_cli"):
        assert name in harden.__all__
        assert callable(getattr(harden, name))


def test_sarif_tool_version_matches_package_metadata():
    sarif = json.loads(SarifFormatter().format([]))
    driver = sarif["runs"][0]["tool"]["driver"]
    assert driver["version"] == metadata.version("pensive")


def test_sarif_non_str_severity_maps_to_warning():
    finding = {"id": "X", "severity": None, "location": "a.py:1"}
    sarif = json.loads(SarifFormatter().format([finding]))
    run = sarif["runs"][0]
    assert run["results"][0]["level"] == "warning"
    assert run["tool"]["driver"]["rules"][0]["defaultConfiguration"] == {
        "level": "warning"
    }


def test_count_by_severity_maps_info_to_low_and_rejects_undefined_levels():
    counts = count_by_severity([{"severity": "info"}, {"severity": "high"}])
    assert counts == {"critical": 0, "high": 1, "medium": 0, "low": 1}
    with pytest.raises(ValueError, match="warning"):
        count_by_severity([{"severity": "warning"}])


def test_header_files_count_as_c_in_both_language_detectors(tmp_path) -> None:
    """`.h` belongs to C in both detectors.

    RepositoryAnalyzer counted it as C only because a later dict entry
    overwrote the C++ one; UnifiedReviewSkill read the same table and
    counted it for both.
    """
    (tmp_path / "foo.h").write_text("int f(void);\n")

    class _Ctx:
        def get_files(self):
            return ["foo.h"]

    unified = UnifiedReviewSkill().detect_languages(_Ctx())
    analyzer = RepositoryAnalyzer(tmp_path)._detect_languages_in_repo(tmp_path)
    assert unified.get("c", {}).get("files") == 1
    assert "cpp" not in unified or unified["cpp"].get("files", 0) == 0
    assert analyzer == {"c": 1}


def test_markdown_report_lists_an_advisory_finding_under_low() -> None:
    report = MarkdownFormatter().format(
        [{"severity": "ADVISORY", "issue": "uncited path", "file": "a.py"}]
    )
    assert "0 medium, 1 low" in report
    assert "## Low Priority" in report
    assert "uncited path" in report
