"""Tests for session-to-post skill structure and content.

Validates that the skill file, module files, command file, and plugin
registration all exist and contain the required fields. Follows the
BDD-style pattern used across skill tests in this project.
"""

from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parents[3] / "skills" / "session-to-post"
MODULES_ROOT = SKILL_ROOT / "modules"
COMMANDS_ROOT = Path(__file__).parents[3] / "commands"
OPENPACKAGE = Path(__file__).parents[3] / "openpackage.yml"


class TestSessionToPostSkillExists:
    """Feature: session-to-post skill files are present on disk.

    As a developer using the scribe plugin
    I want the session-to-post skill to be installed
    So that I can convert sessions into blog posts
    """

    @pytest.fixture
    def skill_path(self) -> Path:
        return SKILL_ROOT / "SKILL.md"

    @pytest.fixture
    def session_extraction_module(self) -> Path:
        return MODULES_ROOT / "session-extraction.md"

    @pytest.fixture
    def narrative_structure_module(self) -> Path:
        return MODULES_ROOT / "narrative-structure.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_md_exists(self, skill_path: Path) -> None:
        """Scenario: SKILL.md exists at the expected path.

        Given the scribe plugin
        When checking for the session-to-post skill
        Then SKILL.md should exist under skills/session-to-post/
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_session_extraction_module_exists(
        self, session_extraction_module: Path
    ) -> None:
        """Scenario: session-extraction module exists.

        Given the session-to-post skill
        When checking for its modules
        Then session-extraction.md should exist under modules/
        """
        assert session_extraction_module.exists(), (
            f"session-extraction.md not found at {session_extraction_module}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_narrative_structure_module_exists(
        self, narrative_structure_module: Path
    ) -> None:
        """Scenario: narrative-structure module exists.

        Given the session-to-post skill
        When checking for its modules
        Then narrative-structure.md should exist under modules/
        """
        assert narrative_structure_module.exists(), (
            f"narrative-structure.md not found at {narrative_structure_module}"
        )


class TestSessionToPostFrontmatter:
    """Feature: SKILL.md has valid YAML frontmatter.

    As a plugin loader
    I want the skill to declare its metadata
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_frontmatter_delimiters(self, skill_content: str) -> None:
        """Scenario: File begins with YAML frontmatter.

        Given the session-to-post SKILL.md
        When reading the file
        Then it should begin with '---' frontmatter delimiters
        """
        assert skill_content.startswith("---")

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_name_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares the skill name.

        Given the session-to-post SKILL.md
        When reading the frontmatter
        Then it should contain 'name: session-to-post'
        """
        assert "name: session-to-post" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_category_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares a category."""
        assert "category:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_tags_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares tags."""
        assert "tags:" in skill_content
        assert "blog" in skill_content
        assert "marketing" in skill_content
        assert "session-capture" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_complexity_field(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares complexity."""
        assert "complexity:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_estimated_tokens(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares token budget."""
        assert "estimated_tokens:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_modules_list(self, skill_content: str) -> None:
        """Scenario: Frontmatter lists both modules."""
        assert "modules:" in skill_content
        assert "session-extraction" in skill_content
        assert "narrative-structure" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_dependencies(self, skill_content: str) -> None:
        """Scenario: Frontmatter declares scribe dependencies."""
        assert "dependencies:" in skill_content
        assert "scribe:slop-detector" in skill_content


class TestSessionToPostIntegrationPoints:
    """Feature: Skill documents integration with other plugins.

    As a content creator
    I want session-to-post to integrate with scry and imbue
    So that posts include recordings and verified claims
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_scry_vhs(self, skill_content: str) -> None:
        """Scenario: Skill references terminal recording.

        Given the session-to-post skill
        When reading integration points
        Then it should reference scry:vhs-recording
        """
        assert "scry:vhs-recording" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_scry_browser(self, skill_content: str) -> None:
        """Scenario: Skill references browser recording.

        Given the session-to-post skill
        When reading integration points
        Then it should reference scry:browser-recording
        """
        assert "scry:browser-recording" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_scry_composition(self, skill_content: str) -> None:
        """Scenario: Skill references media composition.

        Given the session-to-post skill
        When reading integration points
        Then it should reference scry:media-composition
        """
        assert "scry:media-composition" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_proof_of_work(self, skill_content: str) -> None:
        """Scenario: Skill references proof-of-work for claims.

        Given the session-to-post skill
        When reading integration points
        Then it should reference imbue:proof-of-work
        """
        assert "imbue:proof-of-work" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_catchup(self, skill_content: str) -> None:
        """Scenario: Skill references catchup for change summaries.

        Given the session-to-post skill
        When reading integration points
        Then it should reference imbue:catchup
        """
        assert "imbue:catchup" in skill_content


class TestSessionToPostContent:
    """Feature: Skill body covers the full methodology.

    As a user following the skill
    I want clear steps from extraction to output
    So that I produce a quality post every time
    """

    @pytest.fixture
    def skill_content(self) -> str:
        return (SKILL_ROOT / "SKILL.md").read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_extraction_step(self, skill_content: str) -> None:
        """Scenario: Methodology includes session extraction."""
        assert "Extract Session Context" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_story_step(self, skill_content: str) -> None:
        """Scenario: Methodology includes story identification."""
        assert "Identify the Story" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_draft_step(self, skill_content: str) -> None:
        """Scenario: Methodology includes drafting."""
        assert "Draft the Post" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_quality_gate(self, skill_content: str) -> None:
        """Scenario: Methodology includes quality gate."""
        assert "Quality Gate" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_testing_section_in_template(self, skill_content: str) -> None:
        """Scenario: Post template includes how-we-tested section.

        Given the session-to-post skill
        When reading the draft template
        Then it should include a testing narrative section
        """
        assert "How We Tested" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_has_example(self, skill_content: str) -> None:
        """Scenario: Skill includes a concrete example."""
        assert "## Example" in skill_content


class TestSessionToPostCommand:
    """Feature: A command file exists to invoke the skill.

    As a user
    I want a /session-to-post slash command
    So that I can invoke the skill quickly
    """

    @pytest.fixture
    def command_path(self) -> Path:
        return COMMANDS_ROOT / "session-to-post.md"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_file_exists(self, command_path: Path) -> None:
        """Scenario: Command file exists.

        Given the scribe plugin
        When checking for the session-to-post command
        Then session-to-post.md should exist under commands/
        """
        assert command_path.exists(), f"Command not found at {command_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_references_skill(self, command_path: Path) -> None:
        """Scenario: Command invokes the skill.

        Given the session-to-post command
        When reading its content
        Then it should reference Skill(scribe:session-to-post)
        """
        content = command_path.read_text()
        assert "scribe:session-to-post" in content


class TestSessionToPostRegistration:
    """Feature: Skill and command registered in openpackage.yml.

    As a plugin loader
    I want session-to-post in the package manifest
    So that the system discovers and loads it
    """

    @pytest.fixture
    def openpackage_content(self) -> str:
        return OPENPACKAGE.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_registered(self, openpackage_content: str) -> None:
        """Scenario: Skill listed in openpackage.yml skills."""
        assert "skills/session-to-post" in openpackage_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_registered(self, openpackage_content: str) -> None:
        """Scenario: Command listed in openpackage.yml commands."""
        assert "commands/session-to-post.md" in openpackage_content
