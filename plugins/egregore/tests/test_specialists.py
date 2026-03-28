"""Tests for egregore agent specialization with persistent expertise."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from specialists import (
    DEFAULT_SPECIALISTS,
    SpecialistProfile,
    build_specialist_context,
    get_specialist_for_step,
    load_specialists,
    record_specialist_metrics,
    save_specialist_context,
    save_specialists,
)


class TestSpecialistProfile:
    """Tests for SpecialistProfile dataclass."""

    def test_create_profile_with_required_fields(self) -> None:
        """Given role, description, and steps, creates a valid profile."""
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews code",
            pipeline_steps=["code-review"],
        )
        assert profile.role == "reviewer"
        assert profile.description == "Reviews code"
        assert profile.pipeline_steps == ["code-review"]

    def test_defaults_for_optional_fields(self) -> None:
        """Given only required fields, optional fields have sensible defaults."""
        profile = SpecialistProfile(
            role="tester",
            description="Runs tests",
            pipeline_steps=["update-tests"],
        )
        assert profile.context_file == ""
        assert profile.items_processed == 0
        assert profile.last_active == ""
        assert profile.performance_metrics == {}

    def test_to_dict_contains_all_fields(self) -> None:
        """Given a profile, to_dict returns all fields as a plain dict."""
        profile = SpecialistProfile(
            role="documenter",
            description="Writes docs",
            pipeline_steps=["update-docs", "prepare-pr"],
            context_file="/tmp/ctx.md",
            items_processed=5,
            last_active="2025-01-01T00:00:00+00:00",
            performance_metrics={"steps": {}},
        )
        d = profile.to_dict()
        assert d["role"] == "documenter"
        assert d["description"] == "Writes docs"
        assert d["pipeline_steps"] == ["update-docs", "prepare-pr"]
        assert d["context_file"] == "/tmp/ctx.md"
        assert d["items_processed"] == 5
        assert d["last_active"] == "2025-01-01T00:00:00+00:00"
        assert d["performance_metrics"] == {"steps": {}}

    def test_to_dict_returns_copies(self) -> None:
        """Given a profile, to_dict returns independent copies of lists/dicts."""
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
            performance_metrics={"steps": {"code-review": {"attempts": 1}}},
        )
        d = profile.to_dict()
        d["pipeline_steps"].append("extra")
        d["performance_metrics"]["new_key"] = "value"
        assert "extra" not in profile.pipeline_steps
        assert "new_key" not in profile.performance_metrics

    def test_from_dict_roundtrip(self) -> None:
        """Given a serialized dict, from_dict reconstructs the profile."""
        original = SpecialistProfile(
            role="tester",
            description="Testing specialist",
            pipeline_steps=["update-tests"],
            context_file="/some/path.md",
            items_processed=10,
            last_active="2025-06-01T12:00:00+00:00",
            performance_metrics={"steps": {"update-tests": {"attempts": 10}}},
        )
        restored = SpecialistProfile.from_dict(original.to_dict())
        assert restored.role == original.role
        assert restored.description == original.description
        assert restored.pipeline_steps == original.pipeline_steps
        assert restored.context_file == original.context_file
        assert restored.items_processed == original.items_processed
        assert restored.last_active == original.last_active
        assert restored.performance_metrics == original.performance_metrics

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Given a dict with extra keys, from_dict ignores them."""
        data = {
            "role": "reviewer",
            "description": "Reviews code",
            "pipeline_steps": ["code-review"],
            "unknown_field": "should be ignored",
            "another_unknown": 42,
        }
        profile = SpecialistProfile.from_dict(data)
        assert profile.role == "reviewer"
        assert not hasattr(profile, "unknown_field")


