"""Tests for the generate_trust_badges script.

Feature: Trust Badge Generation from ERC-8004 Reputation Data

    As a plugin maintainer
    I want trust badges in my README
    So that consumers can see verification status at a glance
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from generate_trust_badges import (  # noqa: E402, I001
    BadgeData,
    badge_color,
    generate_badge_markdown,
    generate_badge_url,
    generate_badges_for_plugin,
    update_plugin_readme,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_badge_data(
    l1_rate: float = 1.0,
    l2_rate: float = 0.0,
    l3_rate: float = 0.0,
) -> BadgeData:
    """Create a BadgeData with given pass rates."""
    return BadgeData(
        plugin_name="test-plugin",
        l1_rate=l1_rate,
        l2_rate=l2_rate,
        l3_rate=l3_rate,
    )


# ---------------------------------------------------------------------------
# Badge color selection
# ---------------------------------------------------------------------------


class TestBadgeColor:
    """Feature: Color selection based on trust score.

    As a badge consumer
    I want color-coded badges
    So that trust levels are visually obvious.
    """

    @pytest.mark.unit
    def test_high_score_is_green(self) -> None:
        """Scenario: Score above 90% is green.

        Given a pass rate of 0.95
        When selecting badge color
        Then color is "brightgreen".
        """
        assert badge_color(0.95) == "brightgreen"

    @pytest.mark.unit
    def test_score_at_90_is_green(self) -> None:
        """Scenario: Score exactly at 90% threshold.

        Given a pass rate of 0.90
        When selecting badge color
        Then color is "brightgreen".
        """
        assert badge_color(0.90) == "brightgreen"

    @pytest.mark.unit
    def test_moderate_score_is_yellow(self) -> None:
        """Scenario: Score between 70% and 90% is yellow.

        Given a pass rate of 0.80
        When selecting badge color
        Then color is "yellow".
        """
        assert badge_color(0.80) == "yellow"

    @pytest.mark.unit
    def test_score_at_70_is_yellow(self) -> None:
        """Scenario: Score exactly at 70% threshold.

        Given a pass rate of 0.70
        When selecting badge color
        Then color is "yellow".
        """
        assert badge_color(0.70) == "yellow"

    @pytest.mark.unit
    def test_low_score_is_red(self) -> None:
        """Scenario: Score below 70% is red.

        Given a pass rate of 0.50
        When selecting badge color
        Then color is "red".
        """
        assert badge_color(0.50) == "red"

    @pytest.mark.unit
    def test_zero_score_is_red(self) -> None:
        """Scenario: Zero pass rate is red.

        Given a pass rate of 0.0
        When selecting badge color
        Then color is "red".
        """
        assert badge_color(0.0) == "red"

    @pytest.mark.unit
    def test_perfect_score_is_green(self) -> None:
        """Scenario: Perfect 100% is green.

        Given a pass rate of 1.0
        When selecting badge color
        Then color is "brightgreen".
        """
        assert badge_color(1.0) == "brightgreen"


# ---------------------------------------------------------------------------
# Badge URL generation
# ---------------------------------------------------------------------------


class TestGenerateBadgeUrl:
    """Feature: Shields.io-compatible badge URL generation.

    As a badge consumer
    I want valid shields.io URLs
    So that badges render correctly in markdown.
    """

    @pytest.mark.unit
    def test_url_contains_shields_io(self) -> None:
        """Scenario: URL points to shields.io.

        Given badge data for a plugin
        When generating badge URL
        Then URL starts with https://img.shields.io/badge/.
        """
        data = _make_badge_data(l1_rate=0.98)
        url = generate_badge_url(data)
        assert url.startswith("https://img.shields.io/badge/")

    @pytest.mark.unit
    def test_url_contains_trust_label(self) -> None:
        """Scenario: URL includes "trust" label.

        Given badge data
        When generating badge URL
        Then URL contains the "trust" label.
        """
        data = _make_badge_data(l1_rate=0.98)
        url = generate_badge_url(data)
        assert "trust" in url.lower()

    @pytest.mark.unit
    def test_url_contains_percentages(self) -> None:
        """Scenario: URL includes pass rate percentages.

        Given L1 rate of 98%
        When generating badge URL
        Then URL contains "98%25" (URL-encoded %).
        """
        data = _make_badge_data(l1_rate=0.98)
        url = generate_badge_url(data)
        assert "98" in url

    @pytest.mark.unit
    def test_high_score_url_has_green(self) -> None:
        """Scenario: High-scoring plugin gets green badge URL.

        Given L1 rate of 95%
        When generating badge URL
        Then URL contains "brightgreen".
        """
        data = _make_badge_data(l1_rate=0.95)
        url = generate_badge_url(data)
        assert "brightgreen" in url

    @pytest.mark.unit
    def test_low_score_url_has_red(self) -> None:
        """Scenario: Low-scoring plugin gets red badge URL.

        Given L1 rate of 40%
        When generating badge URL
        Then URL contains "red".
        """
        data = _make_badge_data(l1_rate=0.40)
        url = generate_badge_url(data)
        assert "red" in url

    @pytest.mark.unit
    def test_multi_level_url(self) -> None:
        """Scenario: Multiple levels appear in badge message.

        Given rates at all three levels
        When generating badge URL
        Then URL contains L1, L2, and L3 data.
        """
        data = _make_badge_data(l1_rate=0.98, l2_rate=0.95, l3_rate=0.90)
        url = generate_badge_url(data)
        assert "L1" in url
        assert "L2" in url
        assert "L3" in url


# ---------------------------------------------------------------------------
# Markdown snippet generation
# ---------------------------------------------------------------------------


class TestGenerateBadgeMarkdown:
    """Feature: Markdown badge snippet generation.

    As a plugin maintainer
    I want ready-to-paste markdown
    So that I can add badges to my README easily.
    """

    @pytest.mark.unit
    def test_markdown_contains_image_syntax(self) -> None:
        """Scenario: Output is valid markdown image.

        Given badge data
        When generating markdown
        Then output contains markdown image syntax ![...].
        """
        data = _make_badge_data(l1_rate=0.95)
        md = generate_badge_markdown(data)
        assert md.startswith("![")
        assert "](https://img.shields.io/badge/" in md

    @pytest.mark.unit
    def test_markdown_contains_plugin_name(self) -> None:
        """Scenario: Plugin name in alt text.

        Given badge data for "test-plugin"
        When generating markdown
        Then alt text contains the plugin name.
        """
        data = _make_badge_data(l1_rate=0.95)
        md = generate_badge_markdown(data)
        assert "test-plugin" in md

    @pytest.mark.unit
    def test_markdown_is_single_line(self) -> None:
        """Scenario: Badge markdown fits on one line.

        Given badge data
        When generating markdown
        Then output is a single line (no newlines).
        """
        data = _make_badge_data(l1_rate=0.95)
        md = generate_badge_markdown(data)
        assert "\n" not in md


# ---------------------------------------------------------------------------
# Badge generation from verification result
# ---------------------------------------------------------------------------


class TestGenerateBadgesForPlugin:
    """Feature: End-to-end badge generation from a plugin name.

    As the badge generation pipeline
    I want to go from plugin name to badge data
    So that the process is automated.
    """

    @pytest.mark.unit
    def test_generates_badge_from_scores(self) -> None:
        """Scenario: Scores produce valid badge data.

        Given a mock verify result with known pass rates
        When generating badges
        Then BadgeData reflects the scores.
        """
        verify_result = {
            "plugin_name": "sanctum",
            "recommendation": "trusted",
            "meets_threshold": True,
            "level_scores": [
                {"level": "L1", "total": 100, "passed": 98, "rate": 0.98},
                {"level": "L2", "total": 50, "passed": 47, "rate": 0.94},
                {"level": "L3", "total": 20, "passed": 18, "rate": 0.90},
            ],
            "assertion_history": [],
            "error": None,
        }

        badge = generate_badges_for_plugin(verify_result)

        assert badge.plugin_name == "sanctum"
        assert badge.l1_rate == pytest.approx(0.98)
        assert badge.l2_rate == pytest.approx(0.94)
        assert badge.l3_rate == pytest.approx(0.90)

    @pytest.mark.unit
    def test_missing_levels_default_to_zero(self) -> None:
        """Scenario: Partial level data fills zeros.

        Given a result with only L1 scores
        When generating badges
        Then L2 and L3 rates default to 0.0.
        """
        verify_result = {
            "plugin_name": "minimal",
            "recommendation": "trusted",
            "meets_threshold": True,
            "level_scores": [
                {"level": "L1", "total": 10, "passed": 10, "rate": 1.0},
            ],
            "assertion_history": [],
            "error": None,
        }

        badge = generate_badges_for_plugin(verify_result)

        assert badge.l1_rate == 1.0
        assert badge.l2_rate == 0.0
        assert badge.l3_rate == 0.0

    @pytest.mark.unit
    def test_empty_scores_all_zero(self) -> None:
        """Scenario: No scores at all.

        Given a result with empty level_scores
        When generating badges
        Then all rates are 0.0.
        """
        verify_result = {
            "plugin_name": "unknown",
            "recommendation": "untrusted",
            "meets_threshold": False,
            "level_scores": [],
            "assertion_history": [],
            "error": "No history",
        }

        badge = generate_badges_for_plugin(verify_result)

        assert badge.l1_rate == 0.0
        assert badge.l2_rate == 0.0
        assert badge.l3_rate == 0.0


# ---------------------------------------------------------------------------
# README badge insertion
# ---------------------------------------------------------------------------


class TestUpdatePluginReadme:
    """Feature: Insert or update trust badges in plugin READMEs.

    As a plugin maintainer
    I want badges auto-inserted in my README
    So that trust data stays current without manual edits.
    """

    @pytest.mark.unit
    def test_inserts_badge_after_title(self, tmp_path: Path) -> None:
        """Scenario: README with title but no existing badge.

        Given a README with "# My Plugin" header
        When updating with a trust badge
        Then badge appears after the title.
        """
        readme = tmp_path / "README.md"
        readme.write_text("# My Plugin\n\nSome description.\n")

        badge_md = "![trust](https://img.shields.io/badge/trust-L1%3A98%25-brightgreen)"
        modified = update_plugin_readme(readme, badge_md)

        assert modified is True
        content = readme.read_text()
        assert badge_md in content
        assert content.index("# My Plugin") < content.index(badge_md)

    @pytest.mark.unit
    def test_replaces_existing_badge(self, tmp_path: Path) -> None:
        """Scenario: README already has a trust badge.

        Given a README with an existing trust badge
        When updating with a new badge
        Then the old badge is replaced.
        """
        old_badge = "![trust](https://img.shields.io/badge/trust-L1%3A80%25-yellow)"
        new_badge = (
            "![trust](https://img.shields.io/badge/trust-L1%3A98%25-brightgreen)"
        )
        readme = tmp_path / "README.md"
        readme.write_text(f"# Plugin\n\n{old_badge}\n\nDescription.\n")

        modified = update_plugin_readme(readme, new_badge)

        assert modified is True
        content = readme.read_text()
        assert new_badge in content
        assert old_badge not in content

    @pytest.mark.unit
    def test_no_change_when_badge_identical(self, tmp_path: Path) -> None:
        """Scenario: Badge already up to date.

        Given a README with the exact same badge
        When updating with identical badge
        Then file is not modified.
        """
        badge_md = "![trust](https://img.shields.io/badge/trust-L1%3A98%25-brightgreen)"
        readme = tmp_path / "README.md"
        readme.write_text(f"# Plugin\n\n{badge_md}\n\nDescription.\n")

        modified = update_plugin_readme(readme, badge_md)

        assert modified is False

    @pytest.mark.unit
    def test_nonexistent_readme_returns_false(self, tmp_path: Path) -> None:
        """Scenario: README file does not exist.

        Given a path to a nonexistent README
        When attempting to update
        Then returns False without error.
        """
        readme = tmp_path / "nonexistent" / "README.md"
        modified = update_plugin_readme(readme, "![trust](url)")

        assert modified is False

    @pytest.mark.unit
    def test_empty_readme_inserts_badge(self, tmp_path: Path) -> None:
        """Scenario: Empty README gets badge.

        Given an empty README file
        When updating with a badge
        Then badge is inserted at the top.
        """
        readme = tmp_path / "README.md"
        readme.write_text("")

        badge_md = (
            "![trust](https://img.shields.io/badge/trust-L1%3A100%25-brightgreen)"
        )
        modified = update_plugin_readme(readme, badge_md)

        assert modified is True
        content = readme.read_text()
        assert badge_md in content
