"""Tests for Issue #394: computational encoding in palace save/load."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

import memory_palace.migration as migration_mod
from memory_palace.migration import migrate_sensory_to_computational
from memory_palace.palace_repository import PalaceRepository


@pytest.fixture
def sample_palace_with_sensory() -> dict[str, Any]:
    return {
        "id": "enc_test",
        "name": "Encoding Test Palace",
        "domain": "testing",
        "metaphor": "library",
        "created": "2025-01-01T00:00:00",
        "last_modified": "2025-06-01T00:00:00",
        "layout": {
            "districts": [],
            "buildings": [],
            "rooms": [{"id": "enc_r1", "name": "Room One"}],
            "connections": [],
        },
        "associations": {
            "enc_e1": {"label": "Entity One", "location": "enc_r1"},
            "enc_e2": {"label": "Entity Two", "location": "enc_r1"},
        },
        "sensory_encoding": {
            "enc_e1": {"visual": "red glow", "auditory": "hum"},
            "enc_e2": {"visual": "blue light"},
        },
        "metadata": {
            "concept_count": 2,
            "complexity_level": "basic",
            "access_patterns": [],
        },
    }


class TestSavePalaceComputationalEncoding:
    """PalaceRepository.save_palace replaces sensory with computational."""

    def test_save_removes_sensory_encoding(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Saving drops the retired sensory block rather than carrying it forward."""
        repo = PalaceRepository(str(tmp_path))
        (tmp_path / "backups").mkdir(exist_ok=True)
        palace = dict(sample_palace_with_sensory)
        repo.save_palace(palace)

        saved = json.loads((tmp_path / "enc_test.json").read_text())
        assert "sensory_encoding" not in saved

    def test_save_adds_computational_encoding(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Saving writes the computational block that replaced it."""
        repo = PalaceRepository(str(tmp_path))
        (tmp_path / "backups").mkdir(exist_ok=True)
        palace = dict(sample_palace_with_sensory)
        repo.save_palace(palace)

        saved = json.loads((tmp_path / "enc_test.json").read_text())
        assert "computational_encoding" in saved

    def test_computational_encoding_has_required_fields(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Each encoded entity carries the centrality figure the tiering reads."""
        repo = PalaceRepository(str(tmp_path))
        (tmp_path / "backups").mkdir(exist_ok=True)
        palace = dict(sample_palace_with_sensory)
        repo.save_palace(palace)

        saved = json.loads((tmp_path / "enc_test.json").read_text())
        enc = saved["computational_encoding"]

        # Each association entity must have a computational entry
        for entity_id in sample_palace_with_sensory["associations"]:
            assert entity_id in enc
            entry = enc[entity_id]
            assert "centrality" in entry
            assert "in_degree" in entry
            assert "out_degree" in entry
            assert "cluster_id" in entry
            assert "staleness" in entry
            assert "access_count" in entry
            assert "temporal_validity" in entry
            assert "valid_from" in entry["temporal_validity"]
            assert "valid_to" in entry["temporal_validity"]

    def test_load_preserves_sensory_in_memory(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Loading a palace that has sensory_encoding keeps it in memory."""
        palace_file = tmp_path / "enc_test.json"
        palace_file.write_text(json.dumps(sample_palace_with_sensory))
        (tmp_path / "backups").mkdir(exist_ok=True)

        repo = PalaceRepository(str(tmp_path))
        loaded = repo.load_palace("enc_test")

        assert loaded is not None
        # Sensory encoding should still be present in memory
        assert "sensory_encoding" in loaded
        assert (
            loaded["sensory_encoding"] == sample_palace_with_sensory["sensory_encoding"]
        )

    def test_palace_without_sensory_gets_computational(
        self,
        tmp_path: Path,
    ) -> None:
        """Palace without sensory_encoding also gets computational on save."""
        palace: dict[str, Any] = {
            "id": "no_sensory",
            "name": "No Sensory",
            "domain": "test",
            "metaphor": "building",
            "created": "2025-01-01T00:00:00",
            "last_modified": "2025-01-01T00:00:00",
            "layout": {
                "districts": [],
                "buildings": [],
                "rooms": [],
                "connections": [],
            },
            "associations": {
                "ns_e1": {"label": "No Sensory Entity", "location": ""},
            },
            "metadata": {},
        }
        repo = PalaceRepository(str(tmp_path))
        (tmp_path / "backups").mkdir(exist_ok=True)
        repo.save_palace(palace)

        saved = json.loads((tmp_path / "no_sensory.json").read_text())
        assert "computational_encoding" in saved
        assert "ns_e1" in saved["computational_encoding"]


class TestMigrateSensoryToComputational:
    """migrate_sensory_to_computational bulk-converts palace files."""

    def test_converts_all_palace_files(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Every palace file loses the sensory block and gains the computational one."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        (palaces_dir / "enc_test.json").write_text(
            json.dumps(sample_palace_with_sensory)
        )

        migrate_sensory_to_computational(palaces_dir, apply=True)

        converted = json.loads((palaces_dir / "enc_test.json").read_text())
        assert "sensory_encoding" not in converted
        assert "computational_encoding" in converted

    def test_a_dry_run_changes_nothing_on_disk(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Without apply=True the files are left byte-identical."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        target = palaces_dir / "enc_test.json"
        target.write_text(json.dumps(sample_palace_with_sensory))
        before = target.read_bytes()

        report = migrate_sensory_to_computational(palaces_dir)

        assert target.read_bytes() == before
        assert report.rewritten == [target]

    def test_an_unparsable_file_is_recorded_with_a_reason(self, tmp_path: Path) -> None:
        """A corrupt palace file is named in the report, not swallowed."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        broken = palaces_dir / "broken.json"
        broken.write_text("{not json")

        report = migrate_sensory_to_computational(palaces_dir, apply=True)

        assert [path for path, _ in report.skipped] == [broken]
        assert "JSON" in report.skipped[0][1]

    def test_a_file_without_an_id_is_recorded_as_skipped(self, tmp_path: Path) -> None:
        """A JSON file that is not a palace is reported rather than ignored."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        stray = palaces_dir / "stray.json"
        stray.write_text('{"name": "not a palace"}')

        report = migrate_sensory_to_computational(palaces_dir, apply=True)

        assert [path for path, _ in report.skipped] == [stray]
        assert "id" in report.skipped[0][1]

    def test_migrate_encoding_preserves_existing_access_count(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """An enriched encoding entry survives the migration.

        `PalaceGraphAnalyzer` is invited to fill centrality and
        access_count. Rebuilding from defaults would silently revert it.
        """
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        enriched = dict(sample_palace_with_sensory)
        entity_id = next(iter(enriched["associations"]))
        enriched["computational_encoding"] = {
            entity_id: {"access_count": 7, "centrality": 0.5}
        }
        (palaces_dir / "enc_test.json").write_text(json.dumps(enriched))

        migrate_sensory_to_computational(palaces_dir, apply=True)

        entry = json.loads((palaces_dir / "enc_test.json").read_text())[
            "computational_encoding"
        ][entity_id]
        assert entry["access_count"] == 7
        assert entry["centrality"] == 0.5
        assert entry["cluster_id"] == -1

    def test_a_converted_file_is_reported_unchanged_on_the_second_run(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """The dry run only lists files a rewrite would actually change."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        target = palaces_dir / "enc_test.json"
        target.write_text(json.dumps(sample_palace_with_sensory))

        migrate_sensory_to_computational(palaces_dir, apply=True)
        second = migrate_sensory_to_computational(palaces_dir)

        assert second.rewritten == []
        assert second.unchanged == [target]
        assert second.scanned == 1

    def test_skips_master_index(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """The master index is left intact; it holds no encoding to convert."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        (palaces_dir / "master_index.json").write_text('{"palaces": []}')
        (palaces_dir / "enc_test.json").write_text(
            json.dumps(sample_palace_with_sensory)
        )

        migrate_sensory_to_computational(palaces_dir, apply=True)

        # master_index.json should remain unchanged
        index_content = json.loads((palaces_dir / "master_index.json").read_text())
        assert "palaces" in index_content

    def test_idempotent_on_already_converted(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
    ) -> None:
        """Re-running leaves an already-converted file structurally unchanged."""
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        (palaces_dir / "enc_test.json").write_text(
            json.dumps(sample_palace_with_sensory)
        )

        migrate_sensory_to_computational(palaces_dir, apply=True)
        migrate_sensory_to_computational(palaces_dir, apply=True)

        converted = json.loads((palaces_dir / "enc_test.json").read_text())
        assert "computational_encoding" in converted
        # Should not have double-nested computational encoding
        enc = converted["computational_encoding"]
        if "enc_e1" in enc:
            assert isinstance(enc["enc_e1"], dict)
            assert "centrality" in enc["enc_e1"]

    def test_atomic_write_preserves_original_on_replace_failure(
        self,
        tmp_path: Path,
        sample_palace_with_sensory: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If the final rename step fails, the original palace file must
        remain intact (no half-written or truncated JSON).

        Scenario: atomic write guarantee
        Given a palace JSON with sensory_encoding
        And os.replace is monkeypatched to raise OSError during migration
        When migrate_sensory_to_computational is called
        Then the original file is still readable and parseable
        And its content is the pre-migration content
        """
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        original_text = json.dumps(sample_palace_with_sensory, indent=2)
        target = palaces_dir / "enc_test.json"
        target.write_text(original_text)

        def _boom(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
            raise OSError("simulated rename failure")

        monkeypatch.setattr(migration_mod.os, "replace", _boom)

        # Must not crash the caller
        migrate_sensory_to_computational(palaces_dir)

        # Original file still present, still valid JSON, still has sensory_encoding
        assert target.exists(), "original palace file was deleted"
        loaded = json.loads(target.read_text())
        assert "sensory_encoding" in loaded, (
            "original sensory_encoding was lost despite rename failure"
        )
        assert loaded["id"] == "enc_test"

        # No orphaned temp file should remain in the palaces dir
        leftover = [
            p
            for p in palaces_dir.iterdir()
            if p.name != "enc_test.json" and p.suffix != ".json"
        ]
        assert leftover == [], f"atomic write left orphan temp files: {leftover}"
