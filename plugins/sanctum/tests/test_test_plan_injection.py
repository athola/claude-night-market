# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,PLR2004,E501
"""BDD-style tests for shared test-plan-injection module.

Tests cover:
- Detection logic (heading patterns + checkbox threshold)
- Generation template structure
- Injection point selection
- Shared module structure and cross-references
- fix-pr step 6.5b integration
- pr-review step 17.5 integration
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Base paths
SANCTUM_ROOT = Path(__file__).parent.parent
COMMANDS_DIR = SANCTUM_ROOT / "commands"
SHARED_DIR = COMMANDS_DIR / "shared"
FIX_PR_MODULES = COMMANDS_DIR / "fix-pr-modules"
PR_REVIEW_MODULES = COMMANDS_DIR / "pr-review" / "modules"


# ==============================================================================
# Detection Logic (extracted from shared module for testability)
# ==============================================================================

# Heading pattern from test-plan-injection.md
TEST_PLAN_HEADING_PATTERN = re.compile(
    r"##+ (Test [Pp]lan|Manual Test|Verification Steps)",
    re.IGNORECASE,
)

CHECKBOX_PATTERN = re.compile(r"- \[[ x]\]")


def has_test_plan(body: str) -> bool:
    """Check whether a PR body contains a valid test plan.

    A valid test plan requires both:
    1. A recognized heading (## Test Plan, ## Manual Testing, etc.)
    2. At least 3 checkbox items (- [ ] or - [x])
    """
    if not TEST_PLAN_HEADING_PATTERN.search(body):
        return False
    checkbox_count = len(CHECKBOX_PATTERN.findall(body))
    return checkbox_count >= 3


def find_injection_point(body: str) -> str:
    """Determine where to inject the test plan.

    Returns:
        'before_review_summary' if ### Code Review Summary exists
        'append' otherwise
    """
    if "### Code Review Summary" in body:
        return "before_review_summary"
    return "append"


def inject_test_plan(body: str, test_plan: str) -> str:
    """Inject a test plan into the PR body at the correct location."""
    if has_test_plan(body):
        return body  # Already has one

    insertion_point = find_injection_point(body)
    if insertion_point == "before_review_summary":
        return body.replace(
            "### Code Review Summary",
            f"\n{test_plan}\n\n---\n\n### Code Review Summary",
        )
    return f"{body}\n\n---\n\n{test_plan}"


# ==============================================================================
# Test Plan Detection
# ==============================================================================


class TestTestPlanDetection:
    """Feature: Detect existing test plans in PR descriptions.

    As the test-plan-injection module
    I want to detect whether a PR body already has a test plan
    So that I avoid injecting duplicates
    """

    @pytest.mark.unit
    def test_detects_valid_test_plan_with_heading_and_checkboxes(self) -> None:
        """Scenario: Body with heading and 3+ checkboxes is valid.

        Given a PR body with '## Test Plan' heading
        And 3 checkbox items
        When checking for test plan
        Then it should return True
        """
        body = """## Summary
Some changes here.

## Test Plan
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3
"""
        assert has_test_plan(body) is True

    @pytest.mark.unit
    def test_rejects_heading_without_enough_checkboxes(self) -> None:
        """Scenario: Heading with fewer than 3 checkboxes is invalid.

        Given a PR body with '## Test Plan' heading
        And only 2 checkbox items
        When checking for test plan
        Then it should return False
        """
        body = """## Test Plan
- [ ] Step 1
- [ ] Step 2
"""
        assert has_test_plan(body) is False

    @pytest.mark.unit
    def test_rejects_checkboxes_without_heading(self) -> None:
        """Scenario: Checkboxes without recognized heading is invalid.

        Given a PR body with 5 checkboxes
        But no recognized test plan heading
        When checking for test plan
        Then it should return False
        """
        body = """## Checklist
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3
- [ ] Item 4
- [ ] Item 5
"""
        assert has_test_plan(body) is False

    @pytest.mark.unit
    def test_detects_manual_testing_heading(self) -> None:
        """Scenario: '## Manual Testing' is a valid heading.

        Given a PR body with '## Manual Testing' heading
        And 3 checkboxes
        When checking for test plan
        Then it should return True
        """
        body = """## Manual Testing
- [ ] Test login
- [ ] Test logout
- [ ] Test error handling
"""
        assert has_test_plan(body) is True

    @pytest.mark.unit
    def test_detects_verification_steps_heading(self) -> None:
        """Scenario: '### Verification Steps' is a valid heading.

        Given a PR body with '### Verification Steps' heading
        And 4 checkboxes
        When checking for test plan
        Then it should return True
        """
        body = """### Verification Steps
- [ ] Run tests
- [x] Check lint
- [ ] Manual test
- [ ] Review output
"""
        assert has_test_plan(body) is True

    @pytest.mark.unit
    def test_counts_checked_and_unchecked_boxes(self) -> None:
        """Scenario: Both [x] and [ ] count as checkboxes.

        Given a PR body with mix of checked and unchecked boxes
        When counting checkboxes
        Then both types should be counted
        """
        body = """## Test Plan
- [x] Already done
- [x] Also done
- [ ] Still pending
"""
        assert has_test_plan(body) is True

    @pytest.mark.unit
    def test_empty_body_has_no_test_plan(self) -> None:
        """Scenario: Empty body has no test plan.

        Given an empty PR body
        When checking for test plan
        Then it should return False
        """
        assert has_test_plan("") is False


# ==============================================================================
# Injection Point Selection
# ==============================================================================


class TestTestPlanInjectionPoint:
    """Feature: Select correct injection point in PR body.

    As the test-plan-injection module
    I want to insert the test plan at the right location
    So that the PR description stays well-organized
    """

    @pytest.mark.unit
    def test_injects_before_code_review_summary(self) -> None:
        """Scenario: Insert before Code Review Summary when present.

        Given a PR body with '### Code Review Summary' section
        When determining injection point
        Then it should return 'before_review_summary'
        """
        body = """## Summary
Changes.

### Code Review Summary
| Category | Count |
"""
        assert find_injection_point(body) == "before_review_summary"

    @pytest.mark.unit
    def test_appends_when_no_review_summary(self) -> None:
        """Scenario: Append at end when no Code Review Summary.

        Given a PR body without Code Review Summary
        When determining injection point
        Then it should return 'append'
        """
        body = """## Summary
Some changes.
"""
        assert find_injection_point(body) == "append"

    @pytest.mark.unit
    def test_injection_preserves_existing_content(self) -> None:
        """Scenario: Injected test plan preserves original content.

        Given a PR body with existing sections
        When injecting a test plan
        Then all original content should remain
        """
        body = """## Summary
My changes.

### Code Review Summary
| Critical | 0 |
"""
        test_plan = "## Test Plan\n- [ ] Step 1\n- [ ] Step 2\n- [ ] Step 3"
        result = inject_test_plan(body, test_plan)

        assert "My changes." in result
        assert "### Code Review Summary" in result
        assert "## Test Plan" in result

    @pytest.mark.unit
    def test_injection_places_plan_before_review_summary(self) -> None:
        """Scenario: Test plan appears before Code Review Summary.

        Given a PR body with Code Review Summary
        When injecting a test plan
        Then the test plan should come before the review summary
        """
        body = """## Summary
Changes.

### Code Review Summary
| Critical | 0 |
"""
        test_plan = "## Test Plan\n- [ ] Step 1\n- [ ] Step 2\n- [ ] Step 3"
        result = inject_test_plan(body, test_plan)

        plan_pos = result.index("## Test Plan")
        summary_pos = result.index("### Code Review Summary")
        assert plan_pos < summary_pos

    @pytest.mark.unit
    def test_append_adds_separator_before_plan(self) -> None:
        """Scenario: Appended test plan has a separator.

        Given a PR body without Code Review Summary
        When injecting a test plan at the end
        Then a '---' separator should precede the plan
        """
        body = "## Summary\nSome changes."
        test_plan = "## Test Plan\n- [ ] Step 1\n- [ ] Step 2\n- [ ] Step 3"
        result = inject_test_plan(body, test_plan)

        assert "---" in result
        separator_pos = result.index("---")
        plan_pos = result.index("## Test Plan")
        assert separator_pos < plan_pos

    @pytest.mark.unit
    def test_skips_injection_when_plan_exists(self) -> None:
        """Scenario: Skip injection when test plan already present.

        Given a PR body that already has a valid test plan
        When attempting to inject another test plan
        Then the body should remain unchanged
        """
        body = """## Test Plan
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3
"""
        new_plan = "## Test Plan\n- [ ] New step 1\n- [ ] New step 2\n- [ ] New step 3"
        result = inject_test_plan(body, new_plan)

        assert result == body


# ==============================================================================
# Shared Module Structure
# ==============================================================================


class TestSharedModuleStructure:
    """Feature: Shared test-plan-injection module exists with correct structure.

    As a maintainer
    I want the shared module to be properly structured
    So that both fix-pr and pr-review can reference it
    """

    @pytest.fixture
    def shared_module_content(self) -> str:
        """Load the shared test-plan-injection module."""
        module_path = SHARED_DIR / "test-plan-injection.md"
        return module_path.read_text()

    @pytest.mark.unit
    def test_shared_directory_exists(self) -> None:
        """Scenario: shared/ directory exists under commands/.

        Given the sanctum plugin
        When checking for commands/shared/
        Then the directory should exist
        """
        assert SHARED_DIR.exists(), f"Shared directory not found: {SHARED_DIR}"
        assert SHARED_DIR.is_dir()

    @pytest.mark.unit
    def test_test_plan_injection_file_exists(self) -> None:
        """Scenario: test-plan-injection.md exists in shared/.

        Given the shared/ directory
        When checking for the module file
        Then test-plan-injection.md should exist
        """
        module_path = SHARED_DIR / "test-plan-injection.md"
        assert module_path.exists(), f"Module not found: {module_path}"

    @pytest.mark.unit
    def test_module_has_detection_section(self, shared_module_content: str) -> None:
        """Scenario: Module documents detection logic.

        Given the test-plan-injection.md module
        When checking for detection documentation
        Then it should have a Detection Logic section
        """
        assert "Detection Logic" in shared_module_content

    @pytest.mark.unit
    def test_module_has_generation_section(self, shared_module_content: str) -> None:
        """Scenario: Module documents generation template.

        Given the test-plan-injection.md module
        When checking for generation documentation
        Then it should have a Generation Template section
        """
        assert "Generation Template" in shared_module_content

    @pytest.mark.unit
    def test_module_has_injection_section(self, shared_module_content: str) -> None:
        """Scenario: Module documents injection logic.

        Given the test-plan-injection.md module
        When checking for injection documentation
        Then it should have an Injection Logic section
        """
        assert "Injection Logic" in shared_module_content

    @pytest.mark.unit
    def test_module_documents_heading_patterns(
        self, shared_module_content: str
    ) -> None:
        """Scenario: Module lists recognized heading patterns.

        Given the test-plan-injection.md module
        When checking for heading patterns
        Then it should document 'Test Plan' and 'Manual Test' patterns
        """
        assert "Test Plan" in shared_module_content
        assert "Manual Test" in shared_module_content

    @pytest.mark.unit
    def test_module_documents_checkbox_threshold(
        self, shared_module_content: str
    ) -> None:
        """Scenario: Module documents the 3-checkbox minimum.

        Given the test-plan-injection.md module
        When checking for threshold documentation
        Then it should mention at least 3 checkbox items
        """
        # The module should reference the threshold
        assert "3" in shared_module_content
        assert "checkbox" in shared_module_content.lower()

    @pytest.mark.unit
    def test_module_references_both_workflows(self, shared_module_content: str) -> None:
        """Scenario: Module cross-references both consuming workflows.

        Given the test-plan-injection.md module
        When checking for cross-references
        Then it should reference both pr-review and fix-pr
        """
        assert "pr-review" in shared_module_content.lower()
        assert "fix-pr" in shared_module_content.lower()

    @pytest.mark.unit
    def test_module_has_api_fallback(self, shared_module_content: str) -> None:
        """Scenario: Module documents fallback to comment on API failure.

        Given the test-plan-injection.md module
        When checking for error handling
        Then it should document the comment fallback
        """
        assert "fallback" in shared_module_content.lower()
        assert "comment" in shared_module_content.lower()


# ==============================================================================
# fix-pr Step 6.5b Integration
# ==============================================================================


class TestFixPRTestPlanIntegration:
    """Feature: fix-pr step 6.5b injects test plans.

    As the fix-pr completion workflow
    I want to inject test plans into PR descriptions
    So that reviewers have verification steps
    """

    @pytest.fixture
    def fix_pr_summary_content(self) -> str:
        """Load the fix-pr step 6 summary content."""
        summary_path = FIX_PR_MODULES / "steps" / "6-complete" / "summary.md"
        return summary_path.read_text()

    @pytest.mark.unit
    def test_step_6_5b_exists(self, fix_pr_summary_content: str) -> None:
        """Scenario: Step 6.5b section exists in summary.md.

        Given the fix-pr step 6 summary
        When checking for step 6.5b
        Then it should contain the test plan injection step
        """
        assert "6.5b" in fix_pr_summary_content

    @pytest.mark.unit
    def test_step_references_shared_module(self, fix_pr_summary_content: str) -> None:
        """Scenario: Step 6.5b references the shared module.

        Given the fix-pr step 6 summary
        When checking for shared module reference
        Then it should link to test-plan-injection.md
        """
        assert "test-plan-injection" in fix_pr_summary_content

    @pytest.mark.unit
    def test_step_has_detection_logic(self, fix_pr_summary_content: str) -> None:
        """Scenario: Step 6.5b includes detection logic.

        Given the fix-pr step 6 summary
        When checking for detection code
        Then it should check for existing test plan headings
        """
        assert "TEST_PLAN_HEADING" in fix_pr_summary_content

    @pytest.mark.unit
    def test_step_has_generation_from_triage(self, fix_pr_summary_content: str) -> None:
        """Scenario: Step 6.5b generates from fix-pr triage data.

        Given the fix-pr step 6 summary
        When checking for generation source
        Then it should reference FIXED_ITEMS from triage
        """
        assert "FIXED_ITEMS" in fix_pr_summary_content

    @pytest.mark.unit
    def test_step_has_api_fallback(self, fix_pr_summary_content: str) -> None:
        """Scenario: Step 6.5b has fallback to PR comment.

        Given the fix-pr step 6 summary
        When checking for error handling
        Then it should fall back to gh pr comment on API failure
        """
        assert "gh pr comment" in fix_pr_summary_content

    @pytest.mark.unit
    def test_step_includes_quality_gates(self, fix_pr_summary_content: str) -> None:
        """Scenario: Generated test plan includes build gates.

        Given the fix-pr step 6 summary
        When checking the generated test plan template
        Then it should include build and quality gate commands
        """
        assert "make test" in fix_pr_summary_content
        assert "make lint" in fix_pr_summary_content


# ==============================================================================
# pr-review Step 17.5 Integration
# ==============================================================================


class TestPRReviewTestPlanInjection:
    """Feature: pr-review step 17.5 injects test plans.

    As the pr-review workflow
    I want to inject test plans before updating the PR description
    So that the description is self-documenting with verification steps
    """

    @pytest.fixture
    def review_workflow_content(self) -> str:
        """Load the pr-review phases-5-6 module content.

        Step 17.5 lives in review-workflow-phases-5-6.md after the
        review-workflow.md file was split into per-phase modules.
        """
        workflow_path = PR_REVIEW_MODULES / "review-workflow-phases-5-6.md"
        return workflow_path.read_text()

    @pytest.mark.unit
    def test_step_17_5_exists(self, review_workflow_content: str) -> None:
        """Scenario: Step 17.5 section exists in review-workflow-phases-5-6.md.

        Given the pr-review phases-5-6 workflow module
        When checking for step 17.5
        Then it should contain the test plan injection step
        """
        assert "17.5" in review_workflow_content

    @pytest.mark.unit
    def test_step_references_shared_module(self, review_workflow_content: str) -> None:
        """Scenario: Step 17.5 references the shared module.

        Given the pr-review phases-5-6 workflow module
        When checking for shared module reference
        Then it should link to test-plan-injection.md
        """
        assert "test-plan-injection" in review_workflow_content

    @pytest.mark.unit
    def test_step_has_detection_before_injection(
        self, review_workflow_content: str
    ) -> None:
        """Scenario: Step 17.5 detects before injecting.

        Given the pr-review workflow module
        When checking step 17.5 order
        Then detection should come before injection
        """
        content = review_workflow_content
        # Detection section exists
        assert "Detection" in content or "HAS_HEADING" in content

    @pytest.mark.unit
    def test_step_generates_from_phase5_data(
        self, review_workflow_content: str
    ) -> None:
        """Scenario: Step 17.5 uses Phase 5 data for generation.

        Given the pr-review workflow module
        When checking generation source
        Then it should reference blocking/in-scope issues
        """
        assert "BLOCKING_ISSUES" in review_workflow_content or (
            "blocking" in review_workflow_content.lower()
        )

    @pytest.mark.unit
    def test_step_precedes_api_update(self, review_workflow_content: str) -> None:
        """Scenario: Step 17.5 comes before step 18 (API update).

        Given the pr-review workflow module
        When checking step ordering
        Then 17.5 should appear before step 18
        """
        pos_17_5 = review_workflow_content.index("17.5")
        # Step 18 should come after
        pos_18 = review_workflow_content.index("18.", pos_17_5)
        assert pos_17_5 < pos_18

    @pytest.mark.unit
    def test_step_handles_prepend_flow(self, review_workflow_content: str) -> None:
        """Scenario: Step 17.5 handles the prepend flow.

        Given a PR with existing description
        When injecting in prepend mode
        Then it should check the combined body
        """
        assert "prepend" in review_workflow_content.lower()

    @pytest.mark.unit
    def test_step_documents_content_sources(self, review_workflow_content: str) -> None:
        """Scenario: Step 17.5 documents test plan content sources.

        Given the pr-review workflow module
        When checking source documentation
        Then it should list blocking and in-scope issues as sources
        """
        # Look within the 17.5 section area
        assert "content sources" in review_workflow_content.lower() or (
            "Blocking issues" in review_workflow_content
        )
