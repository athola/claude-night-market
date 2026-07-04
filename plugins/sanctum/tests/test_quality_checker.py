"""Tests for quality_checker.py script."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "quality_checker.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "sanctum_quality_checker", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_quality_checker"] = module
    spec.loader.exec_module(module)
    return module


def _good_test_file(tmp_path: Path) -> Path:
    """A test file that scores well on quality."""
    p = tmp_path / "test_good.py"
    p.write_text(
        '"""Good test module covering high quality patterns."""\n'
        "import pytest\n"
        "\n"
        "def test_addition_returns_sum():\n"
        '    """Test addition.\n'
        "\n"
        "    GIVEN two integers\n"
        "    WHEN they are added\n"
        "    THEN the result is the arithmetic sum\n"
        "    AND the operation is commutative\n"
        '    """\n'
        "    assert 1 + 1 == 2\n"
        "    assert 2 + 1 == 3\n"
        "\n"
        "def test_subtraction_returns_difference():\n"
        '    """Test subtraction.\n'
        "\n"
        "    GIVEN two integers\n"
        "    WHEN one is subtracted from the other\n"
        "    THEN the result is the difference\n"
        "    AND ordering matters\n"
        '    """\n'
        "    assert 3 - 1 == 2\n"
        "    assert 1 - 3 == -2\n"
    )
    return p


def _bad_test_file(tmp_path: Path) -> Path:
    """A test file with several quality problems."""
    p = tmp_path / "test_bad.py"
    p.write_text(
        "def test_x():\n"  # short name
        "    pass\n"  # no assertion
        "\n"
        "def test_vague():\n"
        "    result = 5\n"
        "    assert result == 5\n"  # vague 'result' assertion
    )
    return p


# ---------------------- enum + dataclass ----------------------


def test_quality_level_enum_values():
    qc = _load_script()
    assert qc.QualityLevel.EXCELLENT.value == "excellent"
    assert qc.QualityLevel.POOR.value == "poor"


def test_quality_issue_dataclass_defaults():
    qc = _load_script()
    issue = qc.QualityIssue("error", "structure", "msg")
    assert issue.severity == "error"
    assert issue.line_number is None
    assert issue.suggestion is None


# ---------------------- static analysis ----------------------


def test_static_analysis_missing_file_records_error(tmp_path):
    qc = _load_script()
    checker = qc.TestQualityChecker(tmp_path / "nope.py")
    out = checker.run_static_analysis()
    assert any(
        i.message.startswith("Test file not found") for i in out["structure_issues"]
    )


def test_static_analysis_syntax_error_records_error(tmp_path):
    qc = _load_script()
    f = tmp_path / "broken.py"
    f.write_text("def : :: \n")
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("Syntax error" in i.message for i in out["structure_issues"])


def test_static_analysis_no_test_functions_warns(tmp_path):
    qc = _load_script()
    f = tmp_path / "test_empty.py"
    f.write_text("# nothing here\n")
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any(i.message == "No test functions found" for i in out["structure_issues"])


def test_static_analysis_no_imports_warns(tmp_path):
    qc = _load_script()
    f = tmp_path / "test_no_imports.py"
    f.write_text("def test_foo():\n    assert True\n")
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any(
        i.message.startswith("No imports found") for i in out["structure_issues"]
    )


def test_static_analysis_short_name_flagged(tmp_path):
    qc = _load_script()
    f = tmp_path / "test_short.py"
    f.write_text("import pytest\ndef test_x():\n    assert True\n")
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("too short" in i.message for i in out["naming_issues"])


def test_static_analysis_missing_assertion_flagged(tmp_path):
    qc = _load_script()
    f = tmp_path / "test_no_assert.py"
    f.write_text("import pytest\n\ndef test_does_a_thing_without_assert():\n    pass\n")
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("no assertions" in i.message for i in out["assertion_issues"])


