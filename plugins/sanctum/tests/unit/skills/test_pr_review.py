"""Tests for the pr-review skill structure and content.

Feature: PR review skill with educational insights
    As a PR reviewer
    I want review findings to include educational context
    So that reviews improve both the code and the implementer
"""

from __future__ import annotations

from pathlib import Path

import pytest

EXPECTED_MIN_FRONTMATTER_DELIMITERS = 2
EXPECTED_MIN_MODULES = 4

SKILL_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "pr-review"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"


class TestSkillStructure:
    """Feature: PR review skill file structure

    As a plugin maintainer
    I want the pr-review skill properly structured
    So that it loads correctly and all modules are present
    """

    @pytest.mark.unit
    def test_skill_file_exists(self) -> None:
        """Scenario: SKILL.md exists
        Given the pr-review skill directory
        When checking for SKILL.md
        Then the file exists
        """
        assert SKILL_FILE.exists()

    @pytest.mark.unit
    def test_skill_has_frontmatter(self) -> None:
        """Scenario: SKILL.md has YAML frontmatter
        Given the pr-review SKILL.md
        When reading its content
        Then it starts with YAML frontmatter delimiters
        """
        content = SKILL_FILE.read_text()
        assert content.startswith("---")
        assert content.count("---") >= EXPECTED_MIN_FRONTMATTER_DELIMITERS

    @pytest.mark.unit
    def test_skill_name_in_frontmatter(self) -> None:
        """Scenario: Frontmatter contains correct name
        Given the pr-review SKILL.md
        When reading the frontmatter
        Then the name field is 'pr-review'
        """
        content = SKILL_FILE.read_text()
        assert "name: pr-review" in content

    @pytest.mark.unit
    def test_educational_insights_module_registered(self) -> None:
        """Scenario: Educational insights module is registered
        Given the pr-review SKILL.md
        When reading the modules list
        Then educational-insights.md is included
        """
        content = SKILL_FILE.read_text()
        assert "modules/educational-insights.md" in content

    @pytest.mark.unit
    def test_all_registered_modules_exist(self) -> None:
        """Scenario: All registered modules have files on disk
        Given the modules listed in SKILL.md frontmatter
        When checking each module path
        Then every referenced file exists
        """
        content = SKILL_FILE.read_text()
        # Extract module paths from frontmatter
        in_modules = False
        modules: list[str] = []
        for line in content.split("\n"):
            if line.strip() == "modules:":
                in_modules = True
                continue
            if in_modules:
                stripped = line.strip()
                if stripped.startswith("- modules/"):
                    modules.append(stripped[2:])  # Remove "- " prefix
                elif stripped.startswith("- ") or not stripped.startswith("-"):
                    if not stripped.startswith("-"):
                        break
            if in_modules and not line.startswith(" ") and not line.startswith("-"):
                break

        assert len(modules) >= EXPECTED_MIN_MODULES, (
            f"Expected at least {EXPECTED_MIN_MODULES} modules, found {len(modules)}"
        )
        for mod in modules:
            mod_path = SKILL_DIR / mod
            assert mod_path.exists(), f"Module {mod} not found at {mod_path}"


class TestEducationalInsightsModule:
    """Feature: Educational insights module content

    As a PR reviewer
    I want the educational insights module to define
    the three-pillar enrichment format
    So that every finding teaches, not just corrects
    """

    @pytest.fixture()
    def content(self) -> str:
        """Load the educational-insights module content."""
        path = MODULES_DIR / "educational-insights.md"
        return path.read_text()

    @pytest.mark.unit
    def test_module_exists(self) -> None:
        """Scenario: Educational insights module file exists
        Given the pr-review modules directory
        When checking for educational-insights.md
        Then the file exists
        """
        assert (MODULES_DIR / "educational-insights.md").exists()

    @pytest.mark.unit
    def test_has_frontmatter(self, content: str) -> None:
        """Scenario: Module has YAML frontmatter
        Given the educational-insights module
        When reading its content
        Then it starts with frontmatter
        """
        assert content.startswith("---")

    @pytest.mark.unit
    def test_three_pillars_defined(self, content: str) -> None:
        """Scenario: Three educational pillars are defined
        Given the educational-insights module
        When reading the content
        Then it defines Why, Proof, and Teachable Moment pillars
        """
        assert "Why It Matters" in content
        assert "Proof" in content
        assert "Teachable Moment" in content

    @pytest.mark.unit
    def test_enriched_finding_format_example(self, content: str) -> None:
        """Scenario: Module includes an enriched finding example
        Given the educational-insights module
        When reading the content
        Then it shows a complete finding with all three pillars
        """
        assert "**Why**:" in content
        assert "**Proof**:" in content
        assert "**Teachable Moment**:" in content

    @pytest.mark.unit
    def test_proof_source_priority(self, content: str) -> None:
        """Scenario: Module defines proof source priority
        Given the educational-insights module
        When reading the proof sourcing section
        Then it lists authoritative sources in priority order
        """
        assert "Language/framework docs" in content or "language" in content.lower()
        assert "OWASP" in content
        assert "Style guides" in content or "style guide" in content.lower()

    @pytest.mark.unit
    def test_depth_by_classification(self, content: str) -> None:
        """Scenario: Insight depth varies by classification
        Given the educational-insights module
        When reading the depth table
        Then BLOCKING requires full depth and BACKLOG is minimal
        """
        assert "BLOCKING" in content
        assert "IN-SCOPE" in content
        assert "SUGGESTION" in content
        assert "BACKLOG" in content

    @pytest.mark.unit
    def test_anti_patterns_section(self, content: str) -> None:
        """Scenario: Module warns against educational anti-patterns
        Given the educational-insights module
        When reading the anti-patterns section
        Then it warns against lecturing without context
        """
        assert "Anti-Pattern" in content or "Don't:" in content

    @pytest.mark.unit
    def test_exit_criteria(self, content: str) -> None:
        """Scenario: Module has exit criteria
        Given the educational-insights module
        When reading the exit criteria
        Then it requires proof links for blocking findings
        """
        assert "Exit Criteria" in content
        assert "BLOCKING" in content
        assert "Proof" in content or "proof" in content


