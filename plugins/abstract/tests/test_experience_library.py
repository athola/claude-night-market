"""Tests for experience library storage and retrieval."""

from pathlib import Path

from abstract.experience_library import ExperienceLibrary, format_context

PROJECT = "proj-a"


class TestExperienceLibraryStorage:
    """Test storing execution trajectories."""

    def test_should_store_successful_execution(self, tmp_path: Path) -> None:
        """Given a successful execution, when stored, then file created."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        lib.store(
            project=PROJECT,
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
            project=PROJECT,
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
    """Recent entries are what the PreToolUse hook injects."""

    def test_recent_entries_returns_newest_first_up_to_limit(
        self, tmp_path: Path
    ) -> None:
        lib = ExperienceLibrary(tmp_path / "experience-library")
        # Hash filenames sort in an order unrelated to insertion.
        for task in ("alpha", "bravo", "charlie", "delta"):
            lib.store(
                project=PROJECT,
                skill_ref="abstract:test-skill",
                task_description=task,
                approach_taken="",
                outcome="success",
                duration_ms=1,
            )

        recent = lib.recent_entries("abstract:test-skill", limit=3, project=PROJECT)

        assert [e["task_description"] for e in recent] == [
            "delta",
            "charlie",
            "bravo",
        ]

    def test_recent_entries_for_unknown_skill_creates_nothing(
        self, tmp_path: Path
    ) -> None:
        lib = ExperienceLibrary(tmp_path / "experience-library")

        assert lib.recent_entries("abstract:never-run", limit=3, project=PROJECT) == []
        assert not (tmp_path / "experience-library" / "abstract_never-run").exists()

    def test_recent_entries_skip_other_projects_and_non_objects(
        self, tmp_path: Path
    ) -> None:
        lib = ExperienceLibrary(tmp_path / "experience-library")
        for project in ("proj-a", "proj-b"):
            lib.store(
                project=project,
                skill_ref="abstract:test-skill",
                task_description="same task",
                approach_taken="",
                outcome="success",
                duration_ms=1,
            )
        (
            tmp_path / "experience-library" / "abstract_test-skill" / "null.json"
        ).write_text("null")

        recent = lib.recent_entries("abstract:test-skill", limit=5, project="proj-b")

        assert [e["project"] for e in recent] == ["proj-b"]
        assert len(lib.list_entries("abstract:test-skill")) == 2

    def test_untimed_execution_is_stored_without_a_duration(
        self, tmp_path: Path
    ) -> None:
        lib = ExperienceLibrary(tmp_path / "experience-library")
        lib.store(
            project=PROJECT,
            skill_ref="abstract:test-skill",
            task_description="untimed",
            approach_taken="",
            outcome="success",
            duration_ms=None,
        )

        assert lib.list_entries("abstract:test-skill")[0]["duration_ms"] is None

    def test_format_context_caps_each_entry(self) -> None:
        entries = [{"task_description": "y" * 9000}, {"task_description": "short"}]

        text = format_context(entries, max_chars_each=200)

        assert "short" in text
        assert "y" * 150 in text
        assert "y" * 200 not in text


class TestExperienceLibraryPruning:
    """Test pruning to max 20 entries per skill."""

    def test_should_prune_oldest_beyond_limit(self, tmp_path: Path) -> None:
        """Given 25 entries, when pruned, then only 20 remain."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        for i in range(25):
            lib.store(
                project=PROJECT,
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


class TestExperienceLibraryEdgeCases:
    """Test error handling and edge cases."""

    def test_should_skip_corrupt_json_in_list_entries(self, tmp_path: Path) -> None:
        """Given corrupt JSON file in library, when listing, then skip gracefully."""
        lib = ExperienceLibrary(tmp_path / "experience-library")
        lib.store(
            project=PROJECT,
            skill_ref="abstract:test-skill",
            task_description="Valid entry",
            approach_taken="Good approach",
            outcome="success",
            duration_ms=1000,
            tools_used=["Read"],
            key_decisions=[],
        )
        # Inject a corrupt JSON file into the skill directory
        skill_dir = tmp_path / "experience-library" / "abstract_test-skill"
        corrupt_file = skill_dir / "corrupt_entry.json"
        corrupt_file.write_text("{invalid json!!!")

        entries = lib.list_entries("abstract:test-skill")
        # Should have the valid entry but skip the corrupt one
        assert len(entries) == 1
        assert entries[0]["task_description"] == "Valid entry"