def test_pytest_raises_block_counts_as_assertion(tmp_path):
    """A test asserting only via ``pytest.raises`` is not flagged empty.

    GIVEN a test that asserts behavior solely with ``pytest.raises``
    WHEN the static analyzer checks assertion quality
    THEN the test is not reported as having no assertions
    AND the context manager is recognized as a real assertion
    """
    qc = _load_script()
    f = tmp_path / "test_raises_only.py"
    f.write_text(
        "import pytest\n\n"
        "def test_rejects_bad_input():\n"
        "    with pytest.raises(ValueError):\n"
        "        raise ValueError('bad')\n"
    )
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert not any("no assertions" in i.message for i in out["assertion_issues"])


def test_static_analysis_vague_assertion_flagged(tmp_path):
    qc = _load_script()
    f = _bad_test_file(tmp_path)
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("Vague assertion" in i.message for i in out["assertion_issues"])


def test_static_analysis_bdd_missing_keywords(tmp_path):
    qc = _load_script()
    f = tmp_path / "test_bdd.py"
    f.write_text(
        "import pytest\n\n"
        "def test_some_thing_behavior():\n"
        '    """No BDD keywords here."""\n'
        "    assert True\n"
    )
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("missing BDD" in i.message for i in out["bdd_compliance"])


def test_bdd_check_detects_missing_keywords_in_single_quoted_docstring(tmp_path):
    """AST-based BDD check flags missing keywords even for single-quoted docstrings."""
    qc = _load_script()
    f = tmp_path / "test_single_quote.py"
    f.write_text(
        "import pytest\n\n"
        "def test_some_thing_behavior():\n"
        "    'No BDD keywords here.'\n"
        "    assert True\n"
    )
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("missing BDD" in i.message for i in out["bdd_compliance"])


def test_static_analysis_documentation_lacks_module_docstring(tmp_path):
    qc = _load_script()
    f = tmp_path / "test_docs.py"
    f.write_text("import pytest\n\ndef test_some_thing_behavior():\n    assert True\n")
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("module docstring" in i.message for i in out["documentation"])


# ---------------------- metrics ----------------------


def test_calculate_metrics_missing_file_returns_zeros(tmp_path):
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path / "nope.py")
    m = c.calculate_metrics()
    assert m["test_count"] == 0
    assert m["assertion_count"] == 0


def test_calculate_metrics_syntax_error_returns_zeros(tmp_path):
    qc = _load_script()
    f = tmp_path / "broken.py"
    f.write_text("not :: valid\n")
    c = qc.TestQualityChecker(f)
    m = c.calculate_metrics()
    assert m["test_count"] == 0


def test_calculate_metrics_counts_tests_and_assertions(tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)
    c = qc.TestQualityChecker(f)
    m = c.calculate_metrics()
    assert m["test_count"] == 2
    assert m["assertion_count"] >= 4
    assert m["average_test_length"] > 0
    assert m["complexity_score"] >= 1
    assert m["documentation_ratio"] > 0


def test_calculate_complexity_counts_branches():
    qc = _load_script()
    tree = ast.parse(
        "def f(x):\n"
        "    if x:\n"
        "        for i in range(2):\n"
        "            pass\n"
        "    return x and (x or 1)\n"
    )
    c = qc.TestQualityChecker(Path("/tmp"))  # noqa: S108 - test fixture path, not user input
    score = c._calculate_complexity(tree)
    # base 1 + If 1 + For 1 + 2 BoolOps with 2 values each = 1+1+1+1+1 = 5
    assert score >= 5


# ---------------------- score + level + recommendations ----------------------


def test_determine_quality_level_thresholds(tmp_path):
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    assert c._determine_quality_level(95) == qc.QualityLevel.EXCELLENT
    assert c._determine_quality_level(85) == qc.QualityLevel.GOOD
    assert c._determine_quality_level(75) == qc.QualityLevel.FAIR
    assert c._determine_quality_level(50) == qc.QualityLevel.POOR


def test_calculate_overall_score_clamps_to_range(tmp_path):
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    # Build a synthetic result with many errors to push score negative
    err = qc.QualityIssue("error", "structure", "x")
    results = {
        "static_analysis": {
            "structure_issues": [err] * 50,
            "naming_issues": [],
            "assertion_issues": [],
            "bdd_compliance": [],
            "documentation": [],
        },
        "dynamic_validation": {
            "execution_result": 1,
            "test_duration": 0,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 0,
        },
        "metrics": {
            "test_count": 0,
            "assertion_count": 0,
            "average_test_length": 0,
            "complexity_score": 0,
            "documentation_ratio": 0,
        },
    }
    score = c._calculate_overall_score(results)
    assert score == 0


