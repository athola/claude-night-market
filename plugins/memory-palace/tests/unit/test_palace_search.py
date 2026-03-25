"""Tests for PalaceSearchEngine — search_palaces, _search_in_palace, _matches_query.

Feature: Palace Search
  As a user
  I want to search across memory palaces
  So that I can find stored knowledge quickly
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from memory_palace.palace_search import PalaceSearchEngine


@pytest.fixture
def mock_repo() -> MagicMock:
    """Return a mock PalaceRepository."""
    repo = MagicMock()
    repo.get_master_index.return_value = {"palaces": []}
    repo.load_palace.return_value = None
    return repo


@pytest.fixture
def engine(mock_repo: MagicMock) -> PalaceSearchEngine:
    """Return a search engine with a mock repository."""
    return PalaceSearchEngine(mock_repo)


@pytest.fixture
def palace_with_associations() -> dict[str, Any]:
    """Return a palace containing searchable associations."""
    return {
        "id": "srch0001",
        "name": "Search Palace",
        "domain": "testing",
        "associations": {
            "entry-1": {
                "label": "Python decorators",
                "explanation": "syntactic sugar for wrapping functions",
            },
            "entry-2": {
                "label": "Rust ownership",
                "explanation": "memory safety without garbage collection",
            },
        },
        "sensory_encoding": {
            "room-a": {"visual": "blue walls", "sound": "quiet hum"},
        },
    }


class TestMatchesQuery:
    """Feature: Query matching logic.

    As a search engine
    I want to match content against queries
    So that relevant entries are surfaced
    """

    @pytest.mark.unit
    def test_semantic_search_finds_substring(self, engine: PalaceSearchEngine) -> None:
        """Scenario: Semantic search with matching term
        Given data containing the word "python"
        When I match with semantic search
        Then the result is True.
        """
        data = {"label": "Python decorators", "detail": "functions"}
        assert engine._matches_query(data, "python", "semantic") is True

    @pytest.mark.unit
    def test_semantic_search_returns_false_for_no_match(
        self, engine: PalaceSearchEngine
    ) -> None:
        """Scenario: Semantic search with non-matching term
        Given data that does not contain the query
        When I match with semantic search
        Then the result is False.
        """
        data = {"label": "Rust ownership"}
        assert engine._matches_query(data, "python", "semantic") is False

    @pytest.mark.unit
    def test_exact_search_requires_full_match(self, engine: PalaceSearchEngine) -> None:
        """Scenario: Exact search requires the query to equal the full serialized data
        Given data serialized to JSON
        When I search for the exact JSON string lowercased
        Then the result is True.
        """
        data = {"x": "y"}
        query = json.dumps(data).lower()
        assert engine._matches_query(data, query, "exact") is True

    @pytest.mark.unit
    def test_fuzzy_search_matches_any_word(self, engine: PalaceSearchEngine) -> None:
        """Scenario: Fuzzy search matches when any query word is present
        Given data containing "ownership"
        When I fuzzy-search for "ownership safety"
        Then the result is True.
        """
        data = {"label": "Rust ownership model"}
        assert engine._matches_query(data, "ownership safety", "fuzzy") is True

    @pytest.mark.unit
    def test_unknown_search_type_returns_false(
        self, engine: PalaceSearchEngine
    ) -> None:
        """Scenario: Unknown search type
        Given valid data
        When I use an unrecognised search type
        Then the result is False.
        """
        data = {"label": "anything"}
        assert engine._matches_query(data, "anything", "unknown_type") is False


class TestSearchInPalace:
    """Feature: In-palace search.

    As a user
    I want to search within a single palace
    So that I get matches with type and location metadata
    """

    @pytest.mark.unit
    def test_search_finds_matching_association(
        self, engine: PalaceSearchEngine, palace_with_associations: dict[str, Any]
    ) -> None:
        """Scenario: Query matches an association entry
        Given a palace with associations
        When I search for "python"
        Then I get an association match.
        """
        matches = engine._search_in_palace(
            palace_with_associations, "python", "semantic"
        )

        assert any(m["type"] == "association" for m in matches)
        assert any("entry-1" in m.get("concept_id", "") for m in matches)

    @pytest.mark.unit
    def test_search_finds_matching_sensory_encoding(
        self, engine: PalaceSearchEngine, palace_with_associations: dict[str, Any]
    ) -> None:
        """Scenario: Query matches a sensory encoding entry
        Given a palace with sensory_encoding
        When I search for "blue"
        Then I get a sensory match.
        """
        matches = engine._search_in_palace(palace_with_associations, "blue", "semantic")

        assert any(m["type"] == "sensory" for m in matches)

    @pytest.mark.unit
    def test_search_returns_empty_for_no_match(
        self, engine: PalaceSearchEngine, palace_with_associations: dict[str, Any]
    ) -> None:
        """Scenario: Query matches nothing
        Given a palace with known contents
        When I search for a term not present anywhere
        Then an empty list is returned.
        """
        matches = engine._search_in_palace(
            palace_with_associations, "xyzzy_not_present", "semantic"
        )
        assert matches == []


class TestSearchPalaces:
    """Feature: Cross-palace search.

    As a user
    I want to search across all palaces
    So that I can find knowledge regardless of which palace holds it
    """

    @pytest.mark.unit
    def test_search_palaces_returns_results_for_matches(
        self,
        mock_repo: MagicMock,
        engine: PalaceSearchEngine,
        palace_with_associations: dict[str, Any],
    ) -> None:
        """Scenario: Search finds matches in one palace
        Given a repository with one palace containing "python"
        When I search for "python"
        Then results include that palace's ID and matches.
        """
        mock_repo.get_master_index.return_value = {
            "palaces": [{"id": palace_with_associations["id"]}]
        }
        mock_repo.load_palace.return_value = palace_with_associations

        results = engine.search_palaces("python", "semantic")

        assert len(results) == 1
        assert results[0]["palace_id"] == palace_with_associations["id"]
        assert len(results[0]["matches"]) >= 1

    @pytest.mark.unit
    def test_search_palaces_excludes_non_matching_palaces(
        self,
        mock_repo: MagicMock,
        engine: PalaceSearchEngine,
        palace_with_associations: dict[str, Any],
    ) -> None:
        """Scenario: Search excludes palaces with no matches
        Given a repository with one palace
        When I search for a term not present in it
        Then results are empty.
        """
        mock_repo.get_master_index.return_value = {
            "palaces": [{"id": palace_with_associations["id"]}]
        }
        mock_repo.load_palace.return_value = palace_with_associations

        results = engine.search_palaces("xyzzy_not_present", "semantic")

        assert results == []

    @pytest.mark.unit
    def test_search_palaces_skips_unloadable_palaces(
        self,
        mock_repo: MagicMock,
        engine: PalaceSearchEngine,
    ) -> None:
        """Scenario: Unloadable palace is silently skipped
        Given a repository index listing a palace whose file is missing
        When I search for any query
        Then no error is raised and results are empty.
        """
        mock_repo.get_master_index.return_value = {"palaces": [{"id": "missing-id"}]}
        mock_repo.load_palace.return_value = None

        results = engine.search_palaces("anything", "semantic")

        assert results == []
