"""Pytest configuration and shared fixtures for Memory Palace tests.

Provides reusable test fixtures for:
- Temporary palace directories with isolated storage
- Sample palace data structures
- Digital garden test files
- Configuration fixtures
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from memory_palace.palace_manager import MemoryPalaceManager


@pytest.fixture
def temp_palaces_dir(tmp_path: Path) -> Path:
    """Create an isolated temporary directory for palace storage.

    Creates the main palaces directory and a backups subdirectory,
    mimicking the real storage structure.
    """
    palaces_dir = tmp_path / "palaces"
    palaces_dir.mkdir()
    (palaces_dir / "backups").mkdir()
    return palaces_dir


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Path:
    """Create a temporary configuration file with default settings."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "settings.json"
    config_file.write_text(
        json.dumps(
            {
                "storage": {"palace_directory": str(tmp_path / "palaces")},
                "defaults": {"metaphor": "building"},
            },
            indent=2,
        ),
    )
    return config_file


@pytest.fixture
def sample_palace_data() -> dict[str, Any]:
    """Return a sample palace data structure for testing."""
    return {
        "id": "test1234",
        "name": "Test Palace",
        "domain": "testing",
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
            "concept1": {"label": "Test Concept", "location": "room1"},
            "concept2": {"label": "Another Concept", "location": "room2"},
        },
        "sensory_encoding": {
            "room1": {"visual": "blue walls", "auditory": "quiet hum"},
        },
        "metadata": {
            "concept_count": 2,
            "complexity_level": "basic",
            "access_patterns": [],
        },
    }


@pytest.fixture
def sample_palace_file(temp_palaces_dir: Path, sample_palace_data: dict) -> Path:
    """Create a sample palace JSON file in the temporary directory."""
    palace_file = temp_palaces_dir / f"{sample_palace_data['id']}.json"
    palace_file.write_text(json.dumps(sample_palace_data, indent=2))
    return palace_file


@pytest.fixture
def sample_garden_data() -> dict[str, Any]:
    """Return sample digital garden data for testing."""
    now = datetime.now(UTC)
    return {
        "garden": {
            "plots": [
                {
                    "name": "fresh-plot",
                    "inbound_links": ["a", "b"],
                    "outbound_links": ["c", "d", "e"],
                    "last_tended": now.isoformat(),
                },
                {
                    "name": "week-old-plot",
                    "inbound_links": ["x"],
                    "outbound_links": ["y", "z"],
                    "last_tended": "2025-11-25T12:00:00+00:00",
                },
                {
                    "name": "orphan-plot",
                    "inbound_links": [],
                    "outbound_links": [],
                    "last_tended": "2025-10-01T00:00:00+00:00",
                },
            ],
        },
    }


@pytest.fixture
def sample_garden_file(tmp_path: Path, sample_garden_data: dict) -> Path:
    """Create a sample garden JSON file for testing."""
    garden_file = tmp_path / "garden.json"
    garden_file.write_text(json.dumps(sample_garden_data, indent=2))
    return garden_file


@pytest.fixture
def empty_garden_file(tmp_path: Path) -> Path:
    """Create an empty garden JSON file (no plots)."""
    garden_file = tmp_path / "empty_garden.json"
    garden_file.write_text(json.dumps({"garden": {"plots": []}}, indent=2))
    return garden_file


@pytest.fixture
def fixed_timestamp() -> datetime:
    """Provide a fixed timestamp for reproducible tests."""
    return datetime(2025, 12, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def multiple_palaces(
    temp_palaces_dir: Path, temp_config_file: Path
) -> list[dict[str, Any]]:
    """Create multiple palace files for testing search and index operations.

    Also builds the master index so tests can query it immediately.
    """
    palaces = [
        {
            "id": "palace01",
            "name": "Python Palace",
            "domain": "programming",
            "metaphor": "library",
            "created": "2025-01-01T00:00:00",
            "last_modified": "2025-01-15T00:00:00",
            "layout": {
                "districts": [],
                "buildings": [],
                "rooms": [],
                "connections": [],
            },
            "associations": {
                "decorators": {
                    "label": "Python Decorators",
                    "explanation": "syntactic sugar",
                },
            },
            "sensory_encoding": {},
            "metadata": {
                "concept_count": 1,
                "complexity_level": "intermediate",
                "access_patterns": [],
            },
        },
        {
            "id": "palace02",
            "name": "Rust Fortress",
            "domain": "programming",
            "metaphor": "fortress",
            "created": "2025-02-01T00:00:00",
            "last_modified": "2025-02-10T00:00:00",
            "layout": {
                "districts": [],
                "buildings": [],
                "rooms": [],
                "connections": [],
            },
            "associations": {
                "ownership": {
                    "label": "Rust Ownership",
                    "explanation": "memory safety",
                },
                "borrowing": {"label": "Borrowing Rules", "explanation": "references"},
            },
            "sensory_encoding": {},
            "metadata": {
                "concept_count": 2,
                "complexity_level": "advanced",
                "access_patterns": [],
            },
        },
        {
            "id": "palace03",
            "name": "Math Manor",
            "domain": "mathematics",
            "metaphor": "manor",
            "created": "2025-03-01T00:00:00",
            "last_modified": "2025-03-05T00:00:00",
            "layout": {
                "districts": [],
                "buildings": [],
                "rooms": [],
                "connections": [],
            },
            "associations": {
                "calculus": {
                    "label": "Calculus",
                    "explanation": "derivatives and integrals",
                },
            },
            "sensory_encoding": {},
            "metadata": {
                "concept_count": 1,
                "complexity_level": "basic",
                "access_patterns": [],
            },
        },
    ]

    for palace in palaces:
        palace_file = temp_palaces_dir / f"{palace['id']}.json"
        palace_file.write_text(json.dumps(palace, indent=2))

    # Build the master index so tests can query it
    manager = MemoryPalaceManager(
        config_path=str(temp_config_file),
        palaces_dir_override=str(temp_palaces_dir),
    )
    manager.update_master_index()

    return palaces
