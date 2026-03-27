"""Palace search operations: search_palaces, _search_in_palace, _matches_query."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from memory_palace.palace_repository import PalaceRepository


class PalaceSearchEngine:
    """Search across memory palaces using keyword, exact, or fuzzy matching."""

    def __init__(self, repository: PalaceRepository) -> None:
        """Initialize the search engine with a palace repository.

        Args:
            repository: A PalaceRepository instance used to load palace data.

        """
        self._repo = repository

    def search_palaces(
        self, query: str, search_type: str = "semantic"
    ) -> list[dict[str, Any]]:
        """Search across all memory palaces.

        Args:
            query: The search query.
            search_type: The type of search to perform.

        Returns:
            A list of search results, one entry per matching palace.

        """
        results = []
        query_lower = query.lower()

        for palace_summary in self._repo.get_master_index()["palaces"]:
            palace = self._repo.load_palace(palace_summary["id"])
            if palace:
                matches = self._search_in_palace(palace, query_lower, search_type)
                if matches:
                    results.append(
                        {
                            "palace_id": palace["id"],
                            "palace_name": palace["name"],
                            "matches": matches,
                        }
                    )

        return results

    def _search_in_palace(
        self,
        palace: dict[str, Any],
        query: str,
        search_type: str,
    ) -> list[dict[str, Any]]:
        """Search for a query within a single palace.

        Args:
            palace: The palace to search in.
            query: The search query (already lowercased).
            search_type: The type of search to perform.

        Returns:
            A list of matches found in the palace.

        """
        matches = []

        for concept_id, association in palace.get("associations", {}).items():
            if self._matches_query(association, query, search_type):
                matches.append(
                    {
                        "type": "association",
                        "concept_id": concept_id,
                        "data": association,
                    }
                )

        for location_id, sensory_data in palace.get("sensory_encoding", {}).items():
            if self._matches_query(sensory_data, query, search_type):
                matches.append(
                    {
                        "type": "sensory",
                        "location_id": location_id,
                        "data": sensory_data,
                    }
                )

        return matches

    def _matches_query(
        self, data: dict[str, Any], query: str, search_type: str
    ) -> bool:
        """Check whether *data* matches *query* under *search_type*.

        Args:
            data: The data to check.
            query: The search query (lowercased).
            search_type: One of "semantic", "exact", or "fuzzy".

        Returns:
            True if the data matches the query, False otherwise.

        """
        if search_type == "semantic":
            return query in json.dumps(data).lower()
        if search_type == "exact":
            return query == json.dumps(data).lower()
        if search_type == "fuzzy":
            text_content = json.dumps(data).lower()
            return any(word in text_content for word in query.split())

        return False
