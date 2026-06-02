"""Invariant tests for fix-pr Step 5 validate strategy table.

Step 5.4 of `/fix-pr` documents how the agent verifies reviewer-written
manual test plan items. The strategy table and tier-selection guide
encode three load-bearing decisions:

1. Sub-section ordering 5.4.1 -> 5.4.5 (a prior reorder bug
   placed 5.4.5 between 5.4.2 and 5.4.3; this guards the fix)
2. Verification surface covers shell, HTTP, browser/CDP, Playwright,
   and Computer Use as last resort
3. Browser tier order is Tier 1 = MCP CDP, Tier 2 = Playwright,
   Tier 3 = Computer Use. Reordering changes the default cost
   profile and would push agents to spawn Playwright instances
   for single-DOM-assertion items.

These tests are regression guards. If one fails, do NOT silently
update the assertion: the failure indicates a conscious decision
to change the documented strategy, which deserves human review.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

VALIDATE_FILE = (
    Path(__file__).parents[1]
    / "commands"
    / "fix-pr-modules"
    / "steps"
    / "5-validate.md"
)


@pytest.fixture(scope="module")
def validate_md() -> str:
    return VALIDATE_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def section_5_4_subheadings(validate_md: str) -> list[str]:
    """All ### sub-headings under Section 5.4 in document order."""
    return re.findall(r"^### (5\.4\.\d+ [^\n]+)$", validate_md, re.MULTILINE)


class TestSectionOrdering:
    """Section 5.4 sub-headings appear in numeric order 5.4.1 -> 5.4.5."""

    @pytest.mark.unit
    def test_validate_file_exists(self) -> None:
        assert VALIDATE_FILE.exists(), f"missing {VALIDATE_FILE}"

    @pytest.mark.unit
    def test_all_five_subsections_present(
        self, section_5_4_subheadings: list[str]
    ) -> None:
        """5.4.1 through 5.4.5 are all defined."""
        numbers = [s.split()[0] for s in section_5_4_subheadings]
        for expected in ("5.4.1", "5.4.2", "5.4.3", "5.4.4", "5.4.5"):
            assert expected in numbers, (
                f"Section {expected} missing from validate.md sub-headings: "
                f"{section_5_4_subheadings}"
            )

    @pytest.mark.unit
    def test_subsections_in_numeric_order(
        self, section_5_4_subheadings: list[str]
    ) -> None:
        """A regression guard: a prior edit placed 5.4.5 between 5.4.2 and 5.4.3.

        If this test fails, someone re-introduced the ordering bug.
        Do NOT silently reorder; reading flow assumes 5.4.5 (tier
        selection) follows 5.4.4 (results documentation).
        """
        numbers = [s.split()[0] for s in section_5_4_subheadings]
        assert numbers == sorted(numbers), (
            f"5.4.x sub-sections out of order: {numbers}. "
            "Tier-selection (5.4.5) must follow results doc (5.4.4)."
        )


class TestStrategyCoverage:
    """5.4.2 strategy table covers the required verification surfaces."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("required_keyword", "rationale"),
        [
            ("pytest", "shell test execution"),
            ("curl", "HTTP/API endpoint probing"),
            ("use_browser", "DOM/UI verification via MCP CDP tool"),
            ("playwright", "multi-step browser flows"),
            ("computer-control", "desktop GUI as last resort"),
        ],
    )
    def test_strategy_keyword_present(
        self, validate_md: str, required_keyword: str, rationale: str
    ) -> None:
        """Each verification surface must be discoverable by keyword search.

        If this fails, the strategy table no longer documents
        '{rationale}'. Adding new surfaces is fine; removing one
        means agents fall back to LOW-confidence prose for that
        category of test item.
        """
        assert required_keyword.lower() in validate_md.lower(), (
            f"5-validate.md no longer mentions '{required_keyword}' "
            f"({rationale}). Strategy coverage regression."
        )


class TestBrowserTierOrder:
    """5.4.5 documents three browser tiers in cost-ascending order.

    Tier 1 (MCP CDP) is the lightweight default. Tier 2 (Playwright)
    spawns a browser per spec. Tier 3 (Computer Use) is the heavy
    fallback. Reordering would change the default tool agents reach
    for and break the cost-conscious design.
    """

    @pytest.fixture
    def tier_section(self, validate_md: str) -> str:
        """Body of section 5.4.5 (everything after the heading until next ##)."""
        match = re.search(
            r"### 5\.4\.5[^\n]*\n(.*?)(?=^###? |\Z)",
            validate_md,
            re.DOTALL | re.MULTILINE,
        )
        assert match, "Section 5.4.5 not found"
        return match.group(1)

    @pytest.mark.unit
    def test_three_tiers_in_table(self, tier_section: str) -> None:
        """The tier table has rows for tiers 1, 2, and 3 in that order."""
        tier_rows = re.findall(r"^\|\s*([1-3])\s*\|", tier_section, re.MULTILINE)
        assert tier_rows == ["1", "2", "3"], (
            f"Browser tier rows out of order or missing: {tier_rows}. "
            "Expected ['1','2','3'] (CDP, Playwright, Computer Use)."
        )

    @pytest.mark.unit
    def test_tier_1_is_cdp_mcp_tool(self, tier_section: str) -> None:
        """Tier 1 row references the MCP CDP browser tool by exact name.

        The MCP tool name is part of the agent's invocable surface.
        If this name drifts, agents will try to call a non-existent
        tool. The tool comes from the superpowers-chrome plugin.
        """
        tier_1_match = re.search(r"^\|\s*1\s*\|([^|]+)\|", tier_section, re.MULTILINE)
        assert tier_1_match, "Tier 1 row not found"
        tier_1_cell = tier_1_match.group(1)
        assert "mcp__plugin_superpowers-chrome_chrome__use_browser" in tier_1_cell, (
            f"Tier 1 no longer references the MCP CDP tool by exact name. "
            f"Cell content: {tier_1_cell.strip()!r}"
        )

    @pytest.mark.unit
    def test_default_tier_is_one(self, tier_section: str) -> None:
        """The 'Default to Tier 1' guidance must remain.

        Without this guidance, agents may pick the heaviest tool
        they can reach (Playwright or Computer Use) for trivial
        DOM checks, burning tokens and sandbox setup time.
        """
        assert re.search(r"\*\*Default to Tier 1[.\*]", tier_section), (
            "5.4.5 no longer instructs agents to default to Tier 1."
        )
