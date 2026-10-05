"""Scores, bounds and counts in pensive's review skills (math review B2-10 to B2-15).

Each test pins a number a review printed wrong. The cases: a score that
could not reach 1.0, the last Makefile target never measured, every bare
Cargo requirement called an exact pin, async bodies after a multi-line
signature left unchecked, offsets 11-19 and 100-199 never flagged, a
summary that counted findings the body never listed, and "non-critical"
escalated to critical.
"""

from __future__ import annotations

from typing import Any

from pensive.reporting.formatters import MarkdownFormatter
from pensive.skills.makefile_review._analysis import AnalysisMixin
from pensive.skills.makefile_review._quality import QualityMixin
from pensive.skills.rust_review.cargo import CargoBuildMixin
from pensive.skills.rust_review.ownership import OwnershipMixin
from pensive.skills.rust_review_data import LARGE_OFFSET_RE
from pensive.utils.severity_mapper import categorize

_EVERY_MODERN_FEATURE = """.PHONY: all
CC := gcc
SHELL := /bin/bash
include common.mk
-include config.mk
.PRECIOUS: %.o
%.o: %.c
\t$(CC) -c $< | tee log
ifdef CROSS_COMPILE
endif
"""


class _Ctx:
    def __init__(self, content: str) -> None:
        self.content = content

    def get_file_content(self, _path: str) -> str:
        return self.content


class _Quality(QualityMixin):
    def _get_makefile_content(self, context: Any) -> str:
        return str(context)


def test_a_makefile_using_every_modern_feature_scores_one() -> None:
    """The divisor was 10.0 while the weights sum to 9.0 (B2-10)."""
    weights = sum(w for _, _, w in QualityMixin._MODERNIZATION_SCORE_PATTERNS)
    assert QualityMixin._modernization_score(_EVERY_MODERN_FEATURE) == weights
    result = _Quality().analyze_modernization(_EVERY_MODERN_FEATURE)
    assert result["modern_features"]["score"] == 1.0


def test_the_last_target_is_measured_too() -> None:
    """The size check ran only when the next header appeared (B2-11)."""
    lines = [
        "build:",
        "\ta",
        "\tb",
        "\tc",
        "\td",
        "deploy:",
        "\te",
        "\tf",
        "\tg",
        "\th",
        "",
    ]
    found = AnalysisMixin._find_large_targets(lines)
    assert any(f.startswith("deploy ") for f in found)
    assert any(f.startswith("build ") for f in found)


def test_only_an_equals_requirement_is_an_exact_pin() -> None:
    """Cargo reads "1.0" as ^1.0, so it is a range (B2-12)."""
    for version, pinned in (("1.0", False), ("=1.0.3", True), ("= 1.0", True)):
        deps: list[dict[str, str]] = []
        issues: list[dict[str, str]] = []
        CargoBuildMixin._check_dependency_line(f'serde = "{version}"', deps, issues, [])
        assert bool(issues) is pinned, version


def test_a_multi_line_async_signature_still_opens_the_body() -> None:
    """The body depth was taken from the signature line, which has no
    brace under rustfmt's multi-line layout (B2-13).
    """
    src = "async fn fetch(\n    a: u32,\n) -> u32 {\n    std::thread::sleep(d);\n    a\n}\n"
    result = OwnershipMixin().analyze_async_patterns(_Ctx(src), "x.rs")
    assert len(result["blocking_operations"]) == 1


def test_sync_code_after_an_async_fn_is_not_flagged() -> None:
    """The body ends at its closing brace, wherever the signature was."""
    src = (
        "async fn fetch(\n    a: u32,\n) -> u32 {\n    a\n}\n"
        "fn later() {\n    std::thread::sleep(d);\n}\n"
    )
    result = OwnershipMixin().analyze_async_patterns(_Ctx(src), "x.rs")
    assert result["blocking_operations"] == []


def test_every_offset_from_ten_up_is_large() -> None:
    """11-19 and 100-199 slipped through the old alternation (B2-14)."""
    for n in (10, 11, 15, 19, 20, 100, 150, 1000, 5000):
        assert LARGE_OFFSET_RE.search(f"*p.offset({n})"), n
    for n in (0, 1, 9):
        assert not LARGE_OFFSET_RE.search(f"*p.offset({n})"), n


def test_every_counted_finding_is_listed() -> None:
    """The summary lowercased severity and the grouping did not (B2-15)."""
    out = MarkdownFormatter().format(
        [{"id": "F1", "severity": "HIGH", "title": "t", "issue": "i"}]
    )
    assert "## High Priority" in out
    assert "F1" in out


def test_a_non_critical_issue_is_not_escalated() -> None:
    """A substring test read "non-critical" as critical and "insecurity"
    as security.
    """
    issues = categorize(
        [
            {"type": "style", "issue": "minor non-critical naming nit"},
            {"type": "style", "issue": "naming hints at insecurity"},
            {"type": "style", "issue": "a critical path is blocked"},
        ]
    )
    assert [i["severity"] for i in issues] == ["low", "low", "critical"]
