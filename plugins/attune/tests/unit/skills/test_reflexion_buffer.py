"""BDD tests for attune mission-orchestrator reflexion-buffer module.

Feature: Reflexion Buffer Module Validation
  As a plugin developer
  I want the reflexion-buffer module to follow ecosystem conventions
  So that episodic failure memory integrates correctly
  with the mission-orchestrator retry flow
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

MODULE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "mission-orchestrator"
    / "modules"
)
MODULE_FILE = MODULE_DIR / "reflexion-buffer.md"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestReflexionBufferFileExistence:
    """
    Feature: Module file existence and readability

    As a plugin validator
    I want the reflexion-buffer module to exist and be readable
    So that the orchestrator can load it on demand
    """

    @pytest.mark.bdd
    def test_module_file_exists(self) -> None:
        """Scenario: Module file present
        Given the mission-orchestrator skill
        When checking for reflexion-buffer module
        Then reflexion-buffer.md should exist on disk
        """
        assert MODULE_FILE.exists(), f"reflexion-buffer.md not found at {MODULE_FILE}"

    @pytest.mark.bdd
    def test_module_file_is_readable(self) -> None:
        """Scenario: Module file readable
        Given the reflexion-buffer.md exists
        When reading the file
        Then it should return non-empty content
        """
        content = MODULE_FILE.read_text()
        assert len(content) > 0, "reflexion-buffer.md is empty"


class TestReflexionBufferFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the reflexion-buffer frontmatter to contain required fields
    So that the module is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_correct_name(self) -> None:
        """Scenario: Name field matches module identity
        Given the reflexion-buffer.md module
        When parsing frontmatter
        Then the name field should equal 'reflexion-buffer'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "reflexion-buffer", (
            f"Expected name='reflexion-buffer', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_parent_skill(self) -> None:
        """Scenario: Parent skill declared
        Given the reflexion-buffer.md module
        When parsing frontmatter
        Then parent_skill should be 'attune:mission-orchestrator'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("parent_skill") == "attune:mission-orchestrator", (
            f"Expected parent_skill='attune:mission-orchestrator', "
            f"got {fm.get('parent_skill')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_estimated_tokens(self) -> None:
        """Scenario: Token estimate present
        Given the reflexion-buffer.md module
        When parsing frontmatter
        Then the estimated_tokens field should be a positive integer
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "estimated_tokens" in fm, "Frontmatter missing 'estimated_tokens' field"
        assert isinstance(fm["estimated_tokens"], int), (
            "estimated_tokens must be an integer"
        )
        assert fm["estimated_tokens"] > 0, "estimated_tokens must be positive"

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present
        Given the reflexion-buffer.md module
        When parsing frontmatter
        Then a description field should exist with meaningful content
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description'"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"


class TestReflexionBufferRequiredSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the reflexion-buffer to contain all required sections
    So that the buffer structure and integration are documented
    """

    @pytest.mark.bdd
    def test_has_buffer_structure_section(self) -> None:
        """Scenario: Buffer Structure section present
        Given the reflexion-buffer.md module
        When scanning for section headings
        Then a Buffer Structure section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Buffer Structure" in content, (
            "Missing required '## Buffer Structure' section"
        )

    @pytest.mark.bdd
    def test_has_integration_with_phase_routing_section(self) -> None:
        """Scenario: Integration with Phase Routing section present
        Given the reflexion-buffer.md module
        When scanning for section headings
        Then an Integration with Phase Routing section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Integration with Phase Routing" in content, (
            "Missing '## Integration with Phase Routing' section"
        )

    @pytest.mark.bdd
    def test_has_convergence_detection_section(self) -> None:
        """Scenario: Convergence Detection section present
        Given the reflexion-buffer.md module
        When scanning for section headings
        Then a Convergence Detection section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Convergence Detection" in content, (
            "Missing '## Convergence Detection' section"
        )

    @pytest.mark.bdd
    def test_has_buffer_lifecycle_section(self) -> None:
        """Scenario: Buffer Lifecycle section present
        Given the reflexion-buffer.md module
        When scanning for section headings
        Then a Buffer Lifecycle section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Buffer Lifecycle" in content, "Missing '## Buffer Lifecycle' section"


class TestReflexionBufferContent:
    """
    Feature: Reflexion buffer content validation

    As a plugin developer
    I want the buffer module to document its format and integrations
    So that retry logic can use the buffer correctly
    """

    @pytest.mark.bdd
    def test_contains_buffer_format_template(self) -> None:
        """Scenario: Buffer format template present
        Given the reflexion-buffer.md module
        When scanning content
        Then it should contain the '## Reflexion Buffer' injection template
        """
        content = MODULE_FILE.read_text()
        assert "## Reflexion Buffer" in content, (
            "Missing the reflexion buffer injection format template"
        )

    @pytest.mark.bdd
    def test_references_damage_control(self) -> None:
        """Scenario: Damage-control integration documented
        Given the reflexion-buffer.md module
        When scanning content
        Then it should reference damage-control for retry flow
        """
        content = MODULE_FILE.read_text()
        assert "damage-control" in content, (
            "reflexion-buffer.md must reference damage-control integration"
        )

    @pytest.mark.bdd
    def test_references_ralph_wiggum_integration(self) -> None:
        """Scenario: Ralph Wiggum integration documented
        Given the reflexion-buffer.md module
        When scanning content
        Then it should reference ralph-wiggum integration
        """
        content = MODULE_FILE.read_text()
        assert "ralph-wiggum" in content.lower() or "ralph" in content.lower(), (
            "reflexion-buffer.md must reference ralph-wiggum integration"
        )

    @pytest.mark.bdd
    def test_defines_entry_fields(self) -> None:
        """Scenario: Buffer entry fields are documented
        Given the reflexion-buffer.md module
        When scanning content
        Then it should define action, result, diagnosis, and adjustment fields
        """
        content = MODULE_FILE.read_text()
        for field in ["action", "result", "diagnosis", "adjustment"]:
            assert field in content, (
                f"reflexion-buffer.md must define the '{field}' entry field"
            )

    @pytest.mark.bdd
    def test_documents_convergence_algorithm(self) -> None:
        """Scenario: Convergence detection algorithm present
        Given the reflexion-buffer.md module
        When scanning content
        Then it should document the convergence check logic
        """
        content = MODULE_FILE.read_text()
        assert "is_converged" in content or "convergence" in content.lower(), (
            "reflexion-buffer.md must document convergence detection"
        )


class TestReflexionBufferLineWrapping:
    """
    Feature: Markdown prose line wrapping

    As a documentation maintainer
    I want prose lines to wrap at 80 characters
    So that git diffs stay clean and reviewable
    """

    @pytest.mark.bdd
    def test_prose_lines_wrap_at_80_chars(self) -> None:
        """Scenario: Prose lines respect 80-char wrap limit
        Given the reflexion-buffer.md module
        When checking line lengths of prose lines
        Then no prose line should exceed 80 characters
        """
        content = MODULE_FILE.read_text()
        in_code_block = False
        in_frontmatter = False
        violations = []

        for i, line in enumerate(content.splitlines(), 1):
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            # Skip headings, tables, links, empty lines
            stripped = line.strip()
            if (
                stripped.startswith("#")
                or stripped.startswith("|")
                or stripped.startswith("[")
                or stripped.startswith("![")
                or stripped == ""
                or re.match(r"^https?://", stripped)
            ):
                continue
            if len(line) > 80:
                violations.append(f"  Line {i} ({len(line)} chars): {line[:60]}...")

        assert not violations, "Prose lines exceeding 80 chars:\n" + "\n".join(
            violations
        )