def test_passing_tests_not_penalized_for_coverage_gate_exit(tmp_path):
    """A nonzero pytest exit with no failures does not cost the run points.

    GIVEN a result where every test passed but pytest exited nonzero
        (for example because a coverage threshold was not met)
    WHEN the overall score is calculated
    THEN no execution penalty is applied
    AND a clean run scores the full 100
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    results = {
        "static_analysis": {
            "structure_issues": [],
            "naming_issues": [],
            "assertion_issues": [],
            "bdd_compliance": [],
            "documentation": [],
        },
        "dynamic_validation": {
            "execution_result": 1,
            "test_duration": 0,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 5,
        },
        "metrics": {
            "test_count": 5,
            "assertion_count": 5,
            "average_test_length": 10,
            "complexity_score": 0,
            "documentation_ratio": 1.0,
        },
    }
    score = c._calculate_overall_score(results)
    assert score == 100


def test_real_test_failures_still_penalized(tmp_path):
    """Genuine test failures still incur the execution penalty.

    GIVEN a result that records an actual test failure
    WHEN the overall score is calculated
    THEN the execution penalty is applied
    AND the score drops below a clean run
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    results = {
        "static_analysis": {
            "structure_issues": [],
            "naming_issues": [],
            "assertion_issues": [],
            "bdd_compliance": [],
            "documentation": [],
        },
        "dynamic_validation": {
            "execution_result": 1,
            "test_duration": 0,
            "failures": ["test_x failed"],
            "errors": [],
            "skipped": 0,
            "passed": 4,
        },
        "metrics": {
            "test_count": 5,
            "assertion_count": 5,
            "average_test_length": 10,
            "complexity_score": 0,
            "documentation_ratio": 1.0,
        },
    }
    score = c._calculate_overall_score(results)
    assert score <= 80


def test_parse_report_usage_error_is_not_a_failure(tmp_path):
    """A missing report with a usage-error exit code is not a failure.

    GIVEN no JSON report and a pytest usage-error return code (4),
        as happens when the json-report plugin is not installed
    WHEN the report is parsed with that fallback return code
    THEN no synthetic failure or error is recorded
    AND the run is treated as unmeasured rather than failed
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    parsed = c._parse_test_report(str(tmp_path / "missing.json"), fallback_returncode=4)
    assert parsed["failures"] == 0
    assert parsed["errors"] == 0


def test_parse_report_real_failure_returncode_records_failure(tmp_path):
    """A missing report with exit code 1 still records a real failure.

    GIVEN no JSON report and a pytest exit code of 1 (tests failed)
    WHEN the report is parsed with that fallback return code
    THEN a synthetic failure is recorded
    AND a clean pass is not assumed
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    parsed = c._parse_test_report(str(tmp_path / "missing.json"), fallback_returncode=1)
    assert parsed["failures"] == 1


def test_generate_recommendations_covers_branches(tmp_path):
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    issue = qc.QualityIssue("warning", "x", "y")
    results = {
        "static_analysis": {
            "structure_issues": [issue],
            "naming_issues": [issue],
            "assertion_issues": [issue],
            "bdd_compliance": [issue],
            "documentation": [issue],
        },
        "dynamic_validation": {
            "execution_result": 1,
            "test_duration": 999,
            "failures": ["test_x failed"],
            "errors": [],
            "skipped": 0,
            "passed": 0,
        },
        "metrics": {
            "test_count": 1,
            "assertion_count": 0,
            "average_test_length": 999,
            "complexity_score": 0,
            "documentation_ratio": 0,
        },
    }
    recs = c._generate_recommendations(results)
    joined = "|".join(recs)
    assert "structural issues" in joined.lower()
    assert "snake_case" in joined.lower() or "descriptive" in joined.lower()
    assert "assertions" in joined.lower()
    assert "bdd" in joined.lower() or "given" in joined.lower()
    assert "documentation" in joined.lower()
    assert "failing tests" in joined.lower()
    assert "performance" in joined.lower() or "quickly" in joined.lower()
    assert "long tests" in joined.lower() or "smaller" in joined.lower()


