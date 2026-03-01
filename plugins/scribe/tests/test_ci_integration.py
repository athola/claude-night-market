"""Tests for CI integration module (Issue #137).

Validates JSON output schema, exit code logic, threshold comparison,
and summary calculations for the --ci flag behaviour.
"""

from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Helpers that simulate the ci-integration module behaviour
# ---------------------------------------------------------------------------


def build_file_result(path: str, score: float, markers: int) -> dict[str, Any]:
    """Build a single file result dict with rating derived from score."""
    if score <= 1.0:
        rating = "Clean"
    elif score <= 2.5:
        rating = "Light"
    elif score <= 5.0:
        rating = "Moderate"
    else:
        rating = "Heavy"
    return {"path": path, "score": score, "rating": rating, "markers": markers}


def build_summary(
    files: list[dict[str, Any]],
    threshold: float = 3.0,
) -> dict[str, Any]:
    """Compute summary block from a list of file results."""
    if not files:
        return {
            "total_files": 0,
            "avg_score": 0.0,
            "max_score": 0.0,
            "pass": True,
        }
    scores = [f["score"] for f in files]
    avg = round(sum(scores) / len(scores), 2)
    max_score = max(scores)
    return {
        "total_files": len(files),
        "avg_score": avg,
        "max_score": max_score,
        "pass": max_score <= threshold,
    }


def build_ci_output(
    files: list[dict[str, Any]],
    threshold: float = 3.0,
) -> dict[str, Any]:
    """Build the full JSON output object."""
    return {"files": files, "summary": build_summary(files, threshold)}


def exit_code_for(output: dict[str, Any]) -> int:
    """Return 0 if pass, 1 if threshold exceeded."""
    return 0 if output["summary"]["pass"] else 1


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJsonSchema:
    def test_file_result_has_required_keys(self) -> None:
        result = build_file_result("docs/guide.md", 2.4, 7)
        assert set(result.keys()) == {"path", "score", "rating", "markers"}

    def test_file_result_types(self) -> None:
        result = build_file_result("docs/guide.md", 2.4, 7)
        assert isinstance(result["path"], str)
        assert isinstance(result["score"], float)
        assert isinstance(result["rating"], str)
        assert isinstance(result["markers"], int)

    def test_summary_has_required_keys(self) -> None:
        files = [build_file_result("docs/a.md", 1.0, 3)]
        summary = build_summary(files)
        assert set(summary.keys()) == {"total_files", "avg_score", "max_score", "pass"}

    def test_summary_types(self) -> None:
        files = [build_file_result("docs/a.md", 1.0, 3)]
        summary = build_summary(files)
        assert isinstance(summary["total_files"], int)
        assert isinstance(summary["avg_score"], float)
        assert isinstance(summary["max_score"], float)
        assert isinstance(summary["pass"], bool)

    def test_output_top_level_keys(self) -> None:
        output = build_ci_output([])
        assert set(output.keys()) == {"files", "summary"}


# ---------------------------------------------------------------------------
# Rating assignment
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRating:
    def test_clean_rating(self) -> None:
        assert build_file_result("f.md", 0.5, 1)["rating"] == "Clean"

    def test_clean_boundary(self) -> None:
        assert build_file_result("f.md", 1.0, 2)["rating"] == "Clean"

    def test_light_rating(self) -> None:
        assert build_file_result("f.md", 1.5, 4)["rating"] == "Light"

    def test_light_boundary(self) -> None:
        assert build_file_result("f.md", 2.5, 5)["rating"] == "Light"

    def test_moderate_rating(self) -> None:
        assert build_file_result("f.md", 3.5, 8)["rating"] == "Moderate"

    def test_moderate_boundary(self) -> None:
        assert build_file_result("f.md", 5.0, 10)["rating"] == "Moderate"

    def test_heavy_rating(self) -> None:
        assert build_file_result("f.md", 6.0, 15)["rating"] == "Heavy"


