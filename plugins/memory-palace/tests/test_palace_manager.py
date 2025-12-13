"""Tests for palace_manager.py - Memory Palace CRUD operations.

BDD-style tests organized by behavior:
- Palace lifecycle (create, load, save, delete)
- Master index management
- Search operations
- Export/Import functionality
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from memory_palace.palace_manager import MemoryPalaceManager

PALACE_COUNT = 3
PROGRAMMING_COUNT = 2


class TestMemoryPalaceManagerInitialization:
    """Tests for MemoryPalaceManager initialization."""

    def test_initializes_with_config_and_directory(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
    ) -> None:
        """Initialize manager with explicit config and directory paths."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )
        assert manager.palaces_dir == str(temp_palaces_dir)

    def test_creates_directories_on_init(self, temp_config_file: Path, tmp_path: Path) -> None:
        """Create palaces and backups directories if they don't exist."""
        new_palaces_dir = tmp_path / "new_palaces"
        assert not new_palaces_dir.exists()

        MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(new_palaces_dir),
        )

        assert new_palaces_dir.exists()
        assert (new_palaces_dir / "backups").exists()

    def test_respects_environment_variable(
        self,
        temp_config_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Use PALACES_DIR environment variable when no override provided."""
        env_palaces_dir = tmp_path / "env_palaces"
        env_palaces_dir.mkdir()
        monkeypatch.setenv("PALACES_DIR", str(env_palaces_dir))

        manager = MemoryPalaceManager(config_path=str(temp_config_file))
        assert manager.palaces_dir == str(env_palaces_dir)

    def test_override_takes_precedence_over_env(
        self,
        temp_config_file: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Explicit override takes precedence over environment variable."""
        env_dir = tmp_path / "env_palaces"
        override_dir = tmp_path / "override_palaces"
        env_dir.mkdir()
        override_dir.mkdir()
        monkeypatch.setenv("PALACES_DIR", str(env_dir))

        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(override_dir),
        )
        assert manager.palaces_dir == str(override_dir)


class TestPalaceCreation:
    """Tests for creating new memory palaces."""

    def test_creates_palace_with_required_fields(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
    ) -> None:
        """Create palace returns dict with required structure."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palace = manager.create_palace("Test Palace", "programming")

        assert "id" in palace
        assert palace["name"] == "Test Palace"
        assert palace["domain"] == "programming"
        assert palace["metaphor"] == "building"  # default
        assert "created" in palace
        assert "last_modified" in palace
        assert "layout" in palace
        assert "associations" in palace
        assert "sensory_encoding" in palace
        assert "metadata" in palace

    def test_creates_palace_with_custom_metaphor(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
    ) -> None:
        """Create palace with custom architectural metaphor."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palace = manager.create_palace("Rust Fortress", "rust", metaphor="fortress")
        assert palace["metaphor"] == "fortress"

    def test_generates_unique_palace_ids(
        self, temp_config_file: Path, temp_palaces_dir: Path
    ) -> None:
        """Each palace gets a unique ID."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palace1 = manager.create_palace("Palace 1", "domain1")
        palace2 = manager.create_palace("Palace 2", "domain2")

        assert palace1["id"] != palace2["id"]

    def test_persists_palace_to_disk(self, temp_config_file: Path, temp_palaces_dir: Path) -> None:
        """Created palace is saved to a JSON file."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palace = manager.create_palace("Persisted Palace", "testing")
        palace_file = temp_palaces_dir / f"{palace['id']}.json"

        assert palace_file.exists()
        with open(palace_file) as f:
            saved_data = json.load(f)
        assert saved_data["name"] == "Persisted Palace"

    def test_updates_master_index_on_create(
        self, temp_config_file: Path, temp_palaces_dir: Path
    ) -> None:
        """Master index is updated after palace creation."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palace = manager.create_palace("Indexed Palace", "testing")
        index = manager.get_master_index()

        assert any(p["id"] == palace["id"] for p in index["palaces"])
        assert index["global_stats"]["total_palaces"] >= 1


class TestPalaceLoading:
    """Tests for loading palaces from storage."""

    def test_loads_existing_palace(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Load palace by ID returns correct data."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )

        loaded = manager.load_palace(sample_palace_data["id"])

        assert loaded is not None
        assert loaded["name"] == sample_palace_data["name"]
        assert loaded["domain"] == sample_palace_data["domain"]

    def test_returns_none_for_nonexistent_palace(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
    ) -> None:
        """Loading nonexistent palace returns None."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        result = manager.load_palace("nonexistent_id")
        assert result is None


