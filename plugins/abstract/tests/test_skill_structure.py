"""BDD-style tests for skill structure validation.

These tests verify that skills follow Claude Code documentation best practices
for descriptions, triggers, and conflict avoidance.
"""

import re
from pathlib import Path

import pytest

from abstract.frontmatter import FrontmatterProcessor


class TestSkillDescriptionBestPractices:
    """Feature: Skill descriptions follow Claude Code best practices.

    As a plugin developer
    I want skill descriptions to be clear and discoverable
    So that Claude can correctly identify when to use each skill
    """

    @pytest.fixture
    def skills_dir(self):
        """Return the skills directory path."""
        return Path(__file__).parent.parent / "skills"

    @pytest.fixture
    def skill_files(self, skills_dir):
        """Find all user-facing skill files in the plugin.

        Excludes:
        - Module files (in modules/ directories) - internal components
        - Example files (in examples/ directories) - documentation samples
        - Files starting with underscore - private components
        """
        skill_files = []
        exclude_dirs = {"modules", "examples", "__pycache__"}

        for skill_path in skills_dir.rglob("*.md"):
            # Skip if any parent directory is in exclude list
            parts = skill_path.relative_to(skills_dir).parts
            if any(part in exclude_dirs or part.startswith("_") for part in parts[:-1]):
                continue
            # Include SKILL.md files and standalone skill files
            if skill_path.name == "SKILL.md" or skill_path.suffix == ".md":
                skill_files.append(skill_path)

        return skill_files

    def test_skill_description_includes_what_it_does(self, skill_files) -> None:
        """Scenario: Skill description explains what the skill does.

        Given a skill file with frontmatter
        When I read the description field
        Then it should contain action verbs describing capabilities
        """
        action_patterns = [
            r"\b(validate|check|analyze|create|build|generate|evaluate|test|review|guide|help|provide|decision|framework|implement|optimize|manage|configure|design|develop|enable|ensure|enforce|monitor|track|audit|assess)\b",
        ]

        for skill_file in skill_files:
            if not skill_file.exists():
                continue
            content = skill_file.read_text()
            result = FrontmatterProcessor.parse(content, required_fields=["name"])

            if not result.is_valid or "description" not in result.parsed:
                continue

            description = result.parsed["description"].lower()
            has_action = any(
                re.search(pattern, description, re.IGNORECASE)
                for pattern in action_patterns
            )

            desc_preview = result.parsed["description"][:100]
            assert has_action, (
                f"Skill '{skill_file.name}' description should include "
                f"action verbs. Current: {desc_preview}..."
            )

    def test_skill_description_includes_when_to_use(self, skill_files) -> None:
        """Scenario: Skill description explains when to use the skill.

        Given a skill file with frontmatter
        When I read the description field
        Then it should contain trigger phrases like "Use when" or "Use for"
        """
        trigger_patterns = [
            r"use when",
            r"use for",
            r"use this",
            r"trigger",
            r"activate",
            r"invoke",
        ]

        for skill_file in skill_files:
            if not skill_file.exists():
                continue
            content = skill_file.read_text()
            result = FrontmatterProcessor.parse(content, required_fields=["name"])

            if not result.is_valid or "description" not in result.parsed:
                continue

            description = result.parsed["description"].lower()
            has_trigger = any(
                re.search(pattern, description, re.IGNORECASE)
                for pattern in trigger_patterns
            )

            desc_preview = result.parsed["description"][:100]
            assert has_trigger, (
                f"Skill '{skill_file.name}' description should include "
                f"trigger phrases. Current: {desc_preview}..."
            )

    def test_skill_description_not_too_vague(self, skill_files) -> None:
        """Scenario: Skill description is not overly vague.

        Given a skill file with frontmatter
        When I check the description length
        Then it should be at least 50 characters to be meaningful
        """
        min_description_length = 50

        for skill_file in skill_files:
            if not skill_file.exists():
                continue
            content = skill_file.read_text()
            result = FrontmatterProcessor.parse(content, required_fields=["name"])

            if not result.is_valid or "description" not in result.parsed:
                continue

            description = result.parsed["description"]

            desc_len = len(description)
            assert desc_len >= min_description_length, (
                f"Skill '{skill_file.name}' description too short "
                f"({desc_len} chars). Minimum: {min_description_length}."
            )


