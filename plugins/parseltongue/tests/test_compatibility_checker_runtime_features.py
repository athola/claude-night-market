"""Runtime features that break Python 3.9 but were reported compatible.

`_has_union_annotation` looked only at annotations, so a runtime
`isinstance(x, int | str)` (the usual hook break on 3.9) passed, as did
aliased `datetime.UTC`, `StrEnum`, `zip(strict=)`, `typing.Self` and PEP 695.
"""

from __future__ import annotations

import textwrap

import pytest

from parseltongue.analysis.compatibility_checker import CompatibilityChecker


def _min_version(code: str) -> str:
    report = CompatibilityChecker().check_compatibility(
        textwrap.dedent(code), ["3.9", "3.10", "3.11", "3.12"]
    )
    return report["minimum_version"]


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        ("isinstance(1, int | str)\n", "3.10"),
        ("from __future__ import annotations\nAlias = int | None\n", "3.10"),
        ("issubclass(bool, list[int] | dict)\n", "3.10"),
        ("import datetime as dt\nnow = dt.UTC\n", "3.11"),
        ("from enum import StrEnum\n", "3.11"),
        ("import enum\nclass C(enum.StrEnum):\n    A = 'a'\n", "3.11"),
        ("pairs = list(zip([1], [2], strict=True))\n", "3.10"),
        ("from typing import Self\n", "3.11"),
        ("def first[T](items: list[T]) -> T:\n    return items[0]\n", "3.12"),
        ("type Pair = tuple[int, int]\n", "3.12"),
    ],
)
def test_runtime_feature_raises_minimum_version(code: str, expected: str) -> None:
    assert _min_version(code) == expected


@pytest.mark.parametrize(
    "code",
    ["flags = 1 | 2\n", "MASK = 4\nvalue = 3 | MASK\n", "merged = {1} | {2}\n"],
)
def test_bitwise_or_on_values_stays_compatible(code: str) -> None:
    assert _min_version(code) == "3.0"
