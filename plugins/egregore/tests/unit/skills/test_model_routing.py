"""BDD tests for egregore summon model-routing module.

Feature: Model Routing Module Validation
  As a plugin developer
  I want the model-routing module to follow ecosystem conventions
  So that pipeline steps route to cost-appropriate model tiers
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

MODULE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "summon"
    / "modules"
)
MODULE_FILE = MODULE_DIR / "model-routing.md"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestModelRoutingFileExistence:
    """
    Feature: Module file existence and readability

    As a plugin validator
    I want the model-routing module to exist and be readable
    So that the egregore orchestrator can load it on demand
    """

    @pytest.mark.bdd
    def test_module_file_exists(self) -> None:
        """Scenario: Module file present
        Given the summon skill
        When checking for model-routing module
        Then model-routing.md should exist on disk
        """
        assert MODULE_FILE.exists(), f"model-routing.md not found at {MODULE_FILE}"

    @pytest.mark.bdd
    def test_module_file_is_readable(self) -> None:
        """Scenario: Module file readable
        Given the model-routing.md exists
        When reading the file
        Then it should return non-empty content
        """
        content = MODULE_FILE.read_text()
        assert len(content) > 0, "model-routing.md is empty"


class TestModelRoutingFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the model-routing frontmatter to contain required fields
    So that the module is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_correct_name(self) -> None:
        """Scenario: Name field matches module identity
        Given the model-routing.md module
        When parsing frontmatter
        Then the name field should equal 'model-routing'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "model-routing", (
            f"Expected name='model-routing', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present
        Given the model-routing.md module
        When parsing frontmatter
        Then a description field should exist with meaningful content
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "description" in fm, "Frontmatter missing 'description'"
        assert len(fm["description"]) > 20, "description is too short to be meaningful"

    @pytest.mark.bdd
    def test_frontmatter_has_estimated_tokens(self) -> None:
        """Scenario: Token estimate present
        Given the model-routing.md module
        When parsing frontmatter
        Then the estimated_tokens field should be a positive integer
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "estimated_tokens" in fm, "Frontmatter missing 'estimated_tokens' field"
        assert isinstance(fm["estimated_tokens"], int), (
            "estimated_tokens must be an integer"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_category(self) -> None:
        """Scenario: Category field present
        Given the model-routing.md module
        When parsing frontmatter
        Then a category field should exist
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "category" in fm, "Frontmatter missing 'category' field"


class TestModelRoutingRequiredSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the model-routing to contain all required sections
    So that tier definitions and routing logic are documented
    """

    @pytest.mark.bdd
    def test_has_model_tier_definitions_section(self) -> None:
        """Scenario: Model Tier Definitions section present
        Given the model-routing.md module
        When scanning for section headings
        Then a Model Tier Definitions section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Model Tier Definitions" in content, (
            "Missing required '## Model Tier Definitions' section"
        )

    @pytest.mark.bdd
    def test_has_pipeline_step_routing_section(self) -> None:
        """Scenario: Pipeline Step Routing section present
        Given the model-routing.md module
        When scanning for section headings
        Then a Pipeline Step Routing section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Pipeline Step Routing" in content, (
            "Missing required '## Pipeline Step Routing' section"
        )

    @pytest.mark.bdd
    def test_has_dynamic_tier_adjustment_section(self) -> None:
        """Scenario: Dynamic Tier Adjustment section present
        Given the model-routing.md module
        When scanning for section headings
        Then a Dynamic Tier Adjustment section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Dynamic Tier Adjustment" in content, (
            "Missing required '## Dynamic Tier Adjustment' section"
        )

    @pytest.mark.bdd
    def test_has_fallback_protocol_section(self) -> None:
        """Scenario: Fallback Protocol section present
        Given the model-routing.md module
        When scanning for section headings
        Then a Fallback Protocol section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Fallback Protocol" in content or "Fallback Protocol" in content, (
            "Missing Fallback Protocol section"
        )


class TestModelRoutingContent:
    """
    Feature: Model routing content validation

    As a plugin developer
    I want the module to define model tiers and routing rules
    So that pipeline cost optimization is predictable
    """

    @pytest.mark.bdd
    def test_defines_haiku_tier(self) -> None:
        """Scenario: Haiku/Lightweight tier defined
        Given the model-routing.md module
        When scanning content
        Then Haiku or Lightweight tier should be documented
        """
        content = MODULE_FILE.read_text()
        assert "Haiku" in content or "Lightweight" in content, (
            "model-routing.md must define Haiku/Lightweight tier"
        )

    @pytest.mark.bdd
    def test_defines_sonnet_tier(self) -> None:
        """Scenario: Sonnet/Standard tier defined
        Given the model-routing.md module
        When scanning content
        Then Sonnet or Standard tier should be documented
        """
        content = MODULE_FILE.read_text()
        assert "Sonnet" in content or "Standard" in content, (
            "model-routing.md must define Sonnet/Standard tier"
        )

    @pytest.mark.bdd
    def test_defines_opus_tier(self) -> None:
        """Scenario: Opus/Deep tier defined
        Given the model-routing.md module
        When scanning content
        Then Opus or Deep tier should be documented
        """
        content = MODULE_FILE.read_text()
        assert "Opus" in content or "Deep" in content, (
            "model-routing.md must define Opus/Deep tier"
        )

    @pytest.mark.bdd
    def test_references_model_usage_json(self) -> None:
        """Scenario: Cost tracking storage documented
        Given the model-routing.md module
        When scanning content
        Then it should reference .egregore/model-usage.json
        """
        content = MODULE_FILE.read_text()
        assert ".egregore/model-usage.json" in content, (
            "model-routing.md must reference .egregore/model-usage.json"
        )

    @pytest.mark.bdd
    def test_fallback_never_downgrades_from_deep(self) -> None:
        """Scenario: Fallback protocol never downgrades from Deep
        Given the model-routing.md module
        When scanning the Fallback Protocol section
        Then it should state that Deep is never downgraded
        """
        content = MODULE_FILE.read_text()
        lower = content.lower()
        assert "never downgrade" in lower or "never downgrade from deep" in lower, (
            "model-routing.md must state fallback never downgrades from Deep"
        )

    @pytest.mark.bdd
    def test_defines_pipeline_stages(self) -> None:
        """Scenario: Pipeline stages documented in routing table
        Given the model-routing.md module
        When scanning the Pipeline Step Routing section
        Then INTAKE, BUILD, QUALITY, and SHIP stages should appear
        """
        content = MODULE_FILE.read_text()
        for stage in ["INTAKE", "BUILD", "QUALITY", "SHIP"]:
            assert stage in content, (
                f"model-routing.md must document the {stage} pipeline stage"
            )

    @pytest.mark.bdd
    def test_dynamic_adjustment_signals(self) -> None:
        """Scenario: Dynamic adjustment signals documented
        Given the model-routing.md module
        When scanning the Dynamic Tier Adjustment section
        Then step failure and reflexion buffer should be listed as signals
        """
        content = MODULE_FILE.read_text()
        lower = content.lower()
        assert "step failure" in lower or "fails" in lower, (
            "model-routing.md must document step failure as adjustment signal"
        )
        assert "reflexion" in lower, (
            "model-routing.md must document reflexion buffer as adjustment signal"
        )


class TestModelRoutingLineWrapping:
    """
    Feature: Markdown prose line wrapping

    As a documentation maintainer
    I want prose lines to wrap at 80 characters
    So that git diffs stay clean and reviewable
    """

    @pytest.mark.bdd
    def test_prose_lines_wrap_at_80_chars(self) -> None:
        """Scenario: Prose lines respect 80-char wrap limit
        Given the model-routing.md module
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
