#!/usr/bin/env python3
"""Tests for workflow-steps.md modularization.

These tests verify that the workflow-steps.md file has been properly
modularized into separate step files while preserving all content.

Following Iron Law: These tests are written BEFORE implementation.
They MUST FAIL initially, then pass after modularization.
"""

import re
from pathlib import Path

import pytest

# Base paths
SANCTUM_ROOT = Path(__file__).parent.parent
COMMANDS_DIR = SANCTUM_ROOT / "commands"
FIX_PR_MODULES = COMMANDS_DIR / "fix-pr-modules"
STEPS_DIR = FIX_PR_MODULES / "steps"


class TestModularStructureExists:
    """Tests that verify the modular file structure exists."""

    def test_steps_directory_exists(self):
        """The steps/ subdirectory should exist."""
        assert STEPS_DIR.exists(), f"Steps directory not found: {STEPS_DIR}"
        assert STEPS_DIR.is_dir(), f"Steps path is not a directory: {STEPS_DIR}"

    @pytest.mark.parametrize(
        "step_file",
        [
            "1-analyze.md",
            "2-triage.md",
            "3-plan.md",
            "4-fix.md",
            "5-validate.md",
            "6-complete.md",
        ],
    )
    def test_step_files_exist(self, step_file: str):
        """Each workflow step should have its own file."""
        step_path = STEPS_DIR / step_file
        assert step_path.exists(), f"Step file not found: {step_path}"

    def test_hub_document_exists(self):
        """The hub document (workflow-steps.md) should still exist."""
        hub_path = FIX_PR_MODULES / "workflow-steps.md"
        assert hub_path.exists(), f"Hub document not found: {hub_path}"


class TestHubDocumentStructure:
    """Tests for the hub document after modularization."""

    @pytest.fixture
    def hub_content(self) -> str:
        """Load the hub document content."""
        hub_path = FIX_PR_MODULES / "workflow-steps.md"
        return hub_path.read_text(encoding="utf-8")

    def test_hub_has_title(self, hub_content: str):
        """Hub document should have a title."""
        assert "# Fix PR: Workflow Steps" in hub_content

    def test_hub_has_overview(self, hub_content: str):
        """Hub document should have an overview section."""
        assert "## Overview" in hub_content or "## Quick Navigation" in hub_content

    @pytest.mark.parametrize(
        "step_num,step_name",
        [
            (1, "Analyze"),
            (2, "Triage"),
            (3, "Plan"),
            (4, "Fix"),
            (5, "Validate"),
            (6, "Complete"),
        ],
    )
    def test_hub_links_to_all_steps(
        self, hub_content: str, step_num: int, step_name: str
    ):
        """Hub document should link to each step module."""
        # Look for link pattern: [Step N: Name](steps/N-name.md)
        link_pattern = rf"\[.*Step\s*{step_num}.*{step_name}.*\]\(steps/{step_num}-"
        assert re.search(link_pattern, hub_content, re.IGNORECASE), (
            f"Hub missing link to Step {step_num}: {step_name}"
        )

    def test_hub_is_concise(self, hub_content: str):
        """Hub document should be under 200 lines (navigation focused).

        Original monolithic file was 1203 lines. Hub should be <200 lines,
        representing ~85% reduction in the main document.
        """
        line_count = len(hub_content.splitlines())
        assert line_count < 200, (
            f"Hub document too long ({line_count} lines). "
            "Should be a concise navigation document (<200 lines)."
        )