def _clean_results(dynamic: dict) -> dict:
    """Results with no static issues and clean metrics, parameterized dynamic."""
    return {
        "static_analysis": {
            "structure_issues": [],
            "naming_issues": [],
            "assertion_issues": [],
            "bdd_compliance": [],
            "documentation": [],
        },
        "dynamic_validation": dynamic,
        "metrics": {
            "test_count": 5,
            "assertion_count": 5,
            "average_test_length": 10,
            "complexity_score": 0,
            "documentation_ratio": 1.0,
        },
    }


def test_recommendations_omit_fix_tests_when_only_exit_code_nonzero(tmp_path):
    """A coverage-gate failure (nonzero exit, no failures) gives no fix-tests rec.

    GIVEN a run with execution_result=1 but empty failures and errors
        (the coverage gate failed while every test passed)
    WHEN recommendations are generated
    THEN 'Fix failing tests' is absent
    AND this is the exact regression the failures/errors gating prevents
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    results = _clean_results(
        {
            "execution_result": 1,
            "test_duration": 0,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 5,
        }
    )
    recs = c._generate_recommendations(results)
    joined = "|".join(recs).lower()
    assert "fix failing tests" not in joined


def test_inconclusive_run_is_surfaced_in_score_and_recommendations(tmp_path):
    """An inconclusive run (pytest exit >= 2) is penalized and flagged.

    GIVEN a dynamic result carrying the inconclusive flag (a crashed or
        uncollectable suite) with no recorded failures or errors
    WHEN the score and recommendations are computed
    THEN the score is penalized below a clean pass
    AND a recommendation surfaces the inconclusive run
    AND the misleading 'Fix failing tests' message is not emitted
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    results = _clean_results(
        {
            "execution_result": 4,
            "test_duration": 0,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 0,
            "inconclusive": True,
        }
    )
    score = c._calculate_overall_score(results)
    assert score <= 80
    recs = c._generate_recommendations(results)
    joined = "|".join(recs).lower()
    assert "inconclusive" in joined
    assert "fix failing tests" not in joined


def test_parse_report_inconclusive_flag_set_for_exit_two_plus(tmp_path):
    """A missing report with exit >= 2 carries the inconclusive flag.

    GIVEN no JSON report and a pytest exit code of 2 (interrupted)
    WHEN the report is parsed with that fallback return code
    THEN the result is flagged inconclusive
    AND no synthetic failure or error is recorded
    """
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path)
    parsed = c._parse_test_report(str(tmp_path / "missing.json"), fallback_returncode=2)
    assert parsed.get("inconclusive") is True
    assert parsed["failures"] == 0
    assert parsed["errors"] == 0


# ---------------------- run_full_validation ----------------------


def test_run_full_validation_produces_score(tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)
    c = qc.TestQualityChecker(f)
    results = c.run_full_validation()
    assert "quality_score" in results
    assert "quality_level" in results
    assert isinstance(results["quality_score"], int)


# ---------------------- format_report ----------------------


def test_format_report_renders_sections(tmp_path):
    qc = _load_script()
    fake_results = {
        "quality_score": 88,
        "quality_level": "good",
        "dynamic_validation": {
            "passed": 5,
            "failures": 0,
            "errors": [],
            "test_duration": 0.4,
        },
        "metrics": {
            "test_count": 5,
            "assertion_count": 12,
            "average_test_length": 6.4,
            "documentation_ratio": 0.3,
        },
        "recommendations": ["one", "two"],
    }
    out = qc.format_report(fake_results)
    assert "Test Quality Report" in out
    assert "Overall Quality Score: 88" in out
    assert "1. one" in out
    assert "2. two" in out


# ---------------------- main CLI ----------------------


