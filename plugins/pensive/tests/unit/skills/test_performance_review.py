"""Content tests for performance-review kuva-visualization module.

Verifies that the kuva integration added in 2026-05 is present
and correctly wired:
  - kuva-visualization.md module exists with substance
  - install command documented
  - criterion, pytest-benchmark, and ad-hoc patterns covered
  - terminal output option documented
  - proof-of-work evidence guidance present
  - SKILL.md references the module in frontmatter and body
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SKILL_DIR = Path(__file__).parents[3] / "skills" / "performance-review"
_MODULE = _SKILL_DIR / "modules" / "kuva-visualization.md"
_SKILL = _SKILL_DIR / "SKILL.md"


class TestKuvaVisualizationModule:
    """Feature: kuva-visualization module exists and covers key patterns.

    As a developer interpreting a performance-review report,
    I need the visualization module to show me how to turn benchmark
    numbers into charts so that before/after evidence is renderable
    without searching external docs.
    """

    @pytest.fixture
    def content(self) -> str:
        return _MODULE.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_file_exists(self) -> None:
        """Given the kuva-visualization module was added
        Then the file must exist on disk."""
        assert _MODULE.exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_has_substance(self, content: str) -> None:
        """Given the module is meant to be load-worthy
        Then it must be at least 30 lines."""
        assert len(content.splitlines()) >= 30

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_install_command_present(self, content: str) -> None:
        """Given kuva is an external dependency
        Then the module must include the install command."""
        assert "cargo install kuva" in content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_criterion_pattern_documented(self, content: str) -> None:
        """Given Rust projects use criterion for benchmarks
        Then the module must cover criterion output."""
        assert "criterion" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_pytest_benchmark_pattern_documented(self, content: str) -> None:
        """Given Python projects use pytest-benchmark
        Then the module must cover pytest-benchmark JSON output."""
        assert "pytest" in content and "benchmark" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_terminal_output_documented(self, content: str) -> None:
        """Given reviewers may not want to write SVG files in CI
        Then the --terminal flag must be documented."""
        assert "--terminal" in content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_proof_of_work_guidance_present(self, content: str) -> None:
        """Given charts serve as proof-of-work evidence
        Then the module must explain when a chart satisfies [E1]/[E2]."""
        assert "proof-of-work" in content.lower() or "evidence" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_when_not_to_use_section_present(self, content: str) -> None:
        """Given kuva is not always the right tool
        Then the module must document when NOT to use it."""
        assert "When NOT to use" in content or "when not" in content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_kuva_github_url_present(self, content: str) -> None:
        """Given attribution and discoverability matter
        Then the module must reference the kuva GitHub repo."""
        assert "Psy-Fer/kuva" in content


class TestPerformanceReviewSkillWiring:
    """Feature: SKILL.md correctly references the kuva-visualization module.

    As a developer loading the performance-review skill progressively,
    I need the module to appear in frontmatter and body
    so that it is loadable on demand and discoverable without
    reading all supporting modules.
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return _SKILL.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_in_frontmatter(self, skill_content: str) -> None:
        """Given progressive loading uses the frontmatter modules list
        Then kuva-visualization.md must appear there."""
        assert "kuva-visualization.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_referenced_in_supporting_modules_section(
        self, skill_content: str
    ) -> None:
        """Given the Supporting Modules section lists loadable modules
        Then kuva-visualization.md must be mentioned there."""
        assert "kuva-visualization" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_verification_step_references_kuva(self, skill_content: str) -> None:
        """Given step 3 of Verification talks about before/after evidence
        Then it must reference kuva for the chart requirement."""
        assert "kuva" in skill_content.lower()
