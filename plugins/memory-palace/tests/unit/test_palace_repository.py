"""Tests for PalaceRepository — palace CRUD, master index, and backups.

Feature: Palace Repository
  As a palace manager
  I want a dedicated class for palace persistence
  So that storage concerns are isolated from business logic
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from memory_palace.palace_repository import PalaceRepository


@pytest.fixture
def repo(tmp_path: Path) -> PalaceRepository:
    """Return a repository backed by a temporary directory."""
    palaces_dir = tmp_path / "palaces"
    palaces_dir.mkdir()
    (palaces_dir / "backups").mkdir()
    return PalaceRepository(str(palaces_dir))


@pytest.fixture
def sample_palace() -> dict[str, Any]:
    """Return a minimal valid palace dict."""
    return {
        "id": "aabb1122",
        "name": "Test Palace",
        "domain": "testing",
        "metaphor": "building",
        "created": "2025-01-01T00:00:00+00:00",
        "last_modified": "2025-01-01T00:00:00+00:00",
        "layout": {"districts": [], "buildings": [], "rooms": [], "connections": []},
        "associations": {},
        "sensory_encoding": {},
        "metadata": {
            "concept_count": 0,
            "complexity_level": "basic",
            "access_patterns": [],
        },
    }


class TestPalaceRepositoryCreate:
    """Feature: Palace creation.

    As a user
    I want to create a new palace
    So that I can store domain knowledge spatially
    """

    @pytest.mark.unit
    def test_create_palace_returns_dict_with_required_fields(
        self, repo: PalaceRepository
    ) -> None:
        """Scenario: Create a palace with required fields
        Given an empty repository
        When I call create_palace with name, domain, and metaphor
        Then the returned dict has id, name, domain, metaphor, layout, and metadata.
        """
        palace = repo.create_palace("Python Palace", "programming", "library")

        assert "id" in palace
        assert palace["name"] == "Python Palace"
        assert palace["domain"] == "programming"
        assert palace["metaphor"] == "library"
        assert "layout" in palace
        assert "metadata" in palace

    @pytest.mark.unit
    def test_create_palace_writes_json_file(self, repo: PalaceRepository) -> None:
        """Scenario: New palace is persisted to disk
        Given an empty repository
        When I create a palace
        Then a JSON file exists in the palaces directory.
        """
        palace = repo.create_palace("Rust Fortress", "programming")

        palace_file = Path(repo.palaces_dir) / f"{palace['id']}.json"
        assert palace_file.exists()

    @pytest.mark.unit
    def test_create_palace_updates_master_index(self, repo: PalaceRepository) -> None:
        """Scenario: Master index is updated after creation
        Given an empty repository
        When I create a palace
        Then get_master_index reports one palace.
        """
        repo.create_palace("Math Manor", "mathematics")

        index = repo.get_master_index()
        assert index["global_stats"]["total_palaces"] == 1


class TestPalaceRepositoryLoadSave:
    """Feature: Loading and saving palaces.

    As a user
    I want to load and save palace data
    So that changes persist across sessions
    """

    @pytest.mark.unit
    def test_load_palace_returns_existing_palace(
        self, repo: PalaceRepository, sample_palace: dict[str, Any]
    ) -> None:
        """Scenario: Load a palace that exists on disk
        Given a palace file written to the palaces directory
        When I load it by ID
        Then I get the palace data back.
        """
        palace_file = Path(repo.palaces_dir) / f"{sample_palace['id']}.json"
        palace_file.write_text(json.dumps(sample_palace))

        loaded = repo.load_palace(sample_palace["id"])

        assert loaded is not None
        assert loaded["id"] == sample_palace["id"]
        assert loaded["name"] == sample_palace["name"]

    @pytest.mark.unit
    def test_load_palace_returns_none_for_missing_id(
        self, repo: PalaceRepository
    ) -> None:
        """Scenario: Load a palace that does not exist
        Given an empty repository
        When I load a non-existent palace ID
        Then I get None.
        """
        result = repo.load_palace("nonexistent")
        assert result is None

    @pytest.mark.unit
    def test_save_palace_updates_last_modified(
        self, repo: PalaceRepository, sample_palace: dict[str, Any]
    ) -> None:
        """Scenario: Saving a palace updates its timestamp
        Given a palace with an old last_modified value
        When I save it
        Then last_modified is refreshed to now.
        """
        original_ts = sample_palace["last_modified"]
        palace_file = Path(repo.palaces_dir) / f"{sample_palace['id']}.json"
        palace_file.write_text(json.dumps(sample_palace))

        repo.save_palace(sample_palace)

        reloaded = repo.load_palace(sample_palace["id"])
        assert reloaded is not None
        assert reloaded["last_modified"] != original_ts

    @pytest.mark.unit
    def test_save_palace_creates_backup(
        self, repo: PalaceRepository, sample_palace: dict[str, Any]
    ) -> None:
        """Scenario: Saving a palace backs up the existing file
        Given a palace already persisted to disk
        When I save it again
        Then a backup file appears in the backups directory.
        """
        palace_file = Path(repo.palaces_dir) / f"{sample_palace['id']}.json"
        palace_file.write_text(json.dumps(sample_palace))

        repo.save_palace(sample_palace)

        backups = list((Path(repo.palaces_dir) / "backups").glob("*.json"))
        assert len(backups) >= 1


class TestPalaceRepositoryDelete:
    """Feature: Palace deletion.

    As a user
    I want to delete palaces
    So that I can clean up stale data
    """

    @pytest.mark.unit
    def test_delete_palace_removes_file(
        self, repo: PalaceRepository, sample_palace: dict[str, Any]
    ) -> None:
        """Scenario: Delete an existing palace
        Given a palace file on disk
        When I delete it by ID
        Then the file no longer exists and True is returned.
        """
        palace_file = Path(repo.palaces_dir) / f"{sample_palace['id']}.json"
        palace_file.write_text(json.dumps(sample_palace))

        result = repo.delete_palace(sample_palace["id"])

        assert result is True
        assert not palace_file.exists()

    @pytest.mark.unit
    def test_delete_palace_returns_false_for_missing(
        self, repo: PalaceRepository
    ) -> None:
        """Scenario: Delete a palace that does not exist
        Given an empty repository
        When I delete a non-existent palace ID
        Then False is returned.
        """
        result = repo.delete_palace("ghost-palace")
        assert result is False

    @pytest.mark.unit
    def test_delete_palace_creates_backup(
        self, repo: PalaceRepository, sample_palace: dict[str, Any]
    ) -> None:
        """Scenario: Deletion creates a final backup
        Given a palace file on disk
        When I delete it
        Then a backup file exists in the backups directory.
        """
        palace_file = Path(repo.palaces_dir) / f"{sample_palace['id']}.json"
        palace_file.write_text(json.dumps(sample_palace))

        repo.delete_palace(sample_palace["id"])

        backups = list((Path(repo.palaces_dir) / "backups").glob("*.json"))
        assert len(backups) >= 1


class TestPalaceRepositoryIndex:
    """Feature: Master index management.

    As a user
    I want a master index of all palaces
    So that I can list and query them efficiently
    """

    @pytest.mark.unit
    def test_get_master_index_returns_default_when_missing(
        self, repo: PalaceRepository
    ) -> None:
        """Scenario: No index file exists yet
        Given a fresh repository with no index file
        When I call get_master_index
        Then I get a default empty index structure.
        """
        index = repo.get_master_index()

        assert "palaces" in index
        assert index["palaces"] == []
        assert index["global_stats"]["total_palaces"] == 0

    @pytest.mark.unit
    def test_list_palaces_returns_empty_for_new_repo(
        self, repo: PalaceRepository
    ) -> None:
        """Scenario: List palaces in an empty repository
        Given no palaces have been created
        When I call list_palaces
        Then an empty list is returned.
        """
        assert repo.list_palaces() == []

    @pytest.mark.unit
    def test_list_palaces_after_creating_multiple(self, repo: PalaceRepository) -> None:
        """Scenario: List palaces after creating several
        Given three palaces created in the repository
        When I call list_palaces
        Then three summaries are returned.
        """
        repo.create_palace("Palace A", "domain-a")
        repo.create_palace("Palace B", "domain-b")
        repo.create_palace("Palace C", "domain-c")

        palaces = repo.list_palaces()
        assert len(palaces) == 3

    @pytest.mark.unit
    def test_update_master_index_counts_domains(self, repo: PalaceRepository) -> None:
        """Scenario: Master index tallies domains correctly
        Given two palaces in the same domain and one in another
        When I call update_master_index
        Then domain counts are accurate.
        """
        repo.create_palace("P1", "programming")
        repo.create_palace("P2", "programming")
        repo.create_palace("P3", "mathematics")

        index = repo.get_master_index()
        domains = index["global_stats"]["domains"]

        assert domains.get("programming") == 2
        assert domains.get("mathematics") == 1