def test_main_no_args_prints_help(monkeypatch, capsys):
    qc = _load_script()
    monkeypatch.setattr(sys, "argv", ["quality_checker.py"])
    qc.main()
    out = capsys.readouterr().out
    assert "Check test quality" in out


def test_main_check_missing_path_writes_error(monkeypatch, capsys, tmp_path):
    qc = _load_script()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "quality_checker.py",
            "--check",
            str(tmp_path / "missing.py"),
            "--output-json",
        ],
    )
    qc.main()
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload.get("success") is False


def test_main_check_human_output_to_stdout(monkeypatch, capsys, tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)

    # Stub out dynamic validation to avoid running pytest in a subprocess
    def _no_run(self):  # noqa: ARG001 - test stub matches mocked interface
        return {
            "execution_result": 0,
            "test_duration": 0.1,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 2,
        }

    monkeypatch.setattr(qc.TestQualityChecker, "run_dynamic_validation", _no_run)
    monkeypatch.setattr(
        sys,
        "argv",
        ["quality_checker.py", "--check", str(f)],
    )
    qc.main()
    out = capsys.readouterr().out
    assert "Test Quality Report" in out


def test_main_check_writes_to_output_file(monkeypatch, tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)
    out_file = tmp_path / "report.txt"

    def _no_run(self):  # noqa: ARG001 - test stub matches mocked interface
        return {
            "execution_result": 0,
            "test_duration": 0.1,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 2,
        }

    monkeypatch.setattr(qc.TestQualityChecker, "run_dynamic_validation", _no_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "quality_checker.py",
            "--check",
            str(f),
            "--output",
            str(out_file),
        ],
    )
    qc.main()
    assert out_file.exists()
    assert "Test Quality Report" in out_file.read_text()


def test_main_check_json_to_stdout(monkeypatch, capsys, tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)

    def _no_run(self):  # noqa: ARG001 - test stub matches mocked interface
        return {
            "execution_result": 0,
            "test_duration": 0.1,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 2,
        }

    monkeypatch.setattr(qc.TestQualityChecker, "run_dynamic_validation", _no_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "quality_checker.py",
            "--check",
            str(f),
            "--output-json",
        ],
    )
    qc.main()
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload.get("success") is True
    assert "data" in payload


def test_main_check_json_to_output_file(monkeypatch, tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)
    out_file = tmp_path / "report.json"

    def _no_run(self):  # noqa: ARG001 - test stub matches mocked interface
        return {
            "execution_result": 0,
            "test_duration": 0.1,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 2,
        }

    monkeypatch.setattr(qc.TestQualityChecker, "run_dynamic_validation", _no_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "quality_checker.py",
            "--check",
            str(f),
            "--output",
            str(out_file),
            "--output-json",
        ],
    )
    qc.main()
    payload = json.loads(out_file.read_text())
    assert payload["success"] is True


def test_main_handles_internal_exception(monkeypatch, capsys, tmp_path):
    qc = _load_script()
    f = _good_test_file(tmp_path)

    def _boom(self):  # noqa: ARG001 - test stub matches mocked interface
        raise RuntimeError("explode")

    monkeypatch.setattr(qc.TestQualityChecker, "run_full_validation", _boom)
    monkeypatch.setattr(
        sys,
        "argv",
        ["quality_checker.py", "--check", str(f), "--output-json"],
    )
    qc.main()
    payload = json.loads(capsys.readouterr().out)
    assert payload["success"] is False


def test_run_dynamic_validation_runs_against_self(tmp_path):
    """Smoke test of dynamic validation against a real (passing) test file."""
    qc = _load_script()
    f = tmp_path / "test_truth.py"
    f.write_text('"""Truth test."""\ndef test_truth():\n    assert True\n')
    c = qc.TestQualityChecker(f)
    out = c.run_dynamic_validation()
    assert "execution_result" in out
    assert "test_duration" in out