class TestPhase6ReportFormat:
    """Feature: Phase 6 report includes educational insights

    As a PR reviewer
    I want the report template to show enriched findings
    So that the generated report teaches by default
    """

    @pytest.fixture()
    def content(self) -> str:
        """Load the SKILL.md content."""
        return SKILL_FILE.read_text()

    @pytest.mark.unit
    def test_phase6_references_educational_module(self, content: str) -> None:
        """Scenario: Phase 6 references the educational module
        Given the SKILL.md Phase 6 section
        When reading its instructions
        Then it references educational-insights module
        """
        assert "educational-insights" in content

    @pytest.mark.unit
    def test_report_template_has_why_field(self, content: str) -> None:
        """Scenario: Report template includes Why field
        Given the Phase 6 report template in SKILL.md
        When reading the example finding
        Then it includes a Why field with explanation
        """
        assert "**Why**:" in content

    @pytest.mark.unit
    def test_report_template_has_proof_field(self, content: str) -> None:
        """Scenario: Report template includes Proof field
        Given the Phase 6 report template in SKILL.md
        When reading the example finding
        Then it includes a Proof field with a link
        """
        assert "**Proof**:" in content

    @pytest.mark.unit
    def test_report_template_has_teachable_moment(self, content: str) -> None:
        """Scenario: Report template includes Teachable Moment
        Given the Phase 6 report template in SKILL.md
        When reading the example finding
        Then it includes a Teachable Moment field
        """
        assert "**Teachable Moment**:" in content

    @pytest.mark.unit
    def test_blocking_example_has_all_three_pillars(self, content: str) -> None:
        """Scenario: Blocking finding example has full educational context
        Given the blocking finding example in Phase 6
        When reading the example
        Then it has Why, Proof, and Teachable Moment
        """
        # Find the blocking section in the Phase 6 template
        phase6_start = content.find("### Phase 6")
        assert phase6_start != -1
        phase6_section = content[phase6_start:]

        # The blocking example should have all three pillars
        blocking_start = phase6_section.find("### Blocking")
        assert blocking_start != -1
        blocking_section = phase6_section[blocking_start:]

        # Cut at the next section
        in_scope_start = blocking_section.find("### In-Scope")
        if in_scope_start != -1:
            blocking_section = blocking_section[:in_scope_start]

        assert "**Why**:" in blocking_section
        assert "**Proof**:" in blocking_section
        assert "**Teachable Moment**:" in blocking_section

    @pytest.mark.unit
    def test_suggestion_example_has_why(self, content: str) -> None:
        """Scenario: Suggestion finding has at minimum a Why field
        Given the suggestion finding example in Phase 6
        When reading the example
        Then it includes at least a Why field
        """
        phase6_start = content.find("### Phase 6")
        assert phase6_start != -1
        phase6_section = content[phase6_start:]

        suggestion_start = phase6_section.find("### Suggestions")
        assert suggestion_start != -1
        suggestion_section = phase6_section[suggestion_start:]

        backlog_start = suggestion_section.find("### Backlog")
        if backlog_start != -1:
            suggestion_section = suggestion_section[:backlog_start]

        assert "**Why**:" in suggestion_section


class TestOutputFormatTemplates:
    """Feature: Pensive output templates include educational fields

    As a review skill consumer
    I want the finding entry template to support insights
    So that all pensive-based reviews can be educational
    """

    @pytest.fixture()
    def content(self) -> str:
        """Load the output-format-templates module content."""
        path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "pensive"
            / "skills"
            / "unified-review"
            / "modules"
            / "output-format-templates.md"
        )
        return path.read_text()

    @pytest.mark.unit
    def test_finding_template_has_why(self, content: str) -> None:
        """Scenario: Finding template includes Why This Matters
        Given the pensive output-format-templates
        When reading the finding entry template
        Then it includes a Why This Matters field
        """
        assert "Why This Matters" in content

    @pytest.mark.unit
    def test_finding_template_has_proof(self, content: str) -> None:
        """Scenario: Finding template includes Proof field
        Given the pensive output-format-templates
        When reading the finding entry template
        Then it includes a Proof field
        """
        # Look for Proof as a template field (bold)
        assert "**Proof**" in content

    @pytest.mark.unit
    def test_finding_template_has_teachable_moment(self, content: str) -> None:
        """Scenario: Finding template includes Teachable Moment
        Given the pensive output-format-templates
        When reading the finding entry template
        Then it includes a Teachable Moment field
        """
        assert "**Teachable Moment**" in content

    @pytest.mark.unit
    def test_educational_depth_table(self, content: str) -> None:
        """Scenario: Template defines depth by severity
        Given the pensive output-format-templates
        When reading the educational depth section
        Then it maps severity to required educational fields
        """
        assert "Educational Depth" in content or "Severity" in content
        assert "Critical" in content
        assert "Required" in content
