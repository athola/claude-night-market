"""BDD tests for abstract metacognitive-self-mod trace-capture module.

Feature: Trace Capture Module Validation
  As a plugin developer
  I want the trace-capture module to follow ecosystem conventions
  So that execution traces feed into metacognitive self-improvement
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

MODULE_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "skills"
    / "metacognitive-self-mod"
    / "modules"
)
MODULE_FILE = MODULE_DIR / "trace-capture.md"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestTraceCaptureFileExistence:
    """
    Feature: Module file existence and readability

    As a plugin validator
    I want the trace-capture module to exist and be readable
    So that the metacognitive system can load it on demand
    """

    @pytest.mark.bdd
    def test_module_file_exists(self) -> None:
        """Scenario: Module file present
        Given the metacognitive-self-mod skill
        When checking for trace-capture module
        Then trace-capture.md should exist on disk
        """
        assert MODULE_FILE.exists(), f"trace-capture.md not found at {MODULE_FILE}"

    @pytest.mark.bdd
    def test_module_file_is_readable(self) -> None:
        """Scenario: Module file readable
        Given the trace-capture.md exists
        When reading the file
        Then it should return non-empty content
        """
        content = MODULE_FILE.read_text()
        assert len(content) > 0, "trace-capture.md is empty"


class TestTraceCaptureFrontmatter:
    """
    Feature: YAML frontmatter validity

    As a plugin validator
    I want the trace-capture frontmatter to contain required fields
    So that the module is correctly registered and discoverable
    """

    @pytest.mark.bdd
    def test_frontmatter_has_correct_name(self) -> None:
        """Scenario: Name field matches module identity
        Given the trace-capture.md module
        When parsing frontmatter
        Then the name field should equal 'trace-capture'
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert fm.get("name") == "trace-capture", (
            f"Expected name='trace-capture', got {fm.get('name')!r}"
        )

    @pytest.mark.bdd
    def test_frontmatter_has_description(self) -> None:
        """Scenario: Description field present
        Given the trace-capture.md module
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
        Given the trace-capture.md module
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
        Given the trace-capture.md module
        When parsing frontmatter
        Then a category field should exist
        """
        content = MODULE_FILE.read_text()
        fm = _parse_frontmatter(content)
        assert "category" in fm, "Frontmatter missing 'category' field"


class TestTraceCaptureRequiredSections:
    """
    Feature: Required documentation sections

    As a skill consumer
    I want the trace-capture to contain all required sections
    So that trace structure and capture modes are documented
    """

    @pytest.mark.bdd
    def test_has_trace_structure_section(self) -> None:
        """Scenario: Trace Structure section present
        Given the trace-capture.md module
        When scanning for section headings
        Then a Trace Structure section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Trace Structure" in content, (
            "Missing required '## Trace Structure' section"
        )

    @pytest.mark.bdd
    def test_has_capture_modes_section(self) -> None:
        """Scenario: Capture Modes section present
        Given the trace-capture.md module
        When scanning for section headings
        Then a Capture Modes section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Capture Modes" in content, (
            "Missing required '## Capture Modes' section"
        )

    @pytest.mark.bdd
    def test_has_attribution_analysis_section(self) -> None:
        """Scenario: Attribution Analysis section present
        Given the trace-capture.md module
        When scanning for section headings
        Then an Attribution Analysis section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Attribution Analysis" in content, (
            "Missing required '## Attribution Analysis' section"
        )

    @pytest.mark.bdd
    def test_has_storage_section(self) -> None:
        """Scenario: Storage section present
        Given the trace-capture.md module
        When scanning for section headings
        Then a Storage section should exist
        """
        content = MODULE_FILE.read_text()
        assert "## Storage" in content, "Missing required '## Storage' section"


class TestTraceCaptureContent:
    """
    Feature: Trace capture content validation

    As a plugin developer
    I want the module to define capture modes and storage limits
    So that trace recording is predictable and bounded
    """

    @pytest.mark.bdd
    def test_defines_minimal_capture_mode(self) -> None:
        """Scenario: Minimal capture mode defined
        Given the trace-capture.md module
        When scanning content
        Then the minimal capture mode should be documented
        """
        content = MODULE_FILE.read_text()
        assert "minimal" in content.lower(), (
            "trace-capture.md must define the minimal capture mode"
        )

    @pytest.mark.bdd
    def test_defines_decision_only_capture_mode(self) -> None:
        """Scenario: Decision-only capture mode defined
        Given the trace-capture.md module
        When scanning content
        Then the decision-only capture mode should be documented
        """
        content = MODULE_FILE.read_text()
        assert "decision-only" in content, (
            "trace-capture.md must define the decision-only capture mode"
        )

    @pytest.mark.bdd
    def test_defines_full_capture_mode(self) -> None:
        """Scenario: Full capture mode defined
        Given the trace-capture.md module
        When scanning content
        Then the full capture mode should be documented
        """
        content = MODULE_FILE.read_text()
        # Check for 'full' as a capture mode (in context of modes table)
        assert "`full`" in content or "| `full`" in content, (
            "trace-capture.md must define the full capture mode"
        )

    @pytest.mark.bdd
    def test_references_improvement_memory_json(self) -> None:
        """Scenario: Integration with improvement_memory.json
        Given the trace-capture.md module
        When scanning content
        Then it should reference improvement_memory.json
        """
        content = MODULE_FILE.read_text()
        assert "improvement_memory.json" in content, (
            "trace-capture.md must reference improvement_memory.json"
        )

    @pytest.mark.bdd
    def test_storage_limit_100_traces(self) -> None:
        """Scenario: Maximum 100 traces stored
        Given the trace-capture.md module
        When scanning the Storage section
        Then a 100-trace FIFO limit should be documented
        """
        content = MODULE_FILE.read_text()
        assert "100" in content, (
            "trace-capture.md must document the 100-trace storage limit"
        )

    @pytest.mark.bdd
    def test_storage_30_day_window(self) -> None:
        """Scenario: Rolling 30-day retention window
        Given the trace-capture.md module
        When scanning the Storage section
        Then a 30-day rolling window should be documented
        """
        content = MODULE_FILE.read_text()
        assert "30-day" in content or "30 day" in content, (
            "trace-capture.md must document the 30-day retention window"
        )

    @pytest.mark.bdd
    def test_traces_include_decision_points(self) -> None:
        """Scenario: Traces capture decision points
        Given the trace-capture.md module
        When scanning content
        Then decision points should be part of the trace schema
        """
        content = MODULE_FILE.read_text()
        assert "decision_point" in content or "decision point" in content.lower(), (
            "trace-capture.md must document decision point capture"
        )


class TestTraceCaptureLineWrapping:
    """
    Feature: Markdown prose line wrapping

    As a documentation maintainer
    I want prose lines to wrap at 80 characters
    So that git diffs stay clean and reviewable
    """

    @pytest.mark.bdd
    def test_prose_lines_wrap_at_80_chars(self) -> None:
        """Scenario: Prose lines respect 80-char wrap limit
        Given the trace-capture.md module
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
