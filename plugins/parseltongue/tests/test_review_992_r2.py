"""Regression tests for PR #992 review findings R2-S9 and R2-S10."""

from __future__ import annotations

import pytest

from parseltongue.analysis.async_analysis.blocking_detection import (
    detect_missing_await,
)
from parseltongue.analysis.code_transformation import CodeTransformationSkill


@pytest.mark.unit
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("x = 1\ry = dict()\n", "x = 1\ry = {}\n"),
        ("x = 1\r\ny = dict()\r\n", "x = 1\r\ny = {}\r\n"),
        ("x = 1\n\ry = dict()\n", "x = 1\n\ry = {}\n"),
    ],
)
async def test_modernize_rewrites_the_right_line_with_cr_line_endings(
    source: str, expected: str
) -> None:
    result = await CodeTransformationSkill().transform_code(source, "modernize")

    assert result["transformed_code"] == expected


@pytest.mark.unit
async def test_self_call_ignores_async_method_of_another_class() -> None:
    code = (
        "class A:\n"
        "    async def f(self): ...\n"
        "class B:\n"
        "    def f(self): ...\n"
        "    async def run(self):\n"
        "        self.f()\n"
    )

    report = await detect_missing_await(code)

    assert report["missing_awaits"] == {}


@pytest.mark.unit
async def test_self_call_flags_async_method_of_enclosing_class() -> None:
    code = (
        "class A:\n"
        "    async def f(self): ...\n"
        "    async def run(self):\n"
        "        self.f()\n"
    )

    report = await detect_missing_await(code)

    assert report["missing_awaits"]["run"]["line_numbers"] == [4]