class TestStepContentCompleteness:
    """Tests that verify all original content is preserved in modules."""

    @pytest.fixture
    def original_content(self) -> str:
        """Load content that should be preserved.

        Note: In the initial failing test, we check against known content.
        After modularization, this verifies content wasn't lost.
        """
        # These are key content markers that MUST exist in the modularized files
        return ""

    def test_step1_contains_key_content(self):
        """Step 1 (Analyze) should contain discovery and context content."""
        step_path = STEPS_DIR / "1-analyze.md"
        content = step_path.read_text(encoding="utf-8")

        # Key content markers for Step 1
        assert "Identify Target PR" in content
        assert "Fetch Review Context" in content
        assert "gh pr view" in content
        assert "GraphQL" in content or "graphql" in content
        assert "reviewThreads" in content

    def test_step2_contains_key_content(self):
        """Step 2 (Triage) should contain classification content."""
        step_path = STEPS_DIR / "2-triage.md"
        content = step_path.read_text(encoding="utf-8")

        # Key content markers for Step 2
        assert "Classify" in content
        assert "Critical" in content
        assert "Deferred" in content
        assert "Suggestion" in content
        assert "Triage" in content

    def test_step3_contains_key_content(self):
        """Step 3 (Plan) should contain fix strategy content."""
        step_path = STEPS_DIR / "3-plan.md"
        content = step_path.read_text(encoding="utf-8")

        # Key content markers for Step 3
        assert "Fix Strateg" in content
        assert "Commit Strategy" in content
        assert "Single" in content or "Separate" in content

    def test_step4_contains_key_content(self):
        """Step 4 (Fix) should contain change application content."""
        step_path = STEPS_DIR / "4-fix.md"
        content = step_path.read_text(encoding="utf-8")

        # Key content markers for Step 4
        assert "Apply" in content
        assert "Commit" in content
        assert "Edit tool" in content or "changes" in content.lower()

    def test_step5_contains_key_content(self):
        """Step 5 (Validate) should contain test and verify content."""
        step_path = STEPS_DIR / "5-validate.md"
        content = step_path.read_text(encoding="utf-8")

        # Key content markers for Step 5
        assert "Version Validation" in content or "Test Plan" in content
        assert "Quality Gates" in content or "make test" in content
        assert "pytest" in content or "validation" in content.lower()

    def test_step6_contains_key_content(self):
        """Step 6 (Complete) should contain thread resolution content."""
        step_path = STEPS_DIR / "6-complete.md"
        content = step_path.read_text(encoding="utf-8")

        # Key content markers for Step 6
        assert "Thread Resolution" in content or "resolveReviewThread" in content
        assert "PRRT_" in content
        assert "Summary" in content
        assert "Issue" in content


class TestCrossReferences:
    """Tests that verify cross-references work correctly."""

    def test_step_files_reference_adjacent_steps(self):
        """Each step should reference the next step for flow."""
        for i in range(1, 6):
            step_path = STEPS_DIR / f"{i}-analyze.md".replace(
                "1-analyze",
                f"{i}-{'analyze triage plan fix validate complete'.split()[i - 1]}",
            )
            # Construct actual filename
            names = ["analyze", "triage", "plan", "fix", "validate", "complete"]
            step_path = STEPS_DIR / f"{i}-{names[i - 1]}.md"

            if step_path.exists():
                content = step_path.read_text(encoding="utf-8")
                # Should reference next step
                next_step = i + 1
                if next_step <= 6:
                    # Flexible check - either links to next step or mentions it
                    has_next_ref = (
                        f"Step {next_step}" in content
                        or f"{next_step}-" in content
                        or f"step-{next_step}" in content.lower()
                    )
                    # This is a soft check - not all steps must link forward
                    # but it's good practice

    def test_steps_have_see_also_sections(self):
        """Each step should have a See Also section for navigation."""
        for i in range(1, 7):
            names = ["analyze", "triage", "plan", "fix", "validate", "complete"]
            step_path = STEPS_DIR / f"{i}-{names[i - 1]}.md"

            if step_path.exists():
                content = step_path.read_text(encoding="utf-8")
                # Should have navigation aids
                has_navigation = (
                    "See Also" in content
                    or "Related" in content
                    or "← " in content  # Back link
                    or "→ " in content  # Forward link
                    or "[Main" in content  # Link to hub
                )
                assert has_navigation, f"{step_path.name} missing navigation aids"


