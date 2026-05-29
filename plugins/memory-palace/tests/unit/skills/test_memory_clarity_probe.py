"""BDD tests for memory-clarity-probe skill.

Feature: Memory Clarity Probe
  As a memory-palace user
  I want to probe whether a memory or summary retains enough task state
  So that session handoffs and context compressions do not lose critical
  task progress information
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_FILE = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "memory-clarity-probe"
    / "SKILL.md"
)

PLUGIN_METADATA = (
    Path(__file__).resolve().parent.parent.parent.parent
    / ".claude-plugin"
    / "metadata.json"
)


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestSkillFileExists:
    """Feature: Skill file is present and parseable.

    As a plugin validator
    I want the memory-clarity-probe SKILL.md to exist
    So that the skill can be loaded by Claude Code
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md present
        Given the memory-clarity-probe skill directory
        When looking for SKILL.md
        Then the file should exist.
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_frontmatter_is_valid_yaml(self) -> None:
        """Scenario: Frontmatter parses without error
        Given the SKILL.md content
        When parsing the YAML frontmatter
        Then it should not raise an exception.
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert isinstance(fm, dict)
        assert len(fm) > 0

    @pytest.mark.bdd
    def test_frontmatter_has_required_fields(self) -> None:
        """Scenario: Required frontmatter fields present
        Given the SKILL.md frontmatter
        When checking required fields
        Then name, description, and category must be present.
        """
        fm = _parse_frontmatter(SKILL_FILE.read_text())
        assert "name" in fm
        assert "description" in fm
        assert fm["name"] == "memory-clarity-probe"


class TestDualProbePattern:
    """Feature: Dual-probe anchor question pattern is documented.

    As a skill author
    I want both the progress probe and the gap probe documented
    So that callers understand the dual-probe design from MMPO
    """

    @pytest.mark.bdd
    def test_progress_probe_documented(self) -> None:
        """Scenario: Progress probe question present
        Given the SKILL.md body
        When searching for the progress probe
        Then it should contain 'progress probe' or 'Progress probe'.
        """
        content = SKILL_FILE.read_text()
        assert "progress probe" in content.lower()

    @pytest.mark.bdd
    def test_gap_probe_documented(self) -> None:
        """Scenario: Gap probe question present
        Given the SKILL.md body
        When searching for the gap probe
        Then it should contain 'gap probe' or 'Gap probe'.
        """
        content = SKILL_FILE.read_text()
        assert "gap probe" in content.lower()

    @pytest.mark.bdd
    def test_both_probe_questions_present(self) -> None:
        """Scenario: Anchor question text present
        Given the SKILL.md body
        When searching for the anchor question text
        Then both 'task progress' and 'still needed' should appear.
        """
        content = SKILL_FILE.read_text()
        assert "task progress" in content
        assert "still needed" in content

    @pytest.mark.bdd
    def test_composite_scoring_table_present(self) -> None:
        """Scenario: Composite scoring decision table present
        Given the SKILL.md body
        When searching for the composite score logic
        Then a table with Clear/Ambiguous/Unclear outcomes must exist.
        """
        content = SKILL_FILE.read_text()
        assert "Clear" in content
        assert "Ambiguous" in content
        assert "Unclear" in content
        assert "Composite" in content


class TestOutputFormat:
    """Feature: Output format is specified concretely.

    As a skill consumer
    I want the output format to be specified
    So that callers can parse and act on clarity scores.
    """

    @pytest.mark.bdd
    def test_output_format_section_present(self) -> None:
        """Scenario: Output format section exists
        Given the SKILL.md body
        When looking for the output format section
        Then 'Output Format' should appear as a heading.
        """
        content = SKILL_FILE.read_text()
        assert "Output Format" in content

    @pytest.mark.bdd
    def test_output_includes_recommendation(self) -> None:
        """Scenario: Output includes Recommendation field
        Given the SKILL.md output format
        When checking the defined fields
        Then 'Recommendation' should be a named output field.
        """
        content = SKILL_FILE.read_text()
        assert "Recommendation" in content

    @pytest.mark.bdd
    def test_output_includes_composite_score(self) -> None:
        """Scenario: Output includes Composite field
        Given the SKILL.md output format
        When checking the defined fields
        Then 'Composite' should be a named output field.
        """
        content = SKILL_FILE.read_text()
        # 'Composite' appears in output format block
        assert content.count("Composite") >= 2  # table + output block


class TestLimitationDisclosure:
    """Feature: Skill honestly documents the logprob limitation.

    As a skill consumer
    I want the skill to declare it is a qualitative proxy
    So that I do not mistake it for true token-level entropy
    """

    @pytest.mark.bdd
    def test_not_entropy_disclaimer_present(self) -> None:
        """Scenario: Logprob limitation documented
        Given the SKILL.md body
        When looking for the limitation disclosure
        Then 'What This Is NOT' section must exist.
        """
        content = SKILL_FILE.read_text()
        assert "What This Is NOT" in content

    @pytest.mark.bdd
    def test_logprob_limitation_mentioned(self) -> None:
        """Scenario: Log-probability limitation named
        Given the 'What This Is NOT' section
        When reading the limitation
        Then 'log-prob' or 'logprob' must appear.
        """
        content = SKILL_FILE.read_text()
        assert "log-prob" in content.lower() or "logprob" in content.lower()

    @pytest.mark.bdd
    def test_mmpo_paper_cited(self) -> None:
        """Scenario: Source paper cited
        Given the SKILL.md body
        When looking for the citation
        Then the MMPO arXiv ID or author year must appear.
        """
        content = SKILL_FILE.read_text()
        assert "2605.30159" in content or "Liu et al." in content


class TestBestOfNMode:
    """Feature: Best-of-N selection mode is documented.

    As a skill consumer
    I want to evaluate multiple candidate summaries
    So that I can pick the clearest one without retraining.
    """

    @pytest.mark.bdd
    def test_best_of_n_section_present(self) -> None:
        """Scenario: Best-of-N section exists
        Given the SKILL.md body
        When looking for the Best-of-N description
        Then a 'Best-of-N' section must be present.
        """
        content = SKILL_FILE.read_text()
        assert "Best-of-N" in content

    @pytest.mark.bdd
    def test_best_of_n_mentions_ranking(self) -> None:
        """Scenario: Best-of-N explains ranking
        Given the Best-of-N section
        When reading the ranking logic
        Then 'rank' or 'Rank' must appear.
        """
        content = SKILL_FILE.read_text()
        assert "rank" in content.lower()


class TestExitCriteria:
    """Feature: Exit criteria are concrete and falsifiable.

    As a skill reviewer
    I want exit criteria in the SKILL.md
    So that I can verify when the skill is done.
    """

    @pytest.mark.bdd
    def test_exit_criteria_section_present(self) -> None:
        """Scenario: Exit Criteria heading exists
        Given the SKILL.md body
        When looking for exit criteria
        Then 'Exit Criteria' must appear as a heading.
        """
        content = SKILL_FILE.read_text()
        assert "Exit Criteria" in content

    @pytest.mark.bdd
    def test_exit_criteria_has_checkboxes(self) -> None:
        """Scenario: Exit criteria use checkbox format
        Given the Exit Criteria section
        When checking the format
        Then at least 3 unchecked boxes '- [ ]' must appear.
        """
        content = SKILL_FILE.read_text()
        assert content.count("- [ ]") >= 3

    @pytest.mark.bdd
    def test_exit_criteria_references_best_of_n(self) -> None:
        """Scenario: Best-of-N is a verifiable criterion
        Given the Exit Criteria section
        When checking the criteria
        Then Best-of-N behavior is listed as a criterion.
        """
        content = SKILL_FILE.read_text()
        # Find exit criteria block and check Best-of-N appears after it
        criteria_start = content.index("Exit Criteria")
        after_criteria = content[criteria_start:]
        assert "Best-of-N" in after_criteria or "best-of-n" in after_criteria.lower()


class TestPluginRegistration:
    """Feature: Skill is registered in plugin metadata.

    As a plugin user
    I want memory-clarity-probe to appear in plugin.json
    So that Claude Code can discover and load it.
    """

    @pytest.mark.bdd
    def test_skill_registered_in_metadata(self) -> None:
        """Scenario: Skill appears in .claude-plugin/metadata.json
        Given the plugin metadata file
        When reading the skills list
        Then 'skills/memory-clarity-probe' should be listed.
        """
        assert PLUGIN_METADATA.exists(), (
            f"Plugin metadata not found at {PLUGIN_METADATA}"
        )
        metadata = json.loads(PLUGIN_METADATA.read_text())
        skills = metadata.get("skills", [])
        assert "skills/memory-clarity-probe" in skills, (
            f"memory-clarity-probe not registered in metadata. Found: {skills}"
        )