class TestDefaultSpecialists:
    """Tests for the default specialist definitions."""

    def test_three_defaults_exist(self) -> None:
        assert len(DEFAULT_SPECIALISTS) == 3

    def test_default_roles(self) -> None:
        roles = {s.role for s in DEFAULT_SPECIALISTS}
        assert roles == {"reviewer", "documenter", "tester"}

    def test_reviewer_handles_review_steps(self) -> None:
        reviewer = next(s for s in DEFAULT_SPECIALISTS if s.role == "reviewer")
        assert "code-review" in reviewer.pipeline_steps
        assert "code-refinement" in reviewer.pipeline_steps
        assert "pr-review" in reviewer.pipeline_steps
        assert "fix-pr" in reviewer.pipeline_steps

    def test_documenter_handles_doc_steps(self) -> None:
        documenter = next(s for s in DEFAULT_SPECIALISTS if s.role == "documenter")
        assert "update-docs" in documenter.pipeline_steps
        assert "prepare-pr" in documenter.pipeline_steps

    def test_tester_handles_test_steps(self) -> None:
        tester = next(s for s in DEFAULT_SPECIALISTS if s.role == "tester")
        assert "update-tests" in tester.pipeline_steps


class TestGetSpecialistForStep:
    """Tests for step-to-specialist routing."""

    def test_returns_reviewer_for_code_review(self) -> None:
        result = get_specialist_for_step("code-review", DEFAULT_SPECIALISTS)
        assert result is not None
        assert result.role == "reviewer"

    def test_returns_tester_for_update_tests(self) -> None:
        result = get_specialist_for_step("update-tests", DEFAULT_SPECIALISTS)
        assert result is not None
        assert result.role == "tester"

    def test_returns_documenter_for_update_docs(self) -> None:
        result = get_specialist_for_step("update-docs", DEFAULT_SPECIALISTS)
        assert result is not None
        assert result.role == "documenter"

    def test_returns_none_for_unmapped_step(self) -> None:
        result = get_specialist_for_step("parse", DEFAULT_SPECIALISTS)
        assert result is None

    def test_returns_none_for_empty_list(self) -> None:
        result = get_specialist_for_step("code-review", [])
        assert result is None

    def test_returns_first_match_when_ambiguous(self) -> None:
        """Given two specialists claiming the same step, returns the first."""
        specs = [
            SpecialistProfile(
                role="alpha",
                description="First",
                pipeline_steps=["shared-step"],
            ),
            SpecialistProfile(
                role="beta",
                description="Second",
                pipeline_steps=["shared-step"],
            ),
        ]
        result = get_specialist_for_step("shared-step", specs)
        assert result is not None
        assert result.role == "alpha"


class TestBuildSpecialistContext:
    """Tests for loading persisted specialist context."""

    def test_returns_empty_when_no_context_file(self, tmp_path: Path) -> None:
        """Given no prior context, returns empty string."""
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
        )
        result = build_specialist_context(profile, tmp_path)
        assert result == ""

    def test_returns_file_content_when_exists(self, tmp_path: Path) -> None:
        """Given a saved context file, returns its contents."""
        context_dir = tmp_path / "specialists"
        context_dir.mkdir()
        context_file = context_dir / "reviewer.md"
        context_file.write_text("# Reviewer Notes\nPrefer small PRs.\n")

        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
        )
        result = build_specialist_context(profile, tmp_path)
        assert "Reviewer Notes" in result
        assert "Prefer small PRs." in result


class TestSaveSpecialistContext:
    """Tests for persisting specialist context."""

    def test_creates_context_file(self, tmp_path: Path) -> None:
        """Given context text, creates the file in specialists/ subdir."""
        profile = SpecialistProfile(
            role="tester",
            description="Tests",
            pipeline_steps=["update-tests"],
        )
        path = save_specialist_context(profile, "# Test Notes\n", tmp_path)
        assert path.exists()
        assert path.read_text() == "# Test Notes\n"

    def test_creates_specialists_directory(self, tmp_path: Path) -> None:
        """Given a fresh egregore dir, creates the specialists/ subdir."""
        profile = SpecialistProfile(
            role="documenter",
            description="Docs",
            pipeline_steps=["update-docs"],
        )
        save_specialist_context(profile, "content", tmp_path)
        assert (tmp_path / "specialists").is_dir()

    def test_updates_specialist_metadata(self, tmp_path: Path) -> None:
        """Given a save, updates context_file and last_active on the profile."""
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
        )
        assert profile.context_file == ""
        assert profile.last_active == ""

        path = save_specialist_context(profile, "notes", tmp_path)
        assert profile.context_file == str(path)
        assert profile.last_active != ""

    def test_overwrites_existing_context(self, tmp_path: Path) -> None:
        """Given existing context, overwrites with new content."""
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
        )
        save_specialist_context(profile, "old notes", tmp_path)
        save_specialist_context(profile, "new notes", tmp_path)

        context_path = tmp_path / "specialists" / "reviewer.md"
        assert context_path.read_text() == "new notes"


