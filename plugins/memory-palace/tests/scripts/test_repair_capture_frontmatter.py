"""Tests for the capture-frontmatter repair.

Feature: captures corrupted by unescaped quoting become readable again
  The writers now escape their scalars, but that fix is forward-only.
  Captures already on disk stay invisible to every reader until their
  frontmatter is re-quoted, and they are fetched web content, so there
  is no way to regenerate them.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from repair_capture_frontmatter import (
    repair_text,  # noqa: E402 - needs the sys.path insert above
)

CORRUPT = (
    "---\n"
    "queue_entry_id: 2026-08-13_14-59-27_b3c8452e\n"
    'topic: "Search Results for "mtime staleness""\n'
    "status: pending_review\n"
    'url: "https://lobste.rs/search?q=mtime"\n'
    "---\n"
    "\n"
    "# Search Results\n"
    "\n"
    "Body prose that must survive untouched.\n"
)


class TestRepair:
    """Feature: re-quote the scalar without touching anything else."""

    def test_corrupt_frontmatter_becomes_parseable(self) -> None:
        """Scenario: the entry a reader could not load now loads."""
        repaired = repair_text(CORRUPT)

        assert repaired is not None
        metadata = yaml.safe_load(repaired.split("\n---\n")[0].lstrip("-\n"))
        assert metadata["status"] == "pending_review"

    def test_topic_text_is_preserved_including_its_quotes(self) -> None:
        """Scenario: repair re-quotes, it does not discard content."""
        repaired = repair_text(CORRUPT)

        assert repaired is not None
        metadata = yaml.safe_load(repaired.split("\n---\n")[0].lstrip("-\n"))
        assert metadata["topic"] == 'Search Results for "mtime staleness"'

    def test_body_survives_byte_for_byte(self) -> None:
        """Scenario: the captured content is the thing worth keeping."""
        repaired = repair_text(CORRUPT)

        assert repaired is not None
        assert repaired.endswith(
            "\n# Search Results\n\nBody prose that must survive untouched.\n"
        )

    def test_other_frontmatter_lines_are_untouched(self) -> None:
        """Scenario: only the broken scalar is rewritten."""
        repaired = repair_text(CORRUPT)

        assert repaired is not None
        assert "queue_entry_id: 2026-08-13_14-59-27_b3c8452e" in repaired


class TestRefusals:
    """Feature: a repair that cannot be verified is not made."""

    def test_already_valid_entry_is_left_alone(self) -> None:
        """Scenario: idempotence, so a second pass is a no-op."""
        valid = '---\ntopic: "Plain title"\n---\n\n# Body\n'

        assert repair_text(valid) is None

    def test_entry_without_frontmatter_is_left_alone(self) -> None:
        """Scenario: nothing to repair is not the same as a failure."""
        assert repair_text("# Just a heading\n\nprose\n") is None

    def test_unrepairable_entry_is_refused_rather_than_mangled(self) -> None:
        """Scenario: corruption this pass does not model is not guessed at.

        Writing a file we cannot re-parse would turn an invisible capture
        into a wrong one.
        """
        hopeless = "---\ntopic: [unclosed\n  bracket: {\n---\n\n# Body\n"

        assert repair_text(hopeless) is None
