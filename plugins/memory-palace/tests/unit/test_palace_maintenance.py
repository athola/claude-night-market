"""Tests for PalaceMaintenance — queue ingestion, pruning, import/export.

Feature: Palace Maintenance
  As a user
  I want maintenance operations on palaces
  So that the palace store stays tidy and up-to-date
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from memory_palace.palace_maintenance import PalaceMaintenance


@pytest.fixture
def mock_repo() -> MagicMock:
    """Return a mock PalaceRepository."""
    repo = MagicMock()
    repo.list_palaces.return_value = []
    repo.load_palace.return_value = None
    repo.palaces_dir = "/tmp/palaces"  # noqa: S108 - test fixture uses mock path
    return repo


@pytest.fixture
def maintenance(mock_repo: MagicMock) -> PalaceMaintenance:
    """Return a PalaceMaintenance backed by a mock repository."""
    return PalaceMaintenance(mock_repo)


@pytest.fixture
def sample_palace() -> dict[str, Any]:
    """Return a palace with associations suitable for prune tests."""
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=120)).isoformat()
    return {
        "id": "maint001",
        "name": "Maintenance Palace",
        "domain": "testing",
        "associations": {
            "fresh-entry": {
                "query": "fresh query",
                "timestamp": now.isoformat(),
                "novelty_score": 0.9,
            },
            "stale-entry": {
                "query": "stale query",
                "timestamp": old,
                "novelty_score": 0.9,
            },
            "low-quality": {
                "query": "low quality query",
                "timestamp": now.isoformat(),
                "novelty_score": 0.1,
            },
        },
        "metadata": {"concept_count": 3},
    }


class TestExtractDomain:
    """Feature: Domain extraction from query strings.

    As a maintenance module
    I want to extract a domain keyword from a query
    So that entries can be routed to the right palace
    """

    @pytest.mark.unit
    def test_extract_domain_returns_first_significant_word(
        self, maintenance: PalaceMaintenance
    ) -> None:
        """Scenario: Extract domain from a simple query
        Given a query "test python decorators"
        When I extract the domain
        Then "python" is returned (first word > 2 chars, not a stopword).
        """
        domain = maintenance._extract_domain("test python decorators")
        assert domain == "python"

    @pytest.mark.unit
    def test_extract_domain_skips_stopwords(
        self, maintenance: PalaceMaintenance
    ) -> None:
        """Scenario: Stopwords are skipped during extraction
        Given a query that starts with "the"
        When I extract the domain
        Then the first non-stopword is returned.
        """
        domain = maintenance._extract_domain("the async patterns")
        assert domain == "async"

    @pytest.mark.unit
    def test_extract_domain_returns_empty_for_all_stopwords(
        self, maintenance: PalaceMaintenance
    ) -> None:
        """Scenario: All words are stopwords
        Given a query consisting entirely of stopwords
        When I extract the domain
        Then an empty string is returned.
        """
        domain = maintenance._extract_domain("the a an")
        assert domain == ""


class TestSyncFromQueue:
    """Feature: Syncing intake queue entries into palaces.

    As a user
    I want queue entries routed into matching palaces
    So that new knowledge lands in the right place automatically
    """

    @pytest.mark.unit
    def test_sync_from_queue_returns_empty_for_missing_file(
        self, maintenance: PalaceMaintenance
    ) -> None:
        """Scenario: Queue file does not exist
        Given a path to a non-existent queue file
        When I sync from queue
        Then results show zero processed with no errors.
        """
        results = maintenance.sync_from_queue("/nonexistent/path/queue.jsonl")

        assert results["processed"] == 0
        assert results["skipped"] == 0

    @pytest.mark.unit
    def test_sync_from_queue_dry_run_does_not_save(
        self, mock_repo: MagicMock, maintenance: PalaceMaintenance, tmp_path: Path
    ) -> None:
        """Scenario: Dry run leaves palaces unmodified
        Given a queue file with one entry and a matching palace
        When I sync with dry_run=True
        Then no save is called on the repository.
        """
        palace = {
            "id": "dry001",
            "name": "Dry Palace",
            "domain": "python",
            "associations": {},
            "metadata": {"concept_count": 0},
        }
        mock_repo.list_palaces.return_value = [{"id": "dry001"}]
        mock_repo.load_palace.return_value = palace

        queue_file = tmp_path / "queue.jsonl"
        entry = {"query": "python decorators", "timestamp": "2025-01-01T00:00:00Z"}
        queue_file.write_text(json.dumps(entry) + "\n")

        maintenance.sync_from_queue(str(queue_file), dry_run=True)

        mock_repo.save_palace.assert_not_called()

    @pytest.mark.unit
    def test_sync_from_queue_processes_matching_entry(
        self, mock_repo: MagicMock, maintenance: PalaceMaintenance, tmp_path: Path
    ) -> None:
        """Scenario: Entry matches an existing palace domain
        Given a queue file with one entry matching the "python" domain
        When I sync (not dry run)
        Then processed count is 1 and save_palace is called.
        """
        palace = {
            "id": "py001",
            "name": "Python Palace",
            "domain": "python",
            "associations": {},
            "metadata": {"concept_count": 0},
        }
        mock_repo.list_palaces.return_value = [{"id": "py001"}]
        mock_repo.load_palace.return_value = palace

        queue_file = tmp_path / "queue.jsonl"
        entry = {"query": "python decorators", "timestamp": "2025-01-01T00:00:00Z"}
        queue_file.write_text(json.dumps(entry) + "\n")

        results = maintenance.sync_from_queue(str(queue_file))

        assert results["processed"] == 1
        mock_repo.save_palace.assert_called_once()

    @pytest.mark.unit
    def test_sync_from_queue_unmatched_goes_to_skipped(
        self, mock_repo: MagicMock, maintenance: PalaceMaintenance, tmp_path: Path
    ) -> None:
        """Scenario: Entry has no matching palace and auto_create is False
        Given an entry whose domain matches no palace
        When I sync without auto_create
        Then skipped count is 1 and the entry is in unmatched.
        """
        mock_repo.list_palaces.return_value = []

        queue_file = tmp_path / "queue.jsonl"
        entry = {"query": "quantum physics entanglement"}
        queue_file.write_text(json.dumps(entry) + "\n")

        results = maintenance.sync_from_queue(str(queue_file))

        assert results["skipped"] == 1
        assert len(results["unmatched"]) == 1


class TestPruneCheck:
    """Feature: Identifying stale and low-quality entries.

    As a user
    I want to identify entries needing cleanup
    So that palace quality stays high over time
    """

    @pytest.mark.unit
    def test_prune_check_identifies_stale_entries(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Stale entries are identified
        Given a palace with one entry older than 90 days
        When I run prune_check
        Then total_stale is 1.
        """
        mock_repo.list_palaces.return_value = [{"id": sample_palace["id"]}]
        mock_repo.load_palace.return_value = sample_palace

        results = maintenance.prune_check(stale_days=90)

        assert results["total_stale"] == 1

    @pytest.mark.unit
    def test_prune_check_identifies_low_quality_entries(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Low-quality entries are identified
        Given a palace with one entry with novelty_score < 0.3
        When I run prune_check
        Then total_low_quality is 1.
        """
        mock_repo.list_palaces.return_value = [{"id": sample_palace["id"]}]
        mock_repo.load_palace.return_value = sample_palace

        results = maintenance.prune_check()

        assert results["total_low_quality"] == 1

    @pytest.mark.unit
    def test_prune_check_returns_zero_for_empty_repo(
        self, mock_repo: MagicMock, maintenance: PalaceMaintenance
    ) -> None:
        """Scenario: No palaces to check
        Given an empty repository
        When I run prune_check
        Then all counts are zero.
        """
        mock_repo.list_palaces.return_value = []

        results = maintenance.prune_check()

        assert results["palaces_checked"] == 0
        assert results["total_stale"] == 0
        assert results["total_low_quality"] == 0


class TestApplyPrune:
    """Feature: Applying prune actions.

    As a user
    I want to remove stale and low-quality entries
    So that palace data stays fresh
    """

    @pytest.mark.unit
    def test_apply_prune_removes_stale_entries(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Apply stale prune action
        Given recommendations identifying one stale entry
        When I apply with actions=["stale"]
        Then that entry is removed and save_palace is called.
        """
        mock_repo.load_palace.return_value = dict(sample_palace)

        recommendations = {
            "recommendations": [
                {
                    "palace_id": sample_palace["id"],
                    "stale": ["stale-entry"],
                    "low_quality": [],
                }
            ]
        }

        removed = maintenance.apply_prune(recommendations, ["stale"])

        assert removed["stale"] == 1
        mock_repo.save_palace.assert_called_once()

    @pytest.mark.unit
    def test_apply_prune_removes_low_quality_entries(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Apply low_quality prune action
        Given recommendations identifying one low-quality entry
        When I apply with actions=["low_quality"]
        Then that entry is removed.
        """
        mock_repo.load_palace.return_value = dict(sample_palace)

        recommendations = {
            "recommendations": [
                {
                    "palace_id": sample_palace["id"],
                    "stale": [],
                    "low_quality": ["low-quality"],
                }
            ]
        }

        removed = maintenance.apply_prune(recommendations, ["low_quality"])

        assert removed["low_quality"] == 1


class TestImportExport:
    """Feature: Import and export of palace state.

    As a user
    I want to export all palaces to a single file
    And import them back
    So that I can backup and restore my palace store
    """

    @pytest.mark.unit
    def test_export_state_creates_bundle_file(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        tmp_path: Path,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Export creates a bundle JSON file
        Given one palace in the repository
        When I export state
        Then a JSON file is written at the destination path.
        """
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        palace_file = palaces_dir / f"{sample_palace['id']}.json"
        palace_file.write_text(json.dumps(sample_palace))
        mock_repo.palaces_dir = str(palaces_dir)

        dest = tmp_path / "export" / "bundle.json"
        result_path = maintenance.export_state(str(dest))

        assert Path(result_path).exists()
        bundle = json.loads(Path(result_path).read_text())
        assert "palaces" in bundle
        assert len(bundle["palaces"]) == 1

    @pytest.mark.unit
    def test_import_state_writes_palace_files(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        tmp_path: Path,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Import writes palace files from a bundle
        Given a bundle JSON containing one palace
        When I import state
        Then imported count is 1 and update_master_index is called.
        """
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        mock_repo.palaces_dir = str(palaces_dir)

        bundle = {"palaces": [sample_palace], "exported_at": "2025-01-01T00:00:00Z"}
        source = tmp_path / "bundle.json"
        source.write_text(json.dumps(bundle))

        result = maintenance.import_state(str(source))

        assert result["imported"] == 1
        assert result["skipped"] == 0
        mock_repo.update_master_index.assert_called_once()

    @pytest.mark.unit
    def test_import_state_skips_existing_when_keep(
        self,
        mock_repo: MagicMock,
        maintenance: PalaceMaintenance,
        tmp_path: Path,
        sample_palace: dict[str, Any],
    ) -> None:
        """Scenario: Import skips palaces that already exist when keep_existing=True
        Given a palace already on disk and a bundle containing the same palace
        When I import with keep_existing=True
        Then skipped count is 1 and imported count is 0.
        """
        palaces_dir = tmp_path / "palaces"
        palaces_dir.mkdir()
        mock_repo.palaces_dir = str(palaces_dir)

        # Pre-existing file
        existing = palaces_dir / f"{sample_palace['id']}.json"
        existing.write_text(json.dumps(sample_palace))

        bundle = {"palaces": [sample_palace]}
        source = tmp_path / "bundle.json"
        source.write_text(json.dumps(bundle))

        result = maintenance.import_state(str(source), keep_existing=True)

        assert result["skipped"] == 1
        assert result["imported"] == 0