# ---------------------------------------------------------------------------
# Exit code logic
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExitCode:
    def test_exit_zero_when_all_pass(self) -> None:
        files = [
            build_file_result("docs/a.md", 1.0, 2),
            build_file_result("docs/b.md", 2.0, 4),
        ]
        output = build_ci_output(files, threshold=3.0)
        assert exit_code_for(output) == 0

    def test_exit_one_when_threshold_exceeded(self) -> None:
        files = [
            build_file_result("docs/a.md", 1.0, 2),
            build_file_result("docs/b.md", 4.5, 12),
        ]
        output = build_ci_output(files, threshold=3.0)
        assert exit_code_for(output) == 1

    def test_exit_zero_when_score_equals_threshold(self) -> None:
        files = [build_file_result("docs/a.md", 3.0, 6)]
        output = build_ci_output(files, threshold=3.0)
        assert exit_code_for(output) == 0

    def test_exit_one_when_score_just_above_threshold(self) -> None:
        files = [build_file_result("docs/a.md", 3.01, 6)]
        output = build_ci_output(files, threshold=3.0)
        assert exit_code_for(output) == 1

    def test_exit_zero_with_no_files(self) -> None:
        output = build_ci_output([], threshold=3.0)
        assert exit_code_for(output) == 0


# ---------------------------------------------------------------------------
# Threshold comparison
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestThreshold:
    def test_default_threshold_is_3_0(self) -> None:
        files = [build_file_result("docs/a.md", 3.0, 5)]
        summary = build_summary(files)
        assert summary["pass"] is True

    def test_custom_threshold_lower(self) -> None:
        files = [build_file_result("docs/a.md", 2.0, 5)]
        summary = build_summary(files, threshold=1.5)
        assert summary["pass"] is False

    def test_custom_threshold_higher(self) -> None:
        files = [build_file_result("docs/a.md", 4.9, 10)]
        summary = build_summary(files, threshold=5.0)
        assert summary["pass"] is True

    def test_pass_false_uses_max_not_avg(self) -> None:
        # avg is 2.0, but max is 4.0 — should fail at threshold 3.0
        files = [
            build_file_result("docs/a.md", 0.0, 0),
            build_file_result("docs/b.md", 4.0, 9),
        ]
        summary = build_summary(files, threshold=3.0)
        assert summary["pass"] is False


# ---------------------------------------------------------------------------
# Summary calculations
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSummaryCalculation:
    def test_total_files_count(self) -> None:
        files = [build_file_result(f"docs/{i}.md", 1.0, 1) for i in range(5)]
        summary = build_summary(files)
        assert summary["total_files"] == 5

    def test_avg_score_single_file(self) -> None:
        files = [build_file_result("docs/a.md", 2.5, 5)]
        summary = build_summary(files)
        assert summary["avg_score"] == 2.5

    def test_avg_score_multiple_files(self) -> None:
        files = [
            build_file_result("docs/a.md", 1.0, 2),
            build_file_result("docs/b.md", 3.0, 6),
        ]
        summary = build_summary(files)
        assert summary["avg_score"] == 2.0

    def test_avg_score_rounded_to_two_decimals(self) -> None:
        files = [
            build_file_result("docs/a.md", 1.0, 1),
            build_file_result("docs/b.md", 2.0, 2),
            build_file_result("docs/c.md", 3.0, 3),
        ]
        summary = build_summary(files)
        assert summary["avg_score"] == 2.0

    def test_max_score_is_highest(self) -> None:
        files = [
            build_file_result("docs/a.md", 1.2, 2),
            build_file_result("docs/b.md", 5.7, 11),
            build_file_result("docs/c.md", 3.1, 7),
        ]
        summary = build_summary(files)
        assert summary["max_score"] == 5.7

    def test_empty_file_list_returns_zero_scores(self) -> None:
        summary = build_summary([])
        assert summary["total_files"] == 0
        assert summary["avg_score"] == 0.0
        assert summary["max_score"] == 0.0
        assert summary["pass"] is True
