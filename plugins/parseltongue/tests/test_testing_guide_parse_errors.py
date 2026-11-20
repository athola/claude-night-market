"""test-guide reported a clean result for code that does not parse (PAR-2).

Every other parseltongue command sets "error" for a SyntaxError.
"""

from __future__ import annotations

import asyncio

import pytest

from parseltongue.analysis.testing_guide import TestingGuideSkill


@pytest.mark.parametrize(
    ("code", "test_code"),
    [("def f(:\n", ""), ("def f():\n    return 1\n", "def test_f(:\n")],
    ids=["source", "test"],
)
def test_analyze_testing_reports_error_for_unparseable_input(
    code: str, test_code: str
) -> None:
    report = asyncio.run(TestingGuideSkill().analyze_testing(code, test_code))
    assert report["error"] == "Invalid Python syntax"