class TestPalaceSaving:
    """Tests for saving palace modifications."""

    def test_saves_palace_updates(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Save palace persists modifications to disk."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )

        # Modify and save
        sample_palace_data["name"] = "Updated Palace Name"
        manager.save_palace(sample_palace_data)

        # Verify persisted
        loaded = manager.load_palace(sample_palace_data["id"])
        assert loaded["name"] == "Updated Palace Name"

    def test_updates_last_modified_timestamp(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Saving updates the last_modified timestamp."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )

        original_modified = sample_palace_data["last_modified"]
        manager.save_palace(sample_palace_data)

        loaded = manager.load_palace(sample_palace_data["id"])
        assert loaded["last_modified"] != original_modified

    def test_creates_backup_before_save(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Backup is created before overwriting palace file."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )
        backups_dir = sample_palace_file.parent / "backups"

        initial_backups = list(backups_dir.glob("*.json"))
        manager.save_palace(sample_palace_data)

        new_backups = list(backups_dir.glob("*.json"))
        assert len(new_backups) > len(initial_backups)


class TestPalaceDeletion:
    """Tests for deleting palaces."""

    def test_deletes_existing_palace(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Delete palace removes file and returns True."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )

        result = manager.delete_palace(sample_palace_data["id"])

        assert result is True
        assert not sample_palace_file.exists()

    def test_returns_false_for_nonexistent_palace(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
    ) -> None:
        """Deleting nonexistent palace returns False."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        result = manager.delete_palace("nonexistent")
        assert result is False

    def test_creates_backup_before_delete(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Backup is created before deleting palace."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )
        backups_dir = sample_palace_file.parent / "backups"

        initial_backups = list(backups_dir.glob("*.json"))
        manager.delete_palace(sample_palace_data["id"])

        new_backups = list(backups_dir.glob("*.json"))
        assert len(new_backups) > len(initial_backups)

    def test_updates_master_index_on_delete(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Master index is updated after deletion."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )

        # Force index update first
        manager.update_master_index()
        index_before = manager.get_master_index()
        palace_count_before = index_before["global_stats"]["total_palaces"]

        manager.delete_palace(sample_palace_data["id"])
        index_after = manager.get_master_index()

        assert index_after["global_stats"]["total_palaces"] == palace_count_before - 1


class TestMasterIndex:
    """Tests for master index management."""

    def test_builds_index_from_palace_files(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Master index aggregates all palace summaries."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        index = manager.get_master_index()

        assert len(index["palaces"]) == PALACE_COUNT
        assert index["global_stats"]["total_palaces"] == PALACE_COUNT

    def test_counts_concepts_per_domain(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Index tracks concept counts by domain."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        index = manager.get_master_index()
        domains = index["global_stats"]["domains"]

        assert "programming" in domains
        assert "mathematics" in domains
        assert domains["programming"] == PROGRAMMING_COUNT  # Two programming palaces

    def test_handles_empty_directory(self, temp_config_file: Path, temp_palaces_dir: Path) -> None:
        """Empty directory returns valid empty index."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        index = manager.get_master_index()

        assert index["palaces"] == []
        assert index["global_stats"]["total_palaces"] == 0

    def test_index_contains_palace_metadata(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Index entries contain essential palace metadata."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        index = manager.get_master_index()
        entry = index["palaces"][0]

        assert "id" in entry
        assert "name" in entry
        assert "domain" in entry
        assert "metaphor" in entry
        assert "created" in entry
        assert "last_modified" in entry
        assert "concept_count" in entry


class TestListPalaces:
    """Tests for listing palaces."""

    def test_lists_all_palaces(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """List returns all palaces from index."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palaces = manager.list_palaces()
        assert len(palaces) == PALACE_COUNT

    def test_returns_empty_list_when_no_palaces(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
    ) -> None:
        """Returns empty list when no palaces exist."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        palaces = manager.list_palaces()
        assert palaces == []


class TestSearchOperations:
    """Tests for searching within palaces."""

    def test_semantic_search_finds_matching_associations(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Semantic search finds text in associations."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        results = manager.search_palaces("decorators", search_type="semantic")

        assert len(results) >= 1
        assert any("Python" in r["palace_name"] for r in results)

    def test_search_returns_empty_for_no_matches(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Search returns empty list when no matches found."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        results = manager.search_palaces("nonexistent_concept_xyz")
        assert results == []

    def test_fuzzy_search_matches_partial_words(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Fuzzy search matches partial query words."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        # "memory" should match via fuzzy search
        results = manager.search_palaces("memory safety", search_type="fuzzy")

        assert len(results) >= 1

    def test_search_result_structure(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
    ) -> None:
        """Search results have correct structure."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        results = manager.search_palaces("ownership")

        if results:
            result = results[0]
            assert "palace_id" in result
            assert "palace_name" in result
            assert "matches" in result


class TestExportImport:
    """Tests for export and import functionality."""

    def test_exports_all_palaces_to_bundle(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        multiple_palaces: list,
        tmp_path: Path,
    ) -> None:
        """Export creates bundle with all palaces."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        export_file = tmp_path / "export.json"
        result_path = manager.export_state(str(export_file))

        assert Path(result_path).exists()
        with open(result_path) as f:
            bundle = json.load(f)
        assert "exported_at" in bundle
        assert len(bundle["palaces"]) == PALACE_COUNT

    def test_imports_palaces_from_bundle(self, temp_config_file: Path, tmp_path: Path) -> None:
        """Import loads palaces from bundle into storage."""
        # Create a bundle to import
        bundle = {
            "exported_at": datetime.now().isoformat(),
            "palaces": [
                {
                    "id": "imported1",
                    "name": "Imported Palace",
                    "domain": "imported",
                    "metaphor": "house",
                    "created": "2025-01-01T00:00:00",
                    "last_modified": "2025-01-01T00:00:00",
                    "layout": {"districts": [], "buildings": [], "rooms": [], "connections": []},
                    "associations": {},
                    "sensory_encoding": {},
                    "metadata": {
                        "concept_count": 0,
                        "complexity_level": "basic",
                        "access_patterns": [],
                    },
                },
            ],
        }

        bundle_file = tmp_path / "bundle.json"
        bundle_file.write_text(json.dumps(bundle))

        import_dir = tmp_path / "import_target"
        import_dir.mkdir()
        (import_dir / "backups").mkdir()

        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(import_dir),
        )

        stats = manager.import_state(str(bundle_file))

        assert stats["imported"] == 1
        assert (import_dir / "imported1.json").exists()

    def test_import_skips_existing_by_default(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        sample_palace_file: Path,
        tmp_path: Path,
    ) -> None:
        """Import skips palaces that already exist by default."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        # Create bundle with same ID as existing palace
        bundle = {
            "exported_at": datetime.now().isoformat(),
            "palaces": [
                {
                    "id": "test1234",  # Same as sample_palace_data
                    "name": "Duplicate Palace",
                    "domain": "duplicate",
                    "metaphor": "building",
                    "created": "2025-01-01T00:00:00",
                    "last_modified": "2025-01-01T00:00:00",
                    "layout": {"districts": [], "buildings": [], "rooms": [], "connections": []},
                    "associations": {},
                    "sensory_encoding": {},
                    "metadata": {
                        "concept_count": 0,
                        "complexity_level": "basic",
                        "access_patterns": [],
                    },
                },
            ],
        }

        bundle_file = tmp_path / "bundle.json"
        bundle_file.write_text(json.dumps(bundle))

        stats = manager.import_state(str(bundle_file), keep_existing=True)

        assert stats["skipped"] == 1
        assert stats["imported"] == 0

    def test_import_overwrites_when_requested(
        self,
        temp_config_file: Path,
        temp_palaces_dir: Path,
        sample_palace_file: Path,
        tmp_path: Path,
    ) -> None:
        """Import overwrites existing palaces when keep_existing=False."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )

        # Create bundle with same ID as existing palace
        bundle = {
            "exported_at": datetime.now().isoformat(),
            "palaces": [
                {
                    "id": "test1234",  # Same as sample_palace_data
                    "name": "Overwritten Palace",
                    "domain": "overwritten",
                    "metaphor": "building",
                    "created": "2025-01-01T00:00:00",
                    "last_modified": "2025-01-01T00:00:00",
                    "layout": {"districts": [], "buildings": [], "rooms": [], "connections": []},
                    "associations": {},
                    "sensory_encoding": {},
                    "metadata": {
                        "concept_count": 0,
                        "complexity_level": "basic",
                        "access_patterns": [],
                    },
                },
            ],
        }

        bundle_file = tmp_path / "bundle.json"
        bundle_file.write_text(json.dumps(bundle))

        stats = manager.import_state(str(bundle_file), keep_existing=False)

        assert stats["imported"] == 1

        # Verify overwritten
        loaded = manager.load_palace("test1234")
        assert loaded["name"] == "Overwritten Palace"


class TestBackupCreation:
    """Tests for backup functionality."""

    def test_creates_timestamped_backup(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Backup files include timestamp in filename."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )
        backups_dir = sample_palace_file.parent / "backups"

        manager.create_backup(sample_palace_data["id"])

        backups = list(backups_dir.glob(f"{sample_palace_data['id']}_*.json"))
        assert len(backups) >= 1

        # Verify filename contains timestamp pattern
        backup_name = backups[0].stem
        assert sample_palace_data["id"] in backup_name

    def test_backup_contains_original_data(
        self,
        temp_config_file: Path,
        sample_palace_file: Path,
        sample_palace_data: dict,
    ) -> None:
        """Backup file contains exact copy of original."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(sample_palace_file.parent),
        )
        backups_dir = sample_palace_file.parent / "backups"

        manager.create_backup(sample_palace_data["id"])

        backup_file = next(iter(backups_dir.glob(f"{sample_palace_data['id']}_*.json")))
        with open(backup_file) as f:
            backup_data = json.load(f)

        assert backup_data["name"] == sample_palace_data["name"]
        assert backup_data["id"] == sample_palace_data["id"]

    def test_no_backup_for_nonexistent_palace(
        self, temp_config_file: Path, temp_palaces_dir: Path
    ) -> None:
        """Creating backup for nonexistent palace is a no-op."""
        manager = MemoryPalaceManager(
            config_path=str(temp_config_file),
            palaces_dir_override=str(temp_palaces_dir),
        )
        backups_dir = temp_palaces_dir / "backups"

        initial_backups = list(backups_dir.glob("*.json"))
        manager.create_backup("nonexistent")

        assert len(list(backups_dir.glob("*.json"))) == len(initial_backups)
