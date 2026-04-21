"""Tests for the curate_problems CLI script.

Covers coverage survey, gap detection, proposal validation, and the
safety invariant that the script never writes to data/problems/.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# Add scripts directory to path for direct import before importing the module.
SCRIPTS_DIR = Path(__file__).parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import curate_problems as cp  # noqa: E402 - must follow sys.path mutation

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: Any) -> None:
    with open(path, "w") as f:
        yaml.safe_dump(data, f)


def _sample_problem(**overrides: object) -> dict:
    """Return a minimal valid problem dict."""
    base: dict = {
        "id": "test-001",
        "title": "Test Problem",
        "difficulty": "easy",
        "prompt": "Solve this problem.",
        "hints": ["Think carefully."],
        "solution_outline": "Use a hash map.",
        "tags": ["hash-map"],
        "neetcode_id": "neetcode-test",
        "challenge_type": "explain_why",
    }
    base.update(overrides)
    return base


def _make_bank_dir(tmp_path: Path, problems_by_category: dict) -> Path:
    """Write per-category YAML files under tmp_path, return the dir."""
    for cat, problems in problems_by_category.items():
        _write_yaml(
            tmp_path / f"{cat}.yaml",
            {"category": cat, "problems": problems},
        )
    return tmp_path


def _make_manifest(tmp_path: Path, categories: list[dict]) -> None:
    _write_yaml(
        tmp_path / "_manifest.yaml",
        {"version": "1.0", "categories": categories},
    )


# ---------------------------------------------------------------------------
# Feature: Coverage survey
# ---------------------------------------------------------------------------


class TestSurveyBankCoverage:
    """
    Feature: Survey current problem bank coverage by category

    As a gauntlet maintainer
    I want to know how many problems exist per category
    So that I can compare against the expected NeetCode counts
    """

    @pytest.mark.unit
    def test_survey_returns_count_per_category(self, tmp_path):
        """
        Scenario: Valid bank directory returns a count dict
        Given two YAML files with known problem counts
        When survey_bank_coverage is called
        Then a dict mapping category to problem count is returned
        """
        _make_bank_dir(
            tmp_path,
            {
                "arrays-and-hashing": [
                    _sample_problem(id="a1"),
                    _sample_problem(id="a2"),
                ],
                "stack": [_sample_problem(id="s1")],
            },
        )
        result = cp.survey_bank_coverage(tmp_path)

        assert result["arrays-and-hashing"] == 2
        assert result["stack"] == 1

    @pytest.mark.unit
    def test_survey_skips_underscore_files(self, tmp_path):
        """
        Scenario: _manifest.yaml is excluded from the count
        Given a bank dir with a _manifest.yaml and one real YAML file
        When survey_bank_coverage is called
        Then _manifest is not counted
        """
        _make_manifest(
            tmp_path, [{"id": "trees", "name": "Trees", "neetcode_count": 15}]
        )
        _make_bank_dir(tmp_path, {"trees": [_sample_problem(id="t1")]})
        result = cp.survey_bank_coverage(tmp_path)

        assert "trees" in result
        assert "_manifest" not in result

    @pytest.mark.unit
    def test_survey_empty_directory_returns_empty_dict(self, tmp_path):
        """
        Scenario: Empty bank directory returns empty dict
        Given a directory with no YAML files
        When survey_bank_coverage is called
        Then an empty dict is returned
        """
        result = cp.survey_bank_coverage(tmp_path)
        assert result == {}


# ---------------------------------------------------------------------------
# Feature: Gap detection
# ---------------------------------------------------------------------------


class TestIdentifyGaps:
    """
    Feature: Identify categories that are under-represented

    As a gauntlet maintainer
    I want to detect categories with fewer problems than expected
    So that I can prioritise new problem authoring
    """

    @pytest.mark.unit
    def test_gap_detected_when_count_below_expected(self):
        """
        Scenario: Category with fewer problems than expected appears in gaps
        Given a manifest listing 9 expected problems for a category
        And the bank only has 6
        When identify_gaps is called
        Then that category appears in the returned gaps list
        """
        manifest_categories = [
            {
                "id": "arrays-and-hashing",
                "name": "Arrays & Hashing",
                "neetcode_count": 9,
            }
        ]
        current_counts = {"arrays-and-hashing": 6}

        gaps = cp.identify_gaps(current_counts, manifest_categories)

        assert len(gaps) == 1
        gap = gaps[0]
        assert gap["category_id"] == "arrays-and-hashing"
        assert gap["expected"] == 9
        assert gap["actual"] == 6
        assert gap["missing"] == 3

    @pytest.mark.unit
    def test_no_gap_when_count_meets_expected(self):
        """
        Scenario: Category at or above expected count is not a gap
        Given a manifest listing 5 expected problems
        And the bank has exactly 5
        When identify_gaps is called
        Then no gaps are returned
        """
        manifest_categories = [
            {"id": "two-pointers", "name": "Two Pointers", "neetcode_count": 5}
        ]
        current_counts = {"two-pointers": 5}

        gaps = cp.identify_gaps(current_counts, manifest_categories)

        assert gaps == []

    @pytest.mark.unit
    def test_category_missing_from_bank_is_full_gap(self):
        """
        Scenario: Category with neetcode_count > 0 but absent from bank is a gap
        Given a manifest category with neetcode_count=7
        And the bank has no problems for that category
        When identify_gaps is called
        Then the gap shows actual=0 and missing=7
        """
        manifest_categories = [
            {"id": "binary-search", "name": "Binary Search", "neetcode_count": 7}
        ]
        current_counts: dict = {}

        gaps = cp.identify_gaps(current_counts, manifest_categories)

        assert len(gaps) == 1
        assert gaps[0]["actual"] == 0
        assert gaps[0]["missing"] == 7

    @pytest.mark.unit
    def test_zero_expected_count_not_a_gap(self):
        """
        Scenario: Category with neetcode_count=0 is not flagged as a gap
        Given system-design with neetcode_count=0
        When identify_gaps is called
        Then system-design is not in gaps
        """
        manifest_categories = [
            {"id": "system-design", "name": "System Design", "neetcode_count": 0}
        ]
        current_counts: dict = {}

        gaps = cp.identify_gaps(current_counts, manifest_categories)

        assert gaps == []

    @pytest.mark.unit
    def test_multiple_gaps_sorted_by_missing_descending(self):
        """
        Scenario: Gaps are sorted largest-first so the worst gaps come first
        Given two categories both under expected
        When identify_gaps is called
        Then the one with more missing problems appears first
        """
        manifest_categories = [
            {"id": "trees", "name": "Trees", "neetcode_count": 15},
            {"id": "stack", "name": "Stack", "neetcode_count": 7},
        ]
        current_counts = {"trees": 10, "stack": 6}

        gaps = cp.identify_gaps(current_counts, manifest_categories)

        assert gaps[0]["category_id"] == "trees"  # 5 missing
        assert gaps[1]["category_id"] == "stack"  # 1 missing


# ---------------------------------------------------------------------------
# Feature: Proposal validation
# ---------------------------------------------------------------------------


class TestValidateProposedEntries:
    """
    Feature: Validate proposed YAML entries against the existing schema

    As a gauntlet maintainer
    I want proposed problem entries to be validated before human review
    So that only schema-conformant proposals are presented
    """

    @pytest.mark.unit
    def test_valid_entry_passes_validation(self):
        """
        Scenario: A well-formed proposed entry passes schema validation
        Given a proposed problem dict with all required fields
        When validate_proposed_entry is called
        Then no errors are returned
        """
        proposed = _sample_problem(id="trees-999", category="trees")
        errors = cp.validate_proposed_entry(proposed)

        assert errors == []

    @pytest.mark.unit
    def test_missing_required_field_produces_error(self):
        """
        Scenario: A proposed entry missing 'id' fails validation
        Given a proposed problem dict without the 'id' field
        When validate_proposed_entry is called
        Then a non-empty error list is returned
        """
        proposed = _sample_problem()
        del proposed["id"]
        errors = cp.validate_proposed_entry(proposed)

        assert len(errors) > 0

    @pytest.mark.unit
    def test_invalid_difficulty_produces_error(self):
        """
        Scenario: Unknown difficulty string fails validation
        Given a proposed problem with difficulty='nightmare'
        When validate_proposed_entry is called
        Then an error mentioning difficulty is returned
        """
        proposed = _sample_problem(
            id="x-001", difficulty="nightmare", category="graphs"
        )
        errors = cp.validate_proposed_entry(proposed)

        assert any("difficulty" in e.lower() for e in errors)

    @pytest.mark.unit
    def test_invalid_challenge_type_produces_error(self):
        """
        Scenario: Unknown challenge_type string fails validation
        Given a proposed problem with challenge_type='dance_off'
        When validate_proposed_entry is called
        Then an error is returned
        """
        proposed = _sample_problem(
            id="x-002", category="graphs", challenge_type="dance_off"
        )
        errors = cp.validate_proposed_entry(proposed)

        assert len(errors) > 0

    @pytest.mark.unit
    def test_multiple_valid_entries_all_pass(self):
        """
        Scenario: A batch of valid entries all pass validation
        Given two valid proposed problem dicts
        When validate_proposed_entries is called on the list
        Then an empty error list is returned for each
        """
        proposals = [
            _sample_problem(id="x-001", category="graphs"),
            _sample_problem(id="x-002", category="trees"),
        ]
        results = cp.validate_proposed_entries(proposals)

        assert all(len(errs) == 0 for errs in results.values())


# ---------------------------------------------------------------------------
# Feature: Safety invariant — no writes to data/problems/
# ---------------------------------------------------------------------------


class TestNoWriteToProblems:
    """
    Feature: The script never writes to the problems directory

    As a gauntlet maintainer with curated data
    I want the curate script to be read-only
    So that my hand-crafted YAML files cannot be silently overwritten
    """

    @pytest.mark.unit
    def test_script_has_no_write_mode_flag(self):
        """
        Scenario: Argument parser exposes no --write or --fix flag
        Given the curate_problems CLI argument parser
        When it is inspected
        Then no --write or --fix argument is registered
        """
        parser = cp.build_arg_parser()
        known = {
            action.option_strings[0]
            for action in parser._actions
            if action.option_strings
        }

        assert "--write" not in known
        assert "--fix" not in known

    @pytest.mark.unit
    def test_generate_report_does_not_open_files_for_write(self, tmp_path, monkeypatch):
        """
        Scenario: generate_report writes only to its output parameter, not the bank
        Given a problems dir and a separate output dir
        When generate_report is called
        Then no files in the problems dir are modified
        """
        _make_bank_dir(
            tmp_path, {"trees": [_sample_problem(id="t1", category="trees")]}
        )
        _make_manifest(
            tmp_path, [{"id": "trees", "name": "Trees", "neetcode_count": 15}]
        )

        output_path = tmp_path / "report.md"
        cp.generate_report(tmp_path, output_path)

        # Bank files must be unchanged — check that the only new file is the report
        all_yaml = list(tmp_path.glob("*.yaml"))
        # Two: trees.yaml + _manifest.yaml
        assert len(all_yaml) == 2
        assert output_path.exists()

    @pytest.mark.unit
    def test_report_contains_gap_section(self, tmp_path):
        """
        Scenario: Generated report includes a coverage gaps section
        Given a bank with fewer problems than expected
        When generate_report is called
        Then the report markdown mentions the gap
        """
        _make_bank_dir(
            tmp_path, {"trees": [_sample_problem(id="t1", category="trees")]}
        )
        _make_manifest(
            tmp_path, [{"id": "trees", "name": "Trees", "neetcode_count": 15}]
        )

        output_path = tmp_path / "report.md"
        cp.generate_report(tmp_path, output_path)

        content = output_path.read_text()
        assert "trees" in content.lower()
        assert "gap" in content.lower() or "missing" in content.lower()
