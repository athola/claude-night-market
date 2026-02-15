"""Tests for experience library storage and retrieval."""

from pathlib import Path

from abstract.experience_library import ExperienceLibrary


class TestExperienceLibraryStorage:
    """Test storing execution trajectories."""

    def test_should_store_successful_execution(self, tmp_path: Path) -> None:
        """Given a successful execution, when stored, then file created."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        lib.store(
            skill_ref="abstract:test-skill",
            task_description="Generate API docs from OpenAPI spec",
            approach_taken="Used jinja2 templates",
            outcome="success",
            duration_ms=4200,
            tools_used=["Read", "Write"],
            key_decisions=["Template-based over freeform"],
        )
        entries = lib.list_entries("abstract:test-skill")
        assert len(entries) == 1
        assert entries[0]["outcome"] == "success"

    def test_should_reject_failed_execution(self, tmp_path: Path) -> None:
        """Given a failed execution, when stored, then rejected."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        lib.store(
            skill_ref="abstract:test-skill",
            task_description="Failed attempt",
            approach_taken="Wrong approach",
            outcome="failure",
            duration_ms=10000,
            tools_used=["Read"],
            key_decisions=[],
        )
        entries = lib.list_entries("abstract:test-skill")
        assert len(entries) == 0


class TestExperienceLibraryRetrieval:
    """Test retrieving similar past experiences."""

    def test_should_find_similar_by_keyword_overlap(self, tmp_path: Path) -> None:
        """Given stored experiences, when queried with similar words, then matched."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        lib.store(
            skill_ref="abstract:test-skill",
            task_description="Generate API documentation from OpenAPI spec",
            approach_taken="Used jinja2 templates",
            outcome="success",
            duration_ms=4200,
            tools_used=["Read", "Write"],
            key_decisions=["Template-based"],
        )
        lib.store(
            skill_ref="abstract:test-skill",
            task_description="Write unit tests for auth module",
            approach_taken="pytest with fixtures",
            outcome="success",
            duration_ms=3000,
            tools_used=["Read", "Write", "Bash"],
            key_decisions=["Fixture-based"],
        )
        results = lib.find_similar("abstract:test-skill", "Generate docs from OpenAPI")
        assert len(results) >= 1
        assert (
            "API" in results[0]["task_description"]
            or "OpenAPI" in results[0]["task_description"]
        )

    def test_should_limit_to_max_exemplars(self, tmp_path: Path) -> None:
        """Given many experiences, when queried, then max 3 returned."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        for i in range(10):
            lib.store(
                skill_ref="abstract:test-skill",
                task_description=f"Task {i} about testing",
                approach_taken=f"Approach {i}",
                outcome="success",
                duration_ms=1000,
                tools_used=["Read"],
                key_decisions=[],
            )
        results = lib.find_similar("abstract:test-skill", "testing task")
        assert len(results) <= 3


class TestExperienceLibraryPruning:
    """Test pruning to max 20 entries per skill."""

    def test_should_prune_oldest_beyond_limit(self, tmp_path: Path) -> None:
        """Given 25 entries, when pruned, then only 20 remain."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        for i in range(25):
            lib.store(
                skill_ref="abstract:test-skill",
                task_description=f"Task {i} unique description",
                approach_taken=f"Approach {i}",
                outcome="success",
                duration_ms=1000,
                tools_used=["Read"],
                key_decisions=[],
            )
        entries = lib.list_entries("abstract:test-skill")
        assert len(entries) <= 20
