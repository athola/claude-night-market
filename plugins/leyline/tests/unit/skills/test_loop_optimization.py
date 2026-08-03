"""Tests for loop-optimization skill structure and content.

Validates the shared decision-rule module contains the hand-vs-compiler
rule, the per-technique reality table, the two benchmark traps, and a
falsifiable Exit Criteria section.

Following BDD principles with Given/When/Then scenarios.
"""

from pathlib import Path

import pytest

MAX_PROSE_LINE_LENGTH = 80


class TestLoopOptimizationSkillStructure:
    """Feature: loop-optimization skill provides a shared decision rule.

    As a reviewer or author of a hot loop
    I want a canonical hand-vs-compiler reference
    So that manual loop transforms are applied only when they pay
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the loop-optimization skill."""
        return Path(__file__).parents[3] / "skills" / "loop-optimization" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path: Path) -> str:
        """Load the loop-optimization skill content."""
        return skill_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_path: Path) -> None:
        """Scenario: Skill file exists at expected location.

        Given the leyline plugin
        When checking for the loop-optimization skill
        Then SKILL.md should exist
        """
        assert skill_path.exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_content: str) -> None:
        """Scenario: Skill has valid frontmatter with its name.

        Given the loop-optimization SKILL.md
        When reading the file
        Then it should open with YAML frontmatter naming the skill
        """
        assert skill_content.startswith("---")
        assert "name: loop-optimization" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Frontmatter includes required metadata.

        Given the loop-optimization SKILL.md
        When reading the frontmatter
        Then category, tags, complexity, and estimated_tokens are present
        """
        assert "category:" in skill_content
        assert "tags:" in skill_content
        assert "complexity:" in skill_content
        assert "estimated_tokens:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_trust_the_compiler_rule(self, skill_content: str) -> None:
        """Scenario: Skill states the compiled-language default.

        Given the loop-optimization SKILL.md
        When reading the decision rule
        Then it tells compiled-language users to trust the compiler for
        unrolling, LICM, and strength reduction
        """
        lower = skill_content.lower()
        assert "trust the compiler" in lower
        assert "strength reduction" in lower
        assert "invariant code motion" in lower or "licm" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_per_technique_table(self, skill_content: str) -> None:
        """Scenario: Skill includes the per-technique reality table.

        Given the loop-optimization SKILL.md
        When reading the technique reality section
        Then all five techniques and a when-NOT column are present
        """
        lower = skill_content.lower()
        assert "unrolling" in lower
        assert "vectoriz" in lower
        assert "fusion" in lower
        assert "hoisting" in lower or "licm" in lower
        assert "when not" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_python_regime(self, skill_content: str) -> None:
        """Scenario: Skill calls out the Python-specific levers.

        Given the loop-optimization SKILL.md
        When reading the Python guidance
        Then it names hoisting/NumPy as the levers and warns against
        hand-unrolling
        """
        lower = skill_content.lower()
        assert "python" in lower
        assert "numpy" in lower
        assert "hoist" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_both_benchmark_traps(self, skill_content: str) -> None:
        """Scenario: Skill documents the two invalidating traps.

        Given the loop-optimization SKILL.md
        When reading the traps section
        Then the synthetic-benchmark trap and emitted-is-not-executed
        trap are both present
        """
        lower = skill_content.lower()
        assert "synthetic" in lower
        assert "production-distribution" in lower
        assert "emitted is not executed" in lower or "does not mean" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_documents_branch_elimination_technique(self, skill_content: str) -> None:
        """Scenario: Skill covers branch elimination as a distinct lever.

        Given the loop-optimization SKILL.md
        When reading the technique guidance
        Then branchless/branch-elimination appears alongside the loop
        transforms, because control flow is a separate axis from loop
        structure and the compiler will not perform this rewrite
        """
        lower = skill_content.lower()
        assert "branchless" in lower or "branch elimination" in lower
        assert "mispredict" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_branchless_scoped_to_unpredictable_data(self, skill_content: str) -> None:
        """Scenario: Skill scopes branchless to data-dependent branches.

        Given the loop-optimization SKILL.md
        When reading the branchless guidance
        Then it restricts the technique to branches on unpredictable
        data and states that predictable branches are already cheap
        """
        lower = skill_content.lower()
        assert "unpredictable" in lower
        assert "predictable" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_branchless_documents_worst_case_tradeoff(self, skill_content: str) -> None:
        """Scenario: Skill states branchless trades best for worst case.

        Given the loop-optimization SKILL.md
        When reading the branchless guidance
        Then it records that the technique flattens cost rather than
        reducing it, and can be slower when the branch predicts well
        """
        lower = skill_content.lower()
        assert "selectivity" in lower
        assert "worst case" in lower or "worst-case" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_exit_criteria(self, skill_content: str) -> None:
        """Scenario: Skill has a falsifiable Exit Criteria section.

        Given the loop-optimization SKILL.md
        When reading the end of the file
        Then an Exit Criteria checklist is present
        """
        assert "## Exit Criteria" in skill_content
        assert "- [ ]" in skill_content


class TestLoopOptimizationProseCompliance:
    """Feature: Skill practices the repo's formatting rules.

    As a documentation consumer
    I want the reference to follow 80-char wrapping
    So that it stays a credible, diff-friendly reference
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load SKILL.md content."""
        path = Path(__file__).parents[3] / "skills" / "loop-optimization" / "SKILL.md"
        return path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_prose_under_80_chars(self, skill_content: str) -> None:
        """Scenario: SKILL.md prose lines stay under 80 chars.

        Given the loop-optimization SKILL.md
        When checking line lengths outside code blocks and tables
        Then all prose lines should be 80 chars or fewer
        """
        in_code = False
        in_frontmatter = False
        frontmatter_closed = False
        violations = []
        for i, line in enumerate(skill_content.split("\n"), 1):
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
            if not in_code and not in_frontmatter and len(line) > MAX_PROSE_LINE_LENGTH:
                if line.startswith("|"):
                    continue
                violations.append((i, len(line), line[:60]))
        assert violations == [], f"Lines exceeding 80 chars: {violations}"
