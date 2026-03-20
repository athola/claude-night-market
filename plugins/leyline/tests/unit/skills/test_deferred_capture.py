"""Tests for the deferred-capture contract skill structure and content.

Validates that the SKILL.md contains all required contract elements:
CLI interface, issue template, label taxonomy, duplicate detection,
JSON output spec, and compliance test.

Following BDD principles with Given/When/Then scenarios.
"""

import re
from pathlib import Path

import pytest

MAX_PROSE_LINE_LENGTH = 80

SKILL_DIR = Path(__file__).parents[3] / "skills" / "deferred-capture"


class TestDeferredCaptureSkillStructure:
    """Feature: deferred-capture skill defines a complete contract.

    As a plugin developer
    I want a canonical deferred-capture contract
    So that all plugins capture deferred items consistently
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the deferred-capture SKILL.md."""
        return SKILL_DIR / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the deferred-capture SKILL.md content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Skill file exists at expected location.

        Given the leyline plugin
        When checking for deferred-capture skill
        Then SKILL.md should exist at the canonical path
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_content: str) -> None:
        """Scenario: Skill file has valid YAML frontmatter.

        Given the deferred-capture SKILL.md
        When reading the file
        Then it should start with YAML frontmatter containing name and
        description fields
        """
        assert skill_content.startswith("---"), "Missing YAML frontmatter"
        assert "name: deferred-capture" in skill_content
        assert "description:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_cli_interface(self, skill_content: str) -> None:
        """Scenario: Skill documents the required CLI arguments.

        Given the deferred-capture SKILL.md
        When reading the CLI Interface section
        Then it should document --title, --source, --context,
        and --dry-run arguments
        """
        assert "## CLI Interface" in skill_content
        assert "--title" in skill_content
        assert "--source" in skill_content
        assert "--context" in skill_content
        assert "--dry-run" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_optional_arguments(self, skill_content: str) -> None:
        """Scenario: Skill documents all optional CLI arguments.

        Given the deferred-capture SKILL.md
        When reading the optional arguments list
        Then it should include --labels, --session-id, --artifact-path,
        and --captured-by
        """
        assert "--labels" in skill_content
        assert "--session-id" in skill_content
        assert "--artifact-path" in skill_content
        assert "--captured-by" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_issue_template(self, skill_content: str) -> None:
        """Scenario: Skill specifies a complete issue template.

        Given the deferred-capture SKILL.md
        When reading the Issue Template section
        Then it should define the [Deferred] title prefix, labels,
        and body structure including Context and Next Steps
        """
        assert "## Issue Template" in skill_content
        assert "[Deferred]" in skill_content
        assert "### Context" in skill_content
        assert "### Next Steps" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_label_taxonomy(self, skill_content: str) -> None:
        """Scenario: Skill defines labels for all known sources.

        Given the deferred-capture SKILL.md
        When reading the Label Taxonomy section
        Then it should define deferred plus all source labels:
        war-room, brainstorm, scope-guard, feature-review,
        review, regression, egregore
        """
        assert "## Label Taxonomy" in skill_content
        assert "`deferred`" in skill_content
        assert "`war-room`" in skill_content
        assert "`brainstorm`" in skill_content
        assert "`scope-guard`" in skill_content
        assert "`feature-review`" in skill_content
        assert "`review`" in skill_content
        assert "`regression`" in skill_content
        assert "`egregore`" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_duplicate_detection(self, skill_content: str) -> None:
        """Scenario: Skill specifies duplicate detection behavior.

        Given the deferred-capture SKILL.md
        When reading the Duplicate Detection section
        Then it should describe the gh issue list search and
        title-normalization comparison
        """
        assert "## Duplicate Detection" in skill_content
        assert "gh issue list" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_defines_json_output_contract(self, skill_content: str) -> None:
        """Scenario: Skill specifies all JSON output shapes.

        Given the deferred-capture SKILL.md
        When reading the Output section
        Then it should define created, duplicate, and error status values
        """
        assert '"status"' in skill_content
        assert '"created"' in skill_content
        assert '"duplicate"' in skill_content
        assert '"error"' in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_includes_compliance_test(self, skill_content: str) -> None:
        """Scenario: Skill documents a runnable compliance test.

        Given the deferred-capture SKILL.md
        When reading the Compliance Test section
        Then it should show an invocation with --dry-run and note that
        valid JSON with a status field is required
        """
        assert "## Compliance Test" in skill_content
        assert "--dry-run" in skill_content
        assert "status" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_label_colors_defined(self, skill_content: str) -> None:
        """Scenario: Every label row includes a hex color code.

        Given the deferred-capture SKILL.md label table
        When reading each row
        Then every label should have a hex color in #RRGGBB format
        """
        hex_colors = re.findall(r"#[0-9A-Fa-f]{6}", skill_content)
        # One color per label: deferred + 7 sources = 8
        assert len(hex_colors) >= 8, (
            f"Expected at least 8 hex colors, found {len(hex_colors)}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_prose_lines_under_80_chars(self, skill_content: str) -> None:
        """Scenario: Prose lines respect 80-char wrapping limit.

        Given the deferred-capture SKILL.md
        When checking line lengths outside code blocks and tables
        Then all prose lines should be 80 characters or fewer
        """
        in_code = False
        violations = []
        for i, line in enumerate(skill_content.split("\n"), 1):
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            # Skip table rows and horizontal rules
            if line.startswith("|") or line.startswith("---"):
                continue
            if len(line) > MAX_PROSE_LINE_LENGTH:
                violations.append((i, len(line), line[:60]))
        assert violations == [], f"Lines exceeding 80 chars: {violations}"