class TestRecordSpecialistMetrics:
    """Tests for performance metrics recording."""

    def test_increments_items_processed(self) -> None:
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
        )
        assert profile.items_processed == 0
        record_specialist_metrics(profile, "code-review", success=True)
        assert profile.items_processed == 1
        record_specialist_metrics(profile, "code-review", success=False)
        assert profile.items_processed == 2

    def test_sets_last_active(self) -> None:
        profile = SpecialistProfile(
            role="tester",
            description="Tests",
            pipeline_steps=["update-tests"],
        )
        assert profile.last_active == ""
        record_specialist_metrics(profile, "update-tests", success=True)
        assert profile.last_active != ""

    def test_tracks_per_step_attempts(self) -> None:
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review", "code-refinement"],
        )
        record_specialist_metrics(profile, "code-review", success=True)
        record_specialist_metrics(profile, "code-review", success=False)
        record_specialist_metrics(profile, "code-refinement", success=True)

        steps = profile.performance_metrics["steps"]
        assert steps["code-review"]["attempts"] == 2
        assert steps["code-review"]["successes"] == 1
        assert steps["code-refinement"]["attempts"] == 1
        assert steps["code-refinement"]["successes"] == 1

    def test_tracks_duration(self) -> None:
        profile = SpecialistProfile(
            role="tester",
            description="Tests",
            pipeline_steps=["update-tests"],
        )
        record_specialist_metrics(
            profile, "update-tests", success=True, duration_seconds=5.5
        )
        record_specialist_metrics(
            profile, "update-tests", success=True, duration_seconds=3.2
        )

        step_metrics = profile.performance_metrics["steps"]["update-tests"]
        assert step_metrics["total_duration"] == pytest.approx(8.7)

    def test_success_false_does_not_increment_successes(self) -> None:
        profile = SpecialistProfile(
            role="reviewer",
            description="Reviews",
            pipeline_steps=["code-review"],
        )
        record_specialist_metrics(profile, "code-review", success=False)
        steps = profile.performance_metrics["steps"]
        assert steps["code-review"]["attempts"] == 1
        assert steps["code-review"]["successes"] == 0


class TestSaveLoadSpecialists:
    """Tests for JSON persistence of specialist profiles."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "specialists.json"
        save_specialists(DEFAULT_SPECIALISTS, path)
        assert path.exists()

    def test_save_produces_valid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "specialists.json"
        save_specialists(DEFAULT_SPECIALISTS, path)
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        assert len(data) == 3

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "a" / "b" / "specialists.json"
        save_specialists(DEFAULT_SPECIALISTS, path)
        assert path.exists()

    def test_load_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "specialists.json"
        original = [
            SpecialistProfile(
                role="custom",
                description="Custom specialist",
                pipeline_steps=["step-a", "step-b"],
                items_processed=7,
                last_active="2025-03-01T00:00:00+00:00",
                performance_metrics={"steps": {"step-a": {"attempts": 7}}},
            ),
        ]
        save_specialists(original, path)
        loaded = load_specialists(path)
        assert len(loaded) == 1
        assert loaded[0].role == "custom"
        assert loaded[0].pipeline_steps == ["step-a", "step-b"]
        assert loaded[0].items_processed == 7
        assert loaded[0].performance_metrics == {"steps": {"step-a": {"attempts": 7}}}

    def test_load_missing_file_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "nonexistent.json"
        loaded = load_specialists(path)
        assert len(loaded) == len(DEFAULT_SPECIALISTS)
        roles = {s.role for s in loaded}
        assert roles == {"reviewer", "documenter", "tester"}

    def test_load_corrupt_json_returns_defaults(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not valid json {{{")
        loaded = load_specialists(path)
        assert len(loaded) == len(DEFAULT_SPECIALISTS)

    def test_load_defaults_are_independent_copies(self, tmp_path: Path) -> None:
        """Defaults returned from load should not share state with the constant."""
        path = tmp_path / "nonexistent.json"
        loaded = load_specialists(path)
        loaded[0].items_processed = 999
        assert DEFAULT_SPECIALISTS[0].items_processed == 0
