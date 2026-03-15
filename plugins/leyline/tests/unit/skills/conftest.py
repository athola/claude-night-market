"""Shared fixtures for leyline unit skill tests.

Provides path and content fixtures for the testing-quality-standards
skill, eliminating duplication across test classes.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def quality_standards_path() -> Path:
    """Path to the testing-quality-standards skill."""
    return (
        Path(__file__).parents[3] / "skills" / "testing-quality-standards" / "SKILL.md"
    )


@pytest.fixture
def quality_standards_content(quality_standards_path: Path) -> str:
    """Load the testing-quality-standards skill content."""
    return quality_standards_path.read_text()