def test_pytest_warns_block_counts_as_assertion(tmp_path):
    """A test asserting only via ``pytest.warns`` is not flagged empty.

    GIVEN a test that asserts behavior solely with ``pytest.warns``
    WHEN the static analyzer checks assertion quality
    THEN the test is not reported as having no assertions
    AND the warns context manager is recognized like raises
    """
    qc = _load_script()
    f = tmp_path / "test_warns_only.py"
    f.write_text(
        "import pytest\n\n"
        "def test_emits_warning():\n"
        "    with pytest.warns(UserWarning):\n"
        "        import warnings\n"
        "        warnings.warn('x', UserWarning)\n"
    )
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert not any("no assertions" in i.message for i in out["assertion_issues"])


def test_run_dynamic_validation_uses_json_report_when_plugin_present(
    tmp_path, monkeypatch
):
    """The json-report flag is used and parsed when the plugin is present.

    GIVEN the json-report plugin reports as installed
    WHEN dynamic validation runs the target test file
    THEN pytest is invoked with the --json-report flag
    AND the produced report's pass count is parsed into the result
    """
    qc = _load_script()
    f = tmp_path / "test_x.py"
    f.write_text('"""t."""\ndef test_x():\n    assert True\n')
    c = qc.TestQualityChecker(f)

    monkeypatch.setattr(qc.importlib.util, "find_spec", lambda _name: object())

    captured: dict = {}

    class _Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(cmd, **_kwargs):
        captured["cmd"] = cmd
        for arg in cmd:
            if arg.startswith("--json-report-file="):
                with open(arg.split("=", 1)[1], "w") as fh:
                    json.dump(
                        {"summary": {"passed": 3, "failed": 0, "error": 0}},
                        fh,
                    )
        return _Result()

    monkeypatch.setattr(qc.subprocess, "run", fake_run)

    out = c.run_dynamic_validation()

    assert "--json-report" in captured["cmd"]
    assert out["passed"] == 3


# ---- SAN-008: _is_vague_result_assertion helper ----


def test_is_vague_result_assertion_exists():
    """_is_vague_result_assertion must be a callable on TestQualityChecker."""
    qc = _load_script()
    assert callable(getattr(qc.TestQualityChecker, "_is_vague_result_assertion", None))


def test_is_vague_result_assertion_true_for_result_compare(tmp_path):
    """Identifies 'assert result ==' as vague."""
    qc = _load_script()
    node = ast.parse("assert result == 5").body[0]
    c = qc.TestQualityChecker(tmp_path / "t.py")
    assert c._is_vague_result_assertion(node) is True


def test_is_vague_result_assertion_false_for_specific_compare(tmp_path):
    """Does not flag 'assert value.status == ok' as vague."""
    qc = _load_script()
    node = ast.parse("assert response.status == 'ok'").body[0]
    c = qc.TestQualityChecker(tmp_path / "t.py")
    assert c._is_vague_result_assertion(node) is False


def test_is_vague_result_assertion_false_for_non_compare(tmp_path):
    """Does not flag a bare bool assertion as vague."""
    qc = _load_script()
    node = ast.parse("assert result").body[0]
    c = qc.TestQualityChecker(tmp_path / "t.py")
    assert c._is_vague_result_assertion(node) is False


def test_check_assertion_quality_still_flags_vague_result(tmp_path):
    """Behavior guard: vague assertion is still reported after refactor."""
    qc = _load_script()
    f = tmp_path / "test_vague.py"
    f.write_text(
        "import x\ndef test_something_returns_correctly():\n"
        "    result = do_thing()\n"
        "    assert result == 5\n"
    )
    checker = qc.TestQualityChecker(f)
    out = checker.run_static_analysis()
    assert any("Vague assertion" in i.message for i in out["assertion_issues"])


# ---- SAN-009: _parse_test_report helper ----


def test_parse_test_report_exists():
    """_parse_test_report must be a callable on TestQualityChecker."""
    qc = _load_script()
    assert callable(getattr(qc.TestQualityChecker, "_parse_test_report", None))


def test_parse_test_report_reads_valid_json(tmp_path):
    """Returns parsed summary dict from a valid JSON report file."""
    qc = _load_script()
    report_path = tmp_path / "report.json"
    report_path.write_text(
        json.dumps({"summary": {"passed": 3, "failed": 1, "error": 0, "skipped": 0}})
    )
    c = qc.TestQualityChecker(tmp_path / "t.py")
    result = c._parse_test_report(report_path, fallback_returncode=0)
    assert result["passed"] == 3
    assert result["failures"] == 1


