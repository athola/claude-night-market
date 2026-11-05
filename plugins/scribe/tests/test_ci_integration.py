"""Contract tests for the slop-detector ci-integration module (Issue #137).

The `--ci` behavior is an instruction to the model, not code, so the
shipped artifact is `skills/slop-detector/modules/ci-integration.md`.
These tests pin the JSON schema, exit codes, and threshold rule that
document states, and fail when it is edited out of agreement.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

MODULES = Path(__file__).resolve().parents[1] / "skills" / "slop-detector" / "modules"
CI_MODULE = MODULES / "ci-integration.md"
REPORTING_MODULE = MODULES / "reporting.md"


@pytest.fixture(scope="module")
def ci_text() -> str:
    return CI_MODULE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def schema_example(ci_text: str) -> dict[str, Any]:
    block = re.search(r"```json\n(.*?)\n```", ci_text, re.DOTALL)
    assert block, "ci-integration.md has no ```json schema example"
    return json.loads(block.group(1))


@pytest.mark.unit
class TestJsonSchema:
    def test_example_top_level_keys_are_files_and_summary(
        self, schema_example: dict[str, Any]
    ) -> None:
        assert set(schema_example) == {"files", "summary"}

    def test_example_file_entry_has_the_documented_keys(
        self, schema_example: dict[str, Any]
    ) -> None:
        assert set(schema_example["files"][0]) == {"path", "score", "rating", "markers"}

    def test_example_summary_has_the_documented_keys(
        self, schema_example: dict[str, Any]
    ) -> None:
        assert set(schema_example["summary"]) == {
            "total_files",
            "avg_score",
            "max_score",
            "pass",
        }

    def test_example_value_types_match_the_field_table(
        self, schema_example: dict[str, Any]
    ) -> None:
        entry = schema_example["files"][0]
        summary = schema_example["summary"]
        assert isinstance(entry["path"], str)
        assert isinstance(entry["score"], float)
        assert isinstance(entry["rating"], str)
        assert isinstance(entry["markers"], int)
        assert isinstance(summary["total_files"], int)
        assert isinstance(summary["pass"], bool)

    def test_every_schema_field_has_a_row_in_the_field_table(
        self, ci_text: str, schema_example: dict[str, Any]
    ) -> None:
        documented = {
            *(f"files[].{key}" for key in schema_example["files"][0]),
            *(f"summary.{key}" for key in schema_example["summary"]),
        }
        missing = [name for name in sorted(documented) if f"`{name}`" not in ci_text]
        assert missing == []

    def test_example_summary_agrees_with_its_own_file_entry(
        self, schema_example: dict[str, Any]
    ) -> None:
        score = schema_example["files"][0]["score"]
        summary = schema_example["summary"]
        assert summary["total_files"] == len(schema_example["files"])
        assert summary["max_score"] == score
        assert summary["pass"] is (score <= 3.0)


@pytest.mark.unit
class TestRatings:
    def test_documented_ratings_match_the_reporting_label_table(
        self, ci_text: str
    ) -> None:
        listed = re.search(r"One of: ([A-Za-z, ]+)\s*\|", ci_text)
        assert listed, "ci-integration.md no longer lists the rating names"
        ratings = [name.strip() for name in listed.group(1).split(",")]
        reporting = REPORTING_MODULE.read_text(encoding="utf-8")
        labels = re.findall(r"^\| [\d.+ -]+ \| (\w+) \|$", reporting, re.MULTILINE)
        assert ratings == labels


@pytest.mark.unit
class TestExitCodesAndThreshold:
    def test_exit_code_table_maps_zero_one_and_two(self, ci_text: str) -> None:
        rows = dict(re.findall(r"^\| (\d) \| ([^|]+) \|$", ci_text, re.MULTILINE))
        assert set(rows) == {"0", "1", "2"}
        assert "max_score <= threshold" in rows["0"]
        assert "exceed" in rows["1"]
        assert "error" in rows["2"].lower()

    def test_default_threshold_is_three(self, ci_text: str) -> None:
        assert re.search(r"`--threshold <float>` \| `3\.0` \|", ci_text)

    def test_pass_rule_compares_the_maximum_not_the_average(self, ci_text: str) -> None:
        assert "True when max_score <= threshold" in ci_text

    def test_json_must_be_the_only_stdout_content(self, ci_text: str) -> None:
        assert "The JSON must be the only content on stdout" in ci_text
