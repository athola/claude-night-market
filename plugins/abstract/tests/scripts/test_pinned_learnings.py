"""Tests for pinned learnings preservation across LEARNINGS.md regeneration.

Tests follow Given-When-Then pattern for:
1. Extracting pinned sections from existing content
2. Preserving pinned sections during regeneration
3. Handling edge cases (no pinned section, pinned at EOF)
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from aggregate_skill_logs import (
    AggregationResult,
    extract_pinned_section,
    generate_learnings_md,
)

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

LEARNINGS_WITH_PINNED = """\
# Skill Performance Learnings

**Last Updated**: 2026-03-01 04:30:00 UTC
**Analysis Period**: Last 30 days
**Skills Analyzed**: 10
**Total Executions**: 200

---

## Pinned Learnings

- Hook import chains must be 3.9-compatible (system Python)
- Never use `datetime.UTC`; use `datetime.timezone.utc`

## High-Impact Issues

Skills with significant problems requiring immediate attention.

### imbue:proof-of-work
**Type**: high_failure_rate
"""

LEARNINGS_WITHOUT_PINNED = """\
# Skill Performance Learnings

**Last Updated**: 2026-03-01 04:30:00 UTC
**Analysis Period**: Last 30 days

---

## High-Impact Issues

Skills with significant problems requiring immediate attention.
"""

LEARNINGS_PINNED_AT_END = """\
# Skill Performance Learnings

**Last Updated**: 2026-03-01 04:30:00 UTC

---

## High-Impact Issues

Some issues here.

## Pinned Learnings

- Architecture decision: plugins never import from sibling plugins
- The LEARNINGS.md 30-day window loses critical context
"""


def _make_empty_result() -> AggregationResult:
    """Build a minimal AggregationResult for testing."""
    return AggregationResult(
        timestamp=datetime(2026, 3, 4, 12, 0, 0, tzinfo=timezone.utc),
        skills_analyzed=0,
        total_executions=0,
        high_impact_issues=[],
        slow_skills=[],
        low_rated_skills=[],
        metrics_by_skill={},
    )


# ---------------------------------------------------------------------------
# extract_pinned_section tests
# ---------------------------------------------------------------------------


class TestExtractPinnedSection:
    """Test extraction of pinned learnings from LEARNINGS.md content."""

    def test_extract_pinned_section(self) -> None:
        """Given: LEARNINGS.md content with a Pinned Learnings section
        When: extract_pinned_section() is called
        Then: Returns the section body without the header
        """
        result = extract_pinned_section(LEARNINGS_WITH_PINNED)

        assert "Hook import chains must be 3.9-compatible" in result
        assert "Never use `datetime.UTC`" in result
        # Should not include the header itself
        assert "## Pinned Learnings" not in result
        # Should not include content from the next section
        assert "High-Impact Issues" not in result

    def test_extract_pinned_section_empty(self) -> None:
        """Given: LEARNINGS.md content without a Pinned Learnings section
        When: extract_pinned_section() is called
        Then: Returns empty string
        """
        result = extract_pinned_section(LEARNINGS_WITHOUT_PINNED)

        assert result == ""

    def test_extract_pinned_section_at_end(self) -> None:
        """Given: LEARNINGS.md where Pinned Learnings is the last section
        When: extract_pinned_section() is called
        Then: Returns the section body up to end of file
        """
        result = extract_pinned_section(LEARNINGS_PINNED_AT_END)

        assert "plugins never import from sibling plugins" in result
        assert "30-day window loses critical context" in result
        # Should not include the header
        assert "## Pinned Learnings" not in result


# ---------------------------------------------------------------------------
# generate_learnings_md preserves pinned section
# ---------------------------------------------------------------------------


class TestGeneratePreservesPinned:
    """Test that generate_learnings_md includes pinned content."""

    def test_generate_preserves_pinned(self) -> None:
        """Given: An AggregationResult and existing pinned content
        When: generate_learnings_md() is called with existing_pinned
        Then: Output includes the Pinned Learnings section
        """
        result = _make_empty_result()
        pinned = (
            "- Hook import chains must be 3.9-compatible\n- Never use `datetime.UTC`"
        )

        md = generate_learnings_md(result, existing_pinned=pinned)

        assert "## Pinned Learnings" in md
        assert "Hook import chains must be 3.9-compatible" in md
        assert "Never use `datetime.UTC`" in md

    def test_generate_omits_pinned_when_empty(self) -> None:
        """Given: An AggregationResult with no existing pinned content
        When: generate_learnings_md() is called without existing_pinned
        Then: Output does NOT include a Pinned Learnings header
        """
        result = _make_empty_result()

        md = generate_learnings_md(result)

        assert "## Pinned Learnings" not in md
