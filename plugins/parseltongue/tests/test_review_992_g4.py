"""Regression tests for PR #992 review findings S13, S14, S15."""

from __future__ import annotations

import pytest

from parseltongue.analysis.async_analysis.blocking_detection import (
    detect_missing_await,
)
from parseltongue.analysis.compatibility_checker import CompatibilityChecker


@pytest.mark.unit
async def test_transform_omits_edit_nested_inside_a_kept_edit(
    code_transformation_skill,
) -> None:
    report = await code_transformation_skill.transform_code(
        "a = list(x for x in dict())\n", "modernize"
    )

    kinds = [t["type"] for t in report["transformations"]]
    assert "dict()" in report["transformed_code"]
    assert "dict_literal" not in kinds
    assert kinds == ["list_comprehension"]


@pytest.mark.unit
async def test_transform_reports_every_applied_kind(
    code_transformation_skill,
) -> None:
    report = await code_transformation_skill.transform_code(
        "a = dict()\nb = list(y for y in z)\n", "modernize"
    )

    kinds = {t["type"] for t in report["transformations"]}
    assert "dict_literal" in kinds
    assert len(kinds) == 2


@pytest.mark.unit
async def test_missing_await_ignores_coroutine_awaited_later() -> None:
    code = (
        "import asyncio\n"
        "async def work(): ...\n"
        "async def main():\n"
        "    t = work()\n"
        "    await t\n"
        "    c = work()\n"
        "    r = await asyncio.gather(c)\n"
        "    d = work()\n"
        "    e = asyncio.create_task(d)\n"
    )

    report = await detect_missing_await(code)

    assert report["missing_awaits"] == {}


@pytest.mark.unit
async def test_missing_await_flags_assigned_coroutine_never_used() -> None:
    code = "async def work(): ...\nasync def main():\n    t = work()\n"

    report = await detect_missing_await(code)

    assert report["missing_awaits"]["main"]["line_numbers"] == [3]


@pytest.mark.unit
def test_union_annotations_yield_one_issue_per_feature() -> None:
    code = (
        "def f(a: int | str, b: int | None) -> int | None:\n"
        "    x: int | None = None\n"
        "    return x\n"
    )

    report = CompatibilityChecker().check_compatibility(code, ["3.9", "3.10"])

    features = [issue["feature"] for issue in report["issues"]]
    assert features.count("union_type_syntax") == 1