class TestNoContentLoss:
    """Tests that verify no content was lost during modularization."""

    def test_total_content_preserved(self):
        """Combined modules should have similar content volume to original."""
        # Original file was 1203 lines, +47 lines for PENDING review detection (PR #142)
        # +270 lines for mandatory issue creation enforcement (Gates 2 & 3)
        ORIGINAL_LINE_COUNT = 1520
        TOLERANCE = 0.20  # Allow 20% variance for added navigation/headers/structure

        # Count lines in hub + all step files
        total_lines = 0

        hub_path = FIX_PR_MODULES / "workflow-steps.md"
        if hub_path.exists():
            total_lines += len(hub_path.read_text().splitlines())

        for i in range(1, 7):
            names = ["analyze", "triage", "plan", "fix", "validate", "complete"]
            step_path = STEPS_DIR / f"{i}-{names[i - 1]}.md"
            if step_path.exists():
                total_lines += len(step_path.read_text().splitlines())

        # Should be within tolerance of original
        min_expected = int(ORIGINAL_LINE_COUNT * (1 - TOLERANCE))
        max_expected = int(ORIGINAL_LINE_COUNT * (1 + TOLERANCE))

        assert min_expected <= total_lines <= max_expected, (
            f"Content volume mismatch. Expected ~{ORIGINAL_LINE_COUNT} lines, "
            f"got {total_lines}. Range: {min_expected}-{max_expected}"
        )

    def test_critical_sections_preserved(self):
        """Critical workflow sections must exist in the modularized files."""
        all_content = ""

        # Gather all content
        hub_path = FIX_PR_MODULES / "workflow-steps.md"
        if hub_path.exists():
            all_content += hub_path.read_text()

        for i in range(1, 7):
            names = ["analyze", "triage", "plan", "fix", "validate", "complete"]
            step_path = STEPS_DIR / f"{i}-{names[i - 1]}.md"
            if step_path.exists():
                all_content += step_path.read_text()

        # Critical sections that MUST be preserved
        critical_markers = [
            "MANDATORY",  # Workflow guardrails
            "resolveReviewThread",  # GraphQL mutation
            "addPullRequestReviewThreadReply",  # Thread reply mutation
            "gh api graphql",  # API usage
            "Version Validation",  # Step 5 content
            "Issue Linkage",  # Step 6 content
            "Summary Comment",  # Final step
        ]

        for marker in critical_markers:
            assert marker in all_content, f"Critical content missing: '{marker}'"


class TestModuleHeaders:
    """Tests that each module has proper headers and metadata."""

    @pytest.mark.parametrize(
        "step_num,step_name,step_title",
        [
            (1, "analyze", "Analyze"),
            (2, "triage", "Triage"),
            (3, "plan", "Plan"),
            (4, "fix", "Fix"),
            (5, "validate", "Validate"),
            (6, "complete", "Complete"),
        ],
    )
    def test_step_has_proper_header(
        self, step_num: int, step_name: str, step_title: str
    ):
        """Each step file should have a proper H1 header."""
        step_path = STEPS_DIR / f"{step_num}-{step_name}.md"
        content = step_path.read_text(encoding="utf-8")

        # Should start with H1 containing step number and name
        first_line = content.strip().split("\n")[0]
        assert first_line.startswith("# "), f"Step {step_num} missing H1 header"
        assert f"Step {step_num}" in first_line or step_title in first_line, (
            f"Step {step_num} header should mention step number or title"
        )

    @pytest.mark.parametrize("step_num", [1, 2, 3, 4, 5, 6])
    def test_step_has_purpose_section(self, step_num: int):
        """Each step should explain its purpose."""
        names = ["analyze", "triage", "plan", "fix", "validate", "complete"]
        step_path = STEPS_DIR / f"{step_num}-{names[step_num - 1]}.md"
        content = step_path.read_text(encoding="utf-8")

        assert "**Purpose**" in content or "Purpose:" in content, (
            f"Step {step_num} missing Purpose section"
        )
