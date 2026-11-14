"""Version features come from the syntax tree when the code parses.

The regexes for `match` and `@dataclass(slots=True)` ran on raw text, so a
docstring line such as "match the header line:" followed by "case
sensitive." made the checker require Python 3.10.
"""

from __future__ import annotations

import textwrap

import pytest

from parseltongue.analysis.compatibility_checker import CompatibilityChecker

_TARGETS = ["3.8", "3.9", "3.10"]


def _check(code: str) -> dict:
    return CompatibilityChecker().check_compatibility(textwrap.dedent(code), _TARGETS)


@pytest.mark.parametrize(
    "code",
    [
        '''
        def parse(line):
            """Read one line.

            match the header line:
            case sensitive.
            """
            return line
        ''',
        """
        # @dataclass(slots=True) would need 3.10
        x = 1
        """,
    ],
    ids=["match-in-docstring", "slots-in-comment"],
)
def test_prose_does_not_raise_the_minimum_version(code: str) -> None:
    assert _check(code)["minimum_version"] != "3.10"


@pytest.mark.parametrize(
    ("code", "feature"),
    [
        (
            """
            def f(cmd):
                match cmd:
                    case "go":
                        return 1
            """,
            "match_statement",
        ),
        (
            """
            from dataclasses import dataclass

            @dataclass(slots=True)
            class P:
                x: int
            """,
            "dataclass_slots",
        ),
    ],
)
def test_real_syntax_still_requires_3_10(code: str, feature: str) -> None:
    result = _check(code)
    assert result["minimum_version"] == "3.10"
    assert feature in {f["feature"] for f in result["features"]}


def test_future_annotations_is_still_reported() -> None:
    result = _check("from __future__ import annotations\n")
    assert "from __future__ import annotations" in {
        f["feature"] for f in result["features"]
    }
