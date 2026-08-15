"""Tests for the branchless-filter exception in rust-review.

Pattern 6 of modules/iterator-and-allocation-slop.md tells reviewers
that hand-rolled loop optimization is slop because LLVM already
unrolls, hoists, and strength-reduces. Branch elimination is the
documented exception: LLVM will not convert a conditional-push filter
into an unconditional-store-plus-conditional-advance, because that
rewrite writes to slots the original never touched.

Without the exception recorded, a reviewer applying Pattern 6
literally flags a justified optimization as slop.

Following BDD principles with Given/When/Then scenarios.
"""

from pathlib import Path

import pytest

MODULE_NAME = "iterator-and-allocation-slop"


@pytest.fixture
def module_content() -> str:
    """Load the iterator-and-allocation-slop module."""
    path = (
        Path(__file__).parents[2]
        / "skills"
        / "rust-review"
        / "modules"
        / f"{MODULE_NAME}.md"
    )
    return path.read_text()


class TestBranchlessException:
    """Feature: Pattern 6 records the branch-elimination exception.

    As a Rust reviewer applying the no-hand-rolled-loops rule
    I want the one transform LLVM cannot do flagged as legitimate
    So that I do not reject a measured, justified optimization
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_branchless_as_exception(self, module_content: str) -> None:
        """Scenario: The module names branchless as the exception.

        Given the iterator-and-allocation-slop module
        When reading the hand-rolled loop optimization pattern
        Then branch elimination is named as a transform the compiler
        will not perform, rather than folded into the slop rule
        """
        lower = module_content.lower()
        assert "branchless" in lower
        assert "exception" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_states_why_llvm_cannot_do_it(self, module_content: str) -> None:
        """Scenario: The module explains the codegen reason.

        Given the branchless exception
        When reading its rationale
        Then it states that the rewrite stores unconditionally and
        advances conditionally, which changes the write pattern
        """
        lower = module_content.lower()
        assert "unconditional" in lower
        assert "advance" in lower or "index" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_requires_measurement_before_accepting(self, module_content: str) -> None:
        """Scenario: The exception is gated on evidence.

        Given the branchless exception
        When reading its acceptance conditions
        Then a profiler-proven hot path and unpredictable data are
        both required before the hand-rolled form is justified
        """
        lower = module_content.lower()
        assert "unpredictable" in lower
        assert "profil" in lower or "measured" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_names_the_costs(self, module_content: str) -> None:
        """Scenario: The exception records what it costs.

        Given the branchless exception
        When reading the tradeoffs
        Then both the best-case regression and the full-size buffer
        allocation are named, so a reviewer can weigh them
        """
        lower = module_content.lower()
        assert "selectivity" in lower
        assert "alloc" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_links_to_loop_optimization_skill(self, module_content: str) -> None:
        """Scenario: The module defers to the shared decision rule.

        Given the branchless exception
        When reading its references
        Then it points at leyline:loop-optimization rather than
        restating the hand-vs-compiler rule
        """
        assert "leyline:loop-optimization" in module_content


class TestBranchlessProseCompliance:
    """Feature: The module follows repo formatting rules.

    As a documentation consumer
    I want 80-char wrapping preserved
    So that the module stays diff-friendly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_prose_under_80_chars(self, module_content: str) -> None:
        """Scenario: Prose lines stay under 80 chars.

        Given the iterator-and-allocation-slop module
        When checking line lengths outside code blocks and tables
        Then all prose lines should be 80 chars or fewer
        """
        in_code = False
        in_frontmatter = False
        frontmatter_closed = False
        violations = []
        for i, line in enumerate(module_content.split("\n"), 1):
            if line.startswith("```"):
                in_code = not in_code
                continue
            if line == "---" and not frontmatter_closed:
                if i == 1:
                    in_frontmatter = True
                elif in_frontmatter:
                    in_frontmatter = False
                    frontmatter_closed = True
                continue
            if in_code or in_frontmatter:
                continue
            if len(line) > 80 and not line.startswith("|"):
                violations.append((i, len(line), line[:60]))
        assert violations == [], f"Lines exceeding 80 chars: {violations}"