class TestSkillConflictAvoidance:
    """Feature: Skills have distinct descriptions to avoid conflicts.

    As a plugin developer
    I want skills to have unique trigger terms
    So that Claude doesn't get confused between similar skills
    """

    @pytest.fixture
    def skills_dir(self):
        """Return the skills directory path."""
        return Path(__file__).parent.parent / "skills"

    @pytest.fixture
    def all_skill_descriptions(self, skills_dir):
        """Extract descriptions from all skills."""
        descriptions = {}
        for skill_path in skills_dir.rglob("*.md"):
            content = skill_path.read_text()
            result = FrontmatterProcessor.parse(content, required_fields=["name"])
            if result.is_valid and "description" in result.parsed:
                name = result.parsed.get("name", skill_path.stem)
                descriptions[name] = result.parsed["description"]
        return descriptions

    def test_skills_have_distinct_trigger_terms(self, all_skill_descriptions) -> None:
        """Scenario: Skills don't share identical trigger phrases.

        Given multiple skills in the plugin
        When I compare their trigger phrases
        Then each skill should have unique key terms
        """

        # Extract key terms from each description
        def extract_key_terms(description):
            # Remove common words and extract meaningful terms
            stop_words = {
                "the",
                "a",
                "an",
                "is",
                "are",
                "for",
                "to",
                "and",
                "or",
                "this",
                "that",
                "when",
                "use",
            }
            words = re.findall(r"\b[a-z]{4,}\b", description.lower())
            return set(words) - stop_words

        skill_terms = {
            name: extract_key_terms(desc)
            for name, desc in all_skill_descriptions.items()
        }

        # Check for high overlap between skills
        skill_names = list(skill_terms.keys())
        for i, name1 in enumerate(skill_names):
            for name2 in skill_names[i + 1 :]:
                terms1 = skill_terms[name1]
                terms2 = skill_terms[name2]

                if not terms1 or not terms2:
                    continue

                overlap = terms1 & terms2
                overlap_ratio = len(overlap) / min(len(terms1), len(terms2))

                # Allow some overlap but flag very high similarity
                assert overlap_ratio < 0.8, (
                    f"Skills '{name1}' and '{name2}' have similar descriptions "
                    f"(80%+ overlap). Overlapping: {overlap}"
                )


class TestHookScopeGuideSkill:
    """Feature: Hook scope guide skill follows best practices.

    As a plugin developer
    I want the hook-scope-guide skill to be well-structured
    So that it helps users choose the right hook location
    """

    @pytest.fixture
    def skill_path(self):
        """Return path to the hook-scope-guide skill."""
        return Path(__file__).parent.parent / "skills" / "hook-scope-guide.md"

    def test_skill_exists(self, skill_path) -> None:
        """Scenario: Hook scope guide skill file exists.

        Given the abstract plugin
        When I look for the hook-scope-guide skill
        Then it should exist in the skills directory
        """
        assert skill_path.exists(), f"hook-scope-guide.md not found at {skill_path}"

    def test_skill_has_valid_frontmatter(self, skill_path) -> None:
        """Scenario: Skill has valid YAML frontmatter.

        Given the hook-scope-guide skill file
        When I parse its frontmatter
        Then it should have name and description fields
        """
        content = skill_path.read_text()
        required = ["name", "description"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        assert result.is_valid, f"Validation failed: {result.parse_error}"
        assert result.parsed["name"] == "hook-scope-guide"

    def test_skill_description_differentiates_from_hookify(self, skill_path) -> None:
        """Scenario: Description clearly differentiates from hookify.

        Given the hook-scope-guide skill
        When I read its description
        Then it should mention WHERE to put hooks (not HOW to write them)
        And it should cross-reference hookify for syntax questions
        """
        content = skill_path.read_text()
        required = ["name", "description"]
        result = FrontmatterProcessor.parse(content, required_fields=required)

        description = result.parsed["description"].lower()

        # Should focus on WHERE/location
        location_terms = [
            "where",
            "scope",
            "location",
            "plugin",
            "project",
            "global",
        ]
        has_location_focus = any(term in description for term in location_terms)
        assert has_location_focus, "Description should focus on WHERE"

        # Should cross-reference hookify for HOW
        has_hookify = "hookify" in description
        has_rules = "writing-rules" in description
        assert has_hookify or has_rules, "Should cross-reference hookify"

    def test_skill_has_distinct_triggers(self, skill_path) -> None:
        """Scenario: Skill has triggers distinct from other hook skills.

        Given the hook-scope-guide skill
        When I read its triggers
        Then they should not overlap with hookify or hook-development triggers
        """
        content = skill_path.read_text()
        result = FrontmatterProcessor.parse(content, required_fields=["name"])

        triggers = result.parsed.get("triggers", [])

        # These are hookify triggers that should NOT appear
        hookify_triggers = [
            "create a hook",
            "write a hook",
            "hook rule",
            "hookify rule",
        ]

        for trigger in triggers:
            trigger_lower = trigger.lower()
            for hookify_trigger in hookify_triggers:
                assert hookify_trigger not in trigger_lower, (
                    f"Trigger '{trigger}' overlaps with hookify. "
                    f"Use distinct terms like 'hook scope', 'hook location', etc."
                )

    def test_skill_content_covers_three_scopes(self, skill_path) -> None:
        """Scenario: Skill content covers all three hook scopes.

        Given the hook-scope-guide skill
        When I read its content
        Then it should explain plugin, project, and global hooks
        """
        content = skill_path.read_text()

        scopes = ["plugin hook", "project hook", "global hook"]

        for scope in scopes:
            assert (
                scope.lower() in content.lower()
            ), f"Skill should cover '{scope}' scope"

    def test_skill_includes_decision_framework(self, skill_path) -> None:
        """Scenario: Skill includes a decision framework.

        Given the hook-scope-guide skill
        When I read its content
        Then it should include decision questions or a decision tree
        """
        content = skill_path.read_text()

        decision_indicators = [
            "decision",
            "question",
            "who needs",
            "should this",
            "when to use",
        ]

        has_decision_content = any(
            indicator in content.lower() for indicator in decision_indicators
        )

        assert has_decision_content, "Skill should include decision framework questions"
