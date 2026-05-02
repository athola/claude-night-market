"""BDD-style tests for skill structure validation.

These tests verify that skills follow Claude Code documentation best practices
for descriptions, triggers, and conflict avoidance.
"""

import json
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

        if not skill_files:
            pytest.skip(
                f"No skill files found under {skills_dir}. "
                "Skill structure tests require at least one skill markdown file."
            )

        return skill_files

    @pytest.mark.bdd
    def test_skill_description_includes_what_it_does(self, skill_files) -> None:
        """Scenario: Skill description explains what the skill does.

        Given a skill file with frontmatter
        When I read the description field
        Then it should contain action verbs describing capabilities
        """
        action_patterns = [
            r"\b(validate|check|analyze|create|build|generate|evaluate|test|review|guide|help|provide|decision|framework|implement|optimize|manage|configure|design|develop|enable|enforce|monitor|track|audit|assess|surface|select|curate|discover|identify|extract|process|transform|execute|coordinate|orchestrate|detect)\b",
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

    @pytest.mark.bdd
    def test_skill_description_includes_when_to_use(self, skill_files) -> None:
        """Scenario: Skill has trigger/usage information.

        Given a skill file with frontmatter
        When I read the description, triggers, or use_when fields
        Then at least one should contain trigger/usage information

        Note: Skills can specify triggers in:
        - description field (still supported; predates dedicated fields)
        - triggers field (introduced alongside Claude Code 2.1.0 skill
          frontmatter expansion)
        - use_when field (introduced alongside Claude Code 2.1.0 skill
          frontmatter expansion)

        Both old and new formats remain valid. Skills written before
        the triggers/use_when fields existed embed trigger information
        in their description. This test accepts either approach.
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

            # Check description (legacy format)
            description = result.parsed["description"].lower()
            has_trigger_in_desc = any(
                re.search(pattern, description, re.IGNORECASE)
                for pattern in trigger_patterns
            )

            # Check triggers field (new format)
            triggers = result.parsed.get("triggers", "")
            if isinstance(triggers, list):
                triggers = " ".join(triggers)
            has_triggers_field = bool(triggers)

            # Check use_when field (new format)
            use_when = result.parsed.get("use_when", "")
            has_use_when_field = bool(use_when)

            # Pass if ANY of these are present
            has_trigger_info = (
                has_trigger_in_desc or has_triggers_field or has_use_when_field
            )

            desc_preview = result.parsed["description"][:100]
            assert has_trigger_info, (
                f"Skill '{skill_file.name}' should have trigger information "
                f"(in description, triggers, or use_when field). Current description: {desc_preview}..."
            )

    @pytest.mark.bdd
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

    @pytest.mark.bdd
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
        """Return path to the hook-scope-guide skill SKILL.md."""
        return Path(__file__).parent.parent / "skills" / "hook-scope-guide" / "SKILL.md"

    @pytest.mark.bdd
    def test_skill_exists(self, skill_path) -> None:
        """Scenario: Hook scope guide skill file exists.

        Given the abstract plugin
        When I look for the hook-scope-guide skill
        Then it should exist in the skills directory
        """
        assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    @pytest.mark.bdd
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

    def test_skill_description_differentiates_from_hook_authoring(
        self, skill_path
    ) -> None:
        """Scenario: Description clearly differentiates from hook-authoring.

        Given the hook-scope-guide skill
        When I read its description
        Then it should mention WHERE to put hooks (not HOW to write them)
        And it should cross-reference hook-authoring for syntax questions
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

        # Should cross-reference hook-authoring for HOW
        has_hook_authoring = "hook-authoring" in description
        has_authoring_ref = "authoring" in description
        assert has_hook_authoring or has_authoring_ref, (
            "Should cross-reference hook-authoring"
        )

    @pytest.mark.bdd
    def test_skill_has_distinct_triggers(self, skill_path) -> None:
        """Scenario: Skill has triggers distinct from other hook skills.

        Given the hook-scope-guide skill
        When I read its triggers
        Then they should not overlap with hook-authoring or hook-development triggers
        """
        content = skill_path.read_text()
        result = FrontmatterProcessor.parse(content, required_fields=["name"])

        triggers = result.parsed.get("triggers", [])

        # These are hook-authoring triggers that should NOT appear
        authoring_triggers = [
            "create a hook",
            "write a hook",
            "hook rule",
            "authoring rule",
        ]

        for trigger in triggers:
            trigger_lower = trigger.lower()
            for authoring_trigger in authoring_triggers:
                assert authoring_trigger not in trigger_lower, (
                    f"Trigger '{trigger}' overlaps with hook-authoring. "
                    f"Use distinct terms like 'hook scope', 'hook location', etc."
                )

    @pytest.mark.bdd
    def test_skill_content_covers_three_scopes(self, skill_path) -> None:
        """Scenario: Skill content covers all three hook scopes.

        Given the hook-scope-guide skill
        When I read its content
        Then it should explain plugin, project, and global hooks
        """
        content = skill_path.read_text()

        scopes = ["plugin hook", "project hook", "global hook"]

        for scope in scopes:
            assert scope.lower() in content.lower(), (
                f"Skill should cover '{scope}' scope"
            )

    @pytest.mark.bdd
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


class TestHookAuthoringHttpHooks:
    """Feature: Hook-authoring skill teaches Claude to generate valid hook configs.

    As a skill interpreted by Claude Code for hook development guidance
    I want JSON examples to be valid and schema-compliant
    So that Claude produces working hook configurations when users ask.

    Level 2: Code examples parse as valid JSON with correct schema.
    Level 3: Decision framework covers all hook types, version refs are consistent.
    """

    @pytest.fixture
    def skill_path(self):
        return Path(__file__).parent.parent / "skills" / "hook-authoring" / "SKILL.md"

    @pytest.fixture
    def skill_content(self, skill_path):
        return skill_path.read_text()

    @pytest.fixture
    def json_code_blocks(self, skill_content):
        """Extract all ```json ... ``` code blocks from the skill."""
        return re.findall(r"```json\n(.*?)```", skill_content, re.DOTALL)

    # --- Level 2: Code example validity ---

    @pytest.mark.unit
    @pytest.mark.bdd
    def test_all_json_examples_parse_successfully(self, json_code_blocks):
        """Given all JSON code blocks in hook-authoring skill
        When Claude copies them as templates
        Then every block must be valid JSON (no syntax errors).
        """
        assert len(json_code_blocks) > 0, "Skill should contain JSON examples"
        for i, block in enumerate(json_code_blocks):
            try:
                json.loads(block)
            except json.JSONDecodeError as exc:
                pytest.fail(f"JSON block #{i + 1} is invalid: {exc}\n{block[:200]}")

    @pytest.mark.unit
    @pytest.mark.bdd
    def test_http_hook_example_has_correct_schema(self, json_code_blocks):
        """Given the HTTP hooks JSON example
        When Claude uses it as a template for generating hook configs
        Then it must have: event key, matcher, hooks array with type=http and url.

        This prevents Claude from teaching users to write malformed configs.
        """
        http_block = None
        for block in json_code_blocks:
            parsed = json.loads(block)
            # Find the block that contains type: http
            block_str = json.dumps(parsed)
            if '"type": "http"' in block_str:
                http_block = parsed
                break

        assert http_block is not None, "Skill must contain an HTTP hook JSON example"

        # Validate schema: must have an event key containing hook definitions
        event_keys = list(http_block.keys())
        assert len(event_keys) >= 1, "Must have at least one event key"

        hook_defs = http_block[event_keys[0]]
        assert isinstance(hook_defs, list), "Event value must be an array"

        first_def = hook_defs[0]
        assert "matcher" in first_def, "Hook definition must have a matcher"
        assert isinstance(first_def["matcher"], str), (
            "Matcher must be a string (not object)"
        )
        assert "hooks" in first_def, "Hook definition must have hooks array"

        hook = first_def["hooks"][0]
        assert hook["type"] == "http", "Hook type must be 'http'"
        assert "url" in hook, "HTTP hook must have a 'url' field"
        assert hook["url"].startswith("http"), "URL must start with http"

    @pytest.mark.unit
    @pytest.mark.bdd
    def test_command_hook_example_has_correct_schema(self, json_code_blocks):
        """Given the command hooks JSON example
        When Claude uses it as a template
        Then it must have: event key, matcher, hooks array with type=command.
        """
        cmd_block = None
        for block in json_code_blocks:
            parsed = json.loads(block)
            block_str = json.dumps(parsed)
            if '"type": "command"' in block_str:
                cmd_block = parsed
                break

        assert cmd_block is not None, "Skill must contain a command hook JSON example"

        event_keys = list(cmd_block.keys())
        hook_defs = cmd_block[event_keys[0]]
        first_def = hook_defs[0]

        hook = first_def["hooks"][0]
        assert hook["type"] == "command"
        assert "command" in hook, "Command hook must have a 'command' field"

    # --- Level 3: Behavioral contracts ---

    @pytest.mark.unit
    @pytest.mark.bdd
    def test_skill_covers_all_three_hook_types(self, skill_content):
        """Given the skill is Claude's reference for hook creation
        When a user asks 'how do I create a hook?'
        Then Claude must know about all three approaches (JSON, HTTP, SDK).
        """
        assert "JSON Hooks" in skill_content
        assert "HTTP Hooks" in skill_content
        assert "Python SDK" in skill_content or "SDK Hooks" in skill_content

    @pytest.mark.unit
    @pytest.mark.bdd
    def test_http_hooks_version_gate_matches_compatibility_docs(self, skill_content):
        """Given the skill references '2.1.63+' for HTTP hooks
        Then that version must also be documented in compatibility-features.md.

        This prevents Claude from recommending features for wrong versions.
        """
        # Extract version reference from HTTP hooks section
        http_section_match = re.search(r"HTTP Hooks.*?(\d+\.\d+\.\d+)", skill_content)
        assert http_section_match, "HTTP Hooks section must have a version reference"
        version = http_section_match.group(1)

        # Cross-reference against compatibility docs
        compat_path = (
            Path(__file__).parent.parent
            / "docs"
            / "compatibility"
            / "compatibility-features.md"
        )
        compat_content = compat_path.read_text()
        assert (
            f"### Claude Code {version}" in compat_content
            or f"{version}" in compat_content
        ), f"Version {version} referenced in skill but missing from compatibility docs"

    @pytest.mark.unit
    @pytest.mark.bdd
    def test_decision_guidance_distinguishes_http_use_cases(self, skill_content):
        """Given a user asks 'which hook type should I use?'
        When Claude reads the skill's decision guidance
        Then it must find distinct use-case criteria for HTTP vs command hooks.

        Without this, Claude can't make informed recommendations.
        """
        # HTTP hooks should have specific use-case guidance
        http_section = skill_content[skill_content.index("HTTP Hooks") :]
        http_section = http_section[: http_section.index("### Python SDK")]

        # Must provide criteria for WHEN to choose HTTP over command
        use_case_indicators = [
            "enterprise",
            "sandboxed",
            "centralized",
            "web service",
        ]
        found = [ind for ind in use_case_indicators if ind in http_section.lower()]
        min_indicators = 2
        assert len(found) >= min_indicators, (
            f"HTTP section needs distinct use-case criteria. "
            f"Found {found}, need at least {min_indicators} of {use_case_indicators}"
        )
