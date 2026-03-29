"""Tests for tech-tutorial skill structure and content.

Issue #176: Add tech-tutorial skill to scribe plugin

Validates that the skill file, module files, and plugin registration
all exist and contain the required fields and content. Follows the
BDD-style pattern used across skill tests in this project.
"""

from pathlib import Path

import pytest

MAX_PROSE_LINE_LENGTH = 80

SKILL_ROOT = Path(__file__).parents[3] / "skills" / "tech-tutorial"
MODULES_ROOT = SKILL_ROOT / "modules"
PLUGIN_JSON = Path(__file__).parents[3] / ".claude-plugin" / "plugin.json"


class TestTechTutorialSkillExists:
    """Feature: tech-tutorial skill files are present on disk.

    As a developer using the scribe plugin
    I want the tech-tutorial skill to be installed
    So that I can invoke it to write technical tutorials
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        """Path to the tech-tutorial SKILL.md."""
        return SKILL_ROOT / "SKILL.md"

    @pytest.fixture
    def outline_module(self) -> Path:
        """Path to the outline-structure module."""
        return MODULES_ROOT / "outline-structure.md"

    @pytest.fixture
    def code_examples_module(self) -> Path:
        """Path to the code-examples module."""
        return MODULES_ROOT / "code-examples.md"

    @pytest.fixture
    def progressive_complexity_module(self) -> Path:
        """Path to the progressive-complexity module."""
        return MODULES_ROOT / "progressive-complexity.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_exists(self, skill_path: Path) -> None:
        """Scenario: SKILL.md exists at the expected path.

        Given the scribe plugin
        When checking for the tech-tutorial skill
        Then SKILL.md should exist under skills/tech-tutorial/
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outline_structure_module_exists(self, outline_module: Path) -> None:
        """Scenario: outline-structure module exists.

        Given the tech-tutorial skill
        When checking for its modules
        Then outline-structure.md should exist under modules/
        """
        assert outline_module.exists(), (
            f"outline-structure.md not found at {outline_module}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_code_examples_module_exists(self, code_examples_module: Path) -> None:
        """Scenario: code-examples module exists.

        Given the tech-tutorial skill
        When checking for its modules
        Then code-examples.md should exist under modules/
        """
        assert code_examples_module.exists(), (
            f"code-examples.md not found at {code_examples_module}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_complexity_module_exists(
        self, progressive_complexity_module: Path
    ) -> None:
        """Scenario: progressive-complexity module exists.

        Given the tech-tutorial skill
        When checking for its modules
        Then progressive-complexity.md should exist under modules/
        """
        assert progressive_complexity_module.exists(), (
            f"progressive-complexity.md not found at {progressive_complexity_module}"
        )


class TestTechTutorialFrontmatter:
    """Feature: SKILL.md has valid YAML frontmatter.

    As a plugin loader
    I want the skill to declare its metadata
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load tech-tutorial SKILL.md content."""
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_frontmatter_delimiters(self, skill_content: str) -> None:
        """Scenario: File begins with YAML frontmatter.

        Given the tech-tutorial SKILL.md
        When reading the file
        Then it should begin with '---' frontmatter delimiters
        """
        assert skill_content.startswith("---"), (
            "SKILL.md must begin with YAML frontmatter"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_name_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares the skill name.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should contain 'name: tech-tutorial'
        """
        assert "name: tech-tutorial" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_category_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares a category.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should contain a 'category:' field
        """
        assert "category:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_tags_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares tags.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should contain a 'tags:' list
        """
        assert "tags:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_complexity_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares complexity.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should contain a 'complexity:' field
        """
        assert "complexity:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_estimated_tokens_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares estimated token count.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should contain an 'estimated_tokens:' field
        """
        assert "estimated_tokens:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_modules_list(self, skill_content: str) -> None:
        """Scenario: Frontmatter lists module dependencies.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should contain a 'modules:' list referencing
        the three required modules
        """
        assert "modules:" in skill_content
        assert "outline-structure" in skill_content
        assert "code-examples" in skill_content
        assert "progressive-complexity" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_scribe_slop_detector_dependency(self, skill_content: str) -> None:
        """Scenario: Skill declares slop-detector as a dependency.

        Given the tech-tutorial SKILL.md
        When reading the frontmatter
        Then it should list 'scribe:slop-detector' in dependencies
        """
        assert "scribe:slop-detector" in skill_content


class TestTechTutorialContent:
    """Feature: SKILL.md content covers required workflow sections.

    As a developer invoking the skill
    I want the skill to provide complete guidance
    So that I can produce a finished tutorial without gaps
    """

    @pytest.fixture
    def skill_content(self) -> str:
        """Load tech-tutorial SKILL.md content."""
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_when_to_use_section(self, skill_content: str) -> None:
        """Scenario: Skill documents when to use it.

        Given the tech-tutorial SKILL.md
        When reading the content
        Then it should include a 'When To Use' section
        """
        assert "When To Use" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_when_not_to_use_section(self, skill_content: str) -> None:
        """Scenario: Skill documents when NOT to use it.

        Given the tech-tutorial SKILL.md
        When reading the content
        Then it should include a 'When NOT To Use' section
        """
        assert "When NOT To Use" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_methodology_section(self, skill_content: str) -> None:
        """Scenario: Skill provides a step-by-step methodology.

        Given the tech-tutorial SKILL.md
        When reading the content
        Then it should include a 'Methodology' section
        """
        assert "Methodology" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_slop_detector_invocation(self, skill_content: str) -> None:
        """Scenario: Skill directs user to run slop detector.

        Given the tech-tutorial SKILL.md
        When reading the methodology
        Then it should reference Skill(scribe:slop-detector)
        """
        assert "scribe:slop-detector" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_quality_gate_checklist(self, skill_content: str) -> None:
        """Scenario: Skill provides a quality gate checklist.

        Given the tech-tutorial SKILL.md
        When reading the content
        Then it should contain checkbox items for quality verification
        """
        assert "[ ]" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_exit_criteria_section(self, skill_content: str) -> None:
        """Scenario: Skill defines exit criteria.

        Given the tech-tutorial SKILL.md
        When reading the content
        Then it should include an 'Exit Criteria' section
        """
        assert "Exit Criteria" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_required_todowrite_items(self, skill_content: str) -> None:
        """Scenario: Skill lists required TodoWrite tracking items.

        Given the tech-tutorial SKILL.md
        When reading the content
        Then it should define 'tech-tutorial:' prefixed TodoWrite items
        """
        assert "tech-tutorial:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_all_three_modules(self, skill_content: str) -> None:
        """Scenario: Skill body references all three modules.

        Given the tech-tutorial SKILL.md
        When reading the module reference section
        Then it should point to outline-structure, code-examples,
        and progressive-complexity
        """
        assert "outline-structure" in skill_content
        assert "code-examples" in skill_content
        assert "progressive-complexity" in skill_content


class TestModuleContent:
    """Feature: Module files contain required guidance content.

    As a developer loading a module mid-skill
    I want each module to define its scope
    So that it provides focused guidance on one aspect of tutorial writing
    """

    @pytest.fixture
    def outline_content(self) -> str:
        """Load outline-structure module content."""
        return (MODULES_ROOT / "outline-structure.md").read_text()

    @pytest.fixture
    def code_examples_content(self) -> str:
        """Load code-examples module content."""
        return (MODULES_ROOT / "code-examples.md").read_text()

    @pytest.fixture
    def progressive_content(self) -> str:
        """Load progressive-complexity module content."""
        return (MODULES_ROOT / "progressive-complexity.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outline_module_has_frontmatter(self, outline_content: str) -> None:
        """Scenario: outline-structure module has YAML frontmatter.

        Given the outline-structure module
        When reading the file
        Then it should begin with YAML frontmatter
        """
        assert outline_content.startswith("---")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outline_module_covers_section_order(self, outline_content: str) -> None:
        """Scenario: outline-structure covers section ordering.

        Given the outline-structure module
        When reading the content
        Then it should cover section ordering or prerequisites
        """
        content_lower = outline_content.lower()
        assert "section" in content_lower or "prerequisite" in content_lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_code_examples_module_has_frontmatter(
        self, code_examples_content: str
    ) -> None:
        """Scenario: code-examples module has YAML frontmatter.

        Given the code-examples module
        When reading the file
        Then it should begin with YAML frontmatter
        """
        assert code_examples_content.startswith("---")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_code_examples_covers_snippet_testing(
        self, code_examples_content: str
    ) -> None:
        """Scenario: code-examples module requires testing snippets.

        Given the code-examples module
        When reading the content
        Then it should mention running or testing code
        """
        content_lower = code_examples_content.lower()
        assert (
            "test" in content_lower
            or "run" in content_lower
            or "verify" in content_lower
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_complexity_module_has_frontmatter(
        self, progressive_content: str
    ) -> None:
        """Scenario: progressive-complexity module has YAML frontmatter.

        Given the progressive-complexity module
        When reading the file
        Then it should begin with YAML frontmatter
        """
        assert progressive_content.startswith("---")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_complexity_covers_minimal_example(
        self, progressive_content: str
    ) -> None:
        """Scenario: progressive-complexity guides starting minimal.

        Given the progressive-complexity module
        When reading the content
        Then it should discuss starting with a minimal example
        """
        content_lower = progressive_content.lower()
        assert "minimal" in content_lower or "baseline" in content_lower


class TestPluginRegistration:
    """Feature: tech-tutorial skill is registered in plugin.json.

    As the plugin loader
    I want to discover the tech-tutorial skill from plugin.json
    So that it can be invoked via Skill(scribe:tech-tutorial)
    """

    @pytest.fixture
    def plugin_json_content(self) -> str:
        """Load plugin.json content."""
        return PLUGIN_JSON.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_plugin_json_references_tech_tutorial(
        self, plugin_json_content: str
    ) -> None:
        """Scenario: plugin.json lists the tech-tutorial skill.

        Given the scribe plugin.json
        When reading the skills list
        Then it should contain a reference to tech-tutorial
        """
        assert "tech-tutorial" in plugin_json_content


class TestProseCompliance:
    """Feature: Skill and module files follow 80-char prose rules.

    As a reviewer
    I want all skill files to comply with markdown formatting rules
    So that git diffs remain clean and readable
    """

    def _check_line_lengths(self, content: str, filename: str) -> list:
        """Return lines exceeding 80 chars, skipping exempt content."""
        in_code = False
        violations = []
        for i, line in enumerate(content.split("\n"), 1):
            if line.startswith("```"):
                in_code = not in_code
                continue
            if not in_code and len(line) > MAX_PROSE_LINE_LENGTH:
                # Skip tables, frontmatter separators, and bare URLs
                stripped = line.strip()
                if stripped.startswith("|") or stripped == "---":
                    continue
                if stripped.startswith("http://") or stripped.startswith("https://"):
                    continue
                violations.append((i, len(line), line[:60]))
        return violations

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_prose_under_80_chars(self) -> None:
        """Scenario: SKILL.md prose lines are 80 chars or fewer.

        Given the tech-tutorial SKILL.md
        When checking line lengths outside code blocks and tables
        Then no prose line should exceed 80 characters
        """
        content = (SKILL_ROOT / "SKILL.md").read_text()
        violations = self._check_line_lengths(content, "SKILL.md")
        assert violations == [], f"Lines exceeding 80 chars: {violations}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outline_module_prose_under_80_chars(self) -> None:
        """Scenario: outline-structure.md prose lines under 80 chars.

        Given the outline-structure module
        When checking line lengths
        Then no prose line should exceed 80 characters
        """
        content = (MODULES_ROOT / "outline-structure.md").read_text()
        violations = self._check_line_lengths(content, "outline-structure.md")
        assert violations == [], f"Lines exceeding 80 chars: {violations}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_code_examples_module_prose_under_80_chars(self) -> None:
        """Scenario: code-examples.md prose lines under 80 chars.

        Given the code-examples module
        When checking line lengths
        Then no prose line should exceed 80 characters
        """
        content = (MODULES_ROOT / "code-examples.md").read_text()
        violations = self._check_line_lengths(content, "code-examples.md")
        assert violations == [], f"Lines exceeding 80 chars: {violations}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_complexity_prose_under_80_chars(self) -> None:
        """Scenario: progressive-complexity.md prose lines under 80 chars.

        Given the progressive-complexity module
        When checking line lengths
        Then no prose line should exceed 80 characters
        """
        content = (MODULES_ROOT / "progressive-complexity.md").read_text()
        violations = self._check_line_lengths(content, "progressive-complexity.md")
        assert violations == [], f"Lines exceeding 80 chars: {violations}"


class TestNoSlopInSkillFiles:
    """Feature: Skill files are free of tier-1 slop words.

    As a documentation reviewer
    I want the skill files themselves to be clean
    So that the tutorial skill practices what it teaches
    """

    TIER1_WORDS = [
        "seamless",
        "robust",
        "comprehensive",
        "actionable",
        "leverage",
        "leveraging",
        "delve",
        "multifaceted",
        "streamline",
    ]

    def _find_slop(self, content: str) -> list:
        """Return tier-1 slop words found in content."""
        found = []
        content_lower = content.lower()
        for word in self.TIER1_WORDS:
            if word in content_lower:
                # Don't flag words inside code blocks (tables, etc.)
                # Simple heuristic: check plain text lines only
                for line in content.split("\n"):
                    if line.startswith("|") or line.startswith("```"):
                        continue
                    if word in line.lower():
                        found.append(word)
                        break
        return found

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_no_tier1_slop(self) -> None:
        """Scenario: SKILL.md contains no tier-1 slop words.

        Given the tech-tutorial SKILL.md
        When scanning for tier-1 slop words
        Then none should be present in prose lines
        """
        content = (SKILL_ROOT / "SKILL.md").read_text()
        found = self._find_slop(content)
        assert found == [], f"Tier-1 slop words found in SKILL.md: {found}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outline_module_no_tier1_slop(self) -> None:
        """Scenario: outline-structure.md has no tier-1 slop.

        Given the outline-structure module
        When scanning for tier-1 slop words
        Then none should appear in prose lines
        """
        content = (MODULES_ROOT / "outline-structure.md").read_text()
        found = self._find_slop(content)
        assert found == [], f"Tier-1 slop words in outline-structure.md: {found}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_code_examples_module_no_tier1_slop(self) -> None:
        """Scenario: code-examples.md has no tier-1 slop.

        Given the code-examples module
        When scanning for tier-1 slop words
        Then none should appear in prose lines
        """
        content = (MODULES_ROOT / "code-examples.md").read_text()
        found = self._find_slop(content)
        assert found == [], f"Tier-1 slop words in code-examples.md: {found}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_progressive_complexity_module_no_tier1_slop(self) -> None:
        """Scenario: progressive-complexity.md has no tier-1 slop.

        Given the progressive-complexity module
        When scanning for tier-1 slop words
        Then none should appear in prose lines
        """
        content = (MODULES_ROOT / "progressive-complexity.md").read_text()
        found = self._find_slop(content)
        assert found == [], f"Tier-1 slop words in progressive-complexity.md: {found}"
