"""Tests for quality_checker.py script."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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
    import ast as _ast

    tree = _ast.parse(
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
            "failures": [],
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
