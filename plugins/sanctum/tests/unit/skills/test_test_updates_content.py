"""Content assertion tests for test-updates skill modules.

Tests the content-test-discovery and content-test-templates modules
using the L1/L2 taxonomy defined in leyline:testing-quality-standards.
"""

import ast
import re
import textwrap
from pathlib import Path

import pytest


class TestContentTestDiscoveryModuleContent:
    """Feature: Content test discovery module detects execution markdown.

    As the test-updates workflow encountering markdown changes
    I want to correctly identify execution markdown needing tests
    So that behavioral instructions are never left untested.

    Level 1: Structural presence checks.
    Level 2: Code example validity.
    """

    @pytest.fixture
    def module_path(self) -> Path:
        return (
            Path(__file__).parents[3]
            / "skills"
            / "test-updates"
            / "modules"
            / "content-test-discovery.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        return module_path.read_text()

    # --- L1: Structural presence ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists_with_substance(self, module_path: Path) -> None:
        """Given the content test discovery module
        Then it must exist with substantial content."""
        assert module_path.exists()
        content = module_path.read_text()
        assert len(content.splitlines()) >= 40, "Module should be substantial"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_execution_markdown_detection(
        self, module_content: str
    ) -> None:
        """Given the module guides test discovery
        Then it must define what execution markdown is."""
        assert "execution markdown" in module_content.lower()
        assert "skills/" in module_content or "agents/" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_priority_reclassification(
        self, module_content: str
    ) -> None:
        """Given execution markdown is not low-priority docs
        Then the module must reclassify priorities."""
        content_lower = module_content.lower()
        assert "high" in content_lower
        assert "medium" in content_lower or "low" in content_lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_defines_when_to_skip(self, module_content: str) -> None:
        """Given not every markdown change needs tests
        Then the module must define skip conditions."""
        content_lower = module_content.lower()
        assert (
            "skip" in content_lower
            or "not required" in content_lower
            or "when not to" in content_lower
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_references_leyline_taxonomy(self, module_content: str) -> None:
        """Given this module implements the leyline taxonomy
        Then it must reference the canonical definition."""
        assert "content-assertion-levels" in module_content

    # --- L2: Code example validity ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_python_code_blocks_are_syntactically_valid(
        self, module_content: str
    ) -> None:
        """Given Python code blocks in the module
        When Claude copies them as detection logic
        Then every block must be valid Python syntax."""
        python_blocks = re.findall(
            r"```python\n(.*?)\n```",
            module_content,
            re.DOTALL | re.MULTILINE,
        )
        assert len(python_blocks) >= 1, "Module should contain Python examples"
        for i, block in enumerate(python_blocks):
            try:
                ast.parse(block)
            except SyntaxError as exc:
                pytest.fail(f"Python block #{i + 1} has invalid syntax: {exc}")


class TestContentTestTemplatesModuleContent:
    """Feature: Content test templates provide BDD scaffolding.

    As a test author writing content assertions
    I want ready-made BDD templates for each level
    So that I can quickly scaffold correct tests.

    Level 1: Structural presence checks.
    Level 2: Code example validity.
    """

    @pytest.fixture
    def module_path(self) -> Path:
        return (
            Path(__file__).parents[3]
            / "skills"
            / "test-updates"
            / "modules"
            / "generation"
            / "content-test-templates.md"
        )

    @pytest.fixture
    def module_content(self, module_path: Path) -> str:
        return module_path.read_text()

    # --- L1: Structural presence ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_exists_with_substance(self, module_path: Path) -> None:
        """Given the content test templates module
        Then it must exist with substantial content."""
        assert module_path.exists()
        content = module_path.read_text()
        assert len(content.splitlines()) >= 100, "Module should be substantial"

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "level",
        [
            "Level 1",
            "Level 2",
            "Level 3",
        ],
    )
    def test_module_provides_templates_for_all_levels(
        self, module_content: str, level: str
    ) -> None:
        """Given the module provides BDD scaffolding
        Then it must have templates for all three levels."""
        assert level in module_content, f"Missing template for '{level}'"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_includes_common_fixtures(self, module_content: str) -> None:
        """Given test templates share common patterns
        Then the module must document reusable fixtures."""
        assert "fixture" in module_content.lower()
        assert "skill_path" in module_content or "skill_content" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_module_references_leyline_taxonomy(self, module_content: str) -> None:
        """Given this module implements the leyline taxonomy
        Then it must reference the canonical definition."""
        assert "content-assertion-levels" in module_content

    # --- L2: Code example validity ---

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_python_code_blocks_are_syntactically_valid(
        self, module_content: str
    ) -> None:
        """Given Python code blocks serve as copy-paste templates
        When Claude uses them to scaffold tests
        Then every block must be valid Python syntax."""
        python_blocks = re.findall(
            r"```python\n(.*?)\n```",
            module_content,
            re.DOTALL | re.MULTILINE,
        )
        assert len(python_blocks) >= 3, "Module should contain templates for each level"
        for i, block in enumerate(python_blocks):
            # Dedent class-body fragments so they parse standalone
            dedented = textwrap.dedent(block)
            try:
                ast.parse(dedented)
            except SyntaxError as exc:
                pytest.fail(f"Python block #{i + 1} has invalid syntax: {exc}")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_templates_use_bdd_markers(self, module_content: str) -> None:
        """Given templates should follow BDD conventions
        Then they must include pytest BDD markers."""
        assert "@pytest.mark.bdd" in module_content
        assert "@pytest.mark.unit" in module_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_templates_use_given_when_then(self, module_content: str) -> None:
        """Given templates should follow BDD conventions
        Then docstrings must use Given/When/Then format."""
        assert "Given" in module_content
        assert "When" in module_content
        assert "Then" in module_content
