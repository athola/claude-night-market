"""Regression tests from the API review."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from parseltongue import cli
from parseltongue.analysis import pattern_matching
from parseltongue.analysis.compatibility_checker import CompatibilityChecker
from parseltongue.analysis.testing_guide import analyze_testing

if TYPE_CHECKING:
    from pathlib import Path

MATCH_AND_WALRUS = (
    "def f(x):\n"
    "    if (n := len(x)) > 1:\n"
    "        pass\n"
    "    match x:\n"
    "        case 1:\n"
    "            return n\n"
)


def test_minimum_version_compares_numerically_not_lexically():
    result = CompatibilityChecker().check_compatibility(MATCH_AND_WALRUS, ["3.9"])
    assert result["minimum_version"] == "3.10"
    assert result["compatible_versions"] == []


def test_walrus_only_code_is_compatible_with_3_8_and_later():
    result = CompatibilityChecker().check_compatibility("if (n := 1) > 0:\n    pass\n")
    assert result["compatible_versions"] == ["3.8", "3.9", "3.10", "3.11", "3.12"]


def test_analyze_testing_wrapper_forwards_test_code():
    result = asyncio.run(
        analyze_testing(
            "def add(a, b):\n    return a + b\n", "def test_add():\n    pass\n"
        )
    )
    assert result["findings"]["test_analysis"] != {}


def test_cli_test_guide_accepts_test_path(tmp_path: Path, capsys):
    src = tmp_path / "mod.py"
    src.write_text("def add(a, b):\n    return a + b\n")
    tests = tmp_path / "test_mod.py"
    tests.write_text("def test_add():\n    pass\n")
    rc = cli.main(["test-guide", str(src), "--test-path", str(tests)])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["findings"]["test_analysis"] != {}


def test_pattern_matching_all_exports_only_public_skill():
    assert pattern_matching.__all__ == ["PatternMatchingSkill"]


def test_cli_exits_nonzero_when_analysis_reports_error(tmp_path: Path, capsys):
    bad = tmp_path / "bad.py"
    bad.write_text("def f(:\n")
    rc = cli.main(["analyze-async", str(bad)])
    assert rc != 0
    assert "error" in json.loads(capsys.readouterr().out)