def test_parse_test_report_falls_back_on_missing_file(tmp_path):
    """Returns fallback dict when report file does not exist."""
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path / "t.py")
    result = c._parse_test_report(tmp_path / "missing.json", fallback_returncode=0)
    assert result["passed"] == 1
    assert result["failures"] == 0


def test_parse_test_report_falls_back_on_nonzero_rc(tmp_path):
    """Returns failures=1 when fallback_returncode is non-zero."""
    qc = _load_script()
    c = qc.TestQualityChecker(tmp_path / "t.py")
    result = c._parse_test_report(tmp_path / "missing.json", fallback_returncode=1)
    assert result["failures"] == 1
    assert result["passed"] == 0


# ---- SAN-010: _run_check_or_validate helper ----


def test_run_check_or_validate_exists():
    """_run_check_or_validate must be a module-level callable."""
    qc = _load_script()
    assert callable(getattr(qc, "_run_check_or_validate", None))


def test_run_check_or_validate_returns_report_str(monkeypatch, tmp_path):
    """Behavior guard: check command still produces a human report via helper."""
    qc = _load_script()
    f = _good_test_file(tmp_path)

    def _no_run(self):  # noqa: ARG001 - test stub
        return {
            "execution_result": 0,
            "test_duration": 0.1,
            "failures": [],
            "errors": [],
            "skipped": 0,
            "passed": 2,
        }

    monkeypatch.setattr(qc.TestQualityChecker, "run_dynamic_validation", _no_run)
    args = argparse.Namespace(
        check=str(f), validate=None, output=None, output_json=False, coverage=None
    )
    checker = qc.TestQualityChecker(f)
    # Must not raise
    qc._run_check_or_validate(checker, args)


# ---------------------------------------------------------------------------
# SAN-019: cache file content to avoid double-reads
# ---------------------------------------------------------------------------


class TestSAN019FileCaching:
    """TestQualityChecker must read test_path at most once per instance.

    GIVEN a checker whose test file contains valid Python
    WHEN run_static_analysis() and calculate_metrics() are both called
    THEN the underlying file is opened exactly once.
    """

    def test_file_opened_once_across_static_and_metrics(self, tmp_path: Path) -> None:
        qc = _load_script()
        test_file = tmp_path / "test_sample.py"
        test_file.write_text("def test_foo():\n    assert True\n")

        checker = qc.TestQualityChecker(test_file)
        open_calls: list[str] = []
        real_open = open

        def counting_open(path, *args, **kwargs):
            open_calls.append(str(path))
            return real_open(path, *args, **kwargs)

        with patch("builtins.open", side_effect=counting_open):
            checker.run_static_analysis()
            checker.calculate_metrics()

        file_reads = [c for c in open_calls if str(test_file) in c]
        assert len(file_reads) <= 1, (
            f"test_path opened {len(file_reads)} times; expected at most 1"
        )


def test_dynamic_validation_runs_without_python_on_path(tmp_path):
    """Dynamic validation must not depend on `python` being on PATH.

    GIVEN an environment whose PATH resolves no bare `python`
    (Debian/WSL boxes ship only `python3`; simulated with an empty PATH)
    WHEN run_dynamic_validation executes a trivial passing test file
    THEN pytest runs via the interpreter already executing the checker
    (sys.executable) and reports the pass,
    AND no "Test setup failed" error is recorded
    """
    qc = _load_script()
    f = _good_test_file(tmp_path)
    checker = qc.TestQualityChecker(f)
    with patch.dict(qc.os.environ, {"PATH": ""}):
        validation = checker.run_dynamic_validation()

    # On exception paths "errors" is a list of message strings; on a
    # successful run the report parser stores an error *count*.
    errors = validation["errors"]
    setup_failures = (
        [e for e in errors if "Test setup failed" in str(e)]
        if isinstance(errors, list)
        else []
    )
    assert not setup_failures, f"checker depends on PATH python: {setup_failures}"
    assert validation["execution_result"] == 0
