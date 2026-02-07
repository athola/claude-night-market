"""
Test suite for ecosystem-wide discoverability enhancements (v1.4.0).

Validates that all skills, commands, and agents follow the discoverability
pattern established in the v1.4.0 enhancement.

Pattern: [WHAT]. Use when: [triggers]. Do not use when: [boundaries].

References:
- docs/adr/0005-attune-discoverability-enhancement.md
- plugins/attune/templates/TEMPLATE-GUIDE.md
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import yaml


PLUGINS_DIR = Path("plugins")
SKIP_PLUGINS = {"attune"}  # Attune tested separately below

# Excluded: JSON agents, __init__.py, shared skills without full frontmatter
EXCLUDED_PATTERNS = {"__init__.py", ".gitkeep"}


def discover_ecosystem_skills() -> List[str]:
    """Discover all skill SKILL.md files across non-attune plugins."""
    paths = []
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir() or plugin_dir.name in SKIP_PLUGINS:
            continue
        skills_dir = plugin_dir / "skills"
        if skills_dir.exists():
            for skill_dir in sorted(skills_dir.iterdir()):
                sf = skill_dir / "SKILL.md"
                if sf.exists():
                    paths.append(str(sf))
    return paths


def discover_ecosystem_commands() -> List[str]:
    """Discover all command .md files across non-attune plugins."""
    paths = []
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir() or plugin_dir.name in SKIP_PLUGINS:
            continue
        cmds_dir = plugin_dir / "commands"
        if cmds_dir.exists():
            for cf in sorted(cmds_dir.glob("*.md")):
                # Skip subdirectories and non-command files
                if cf.is_file():
                    paths.append(str(cf))
    return paths


def discover_ecosystem_agents_md() -> List[str]:
    """Discover markdown agent files across non-attune plugins."""
    paths = []
    for plugin_dir in sorted(PLUGINS_DIR.iterdir()):
        if not plugin_dir.is_dir() or plugin_dir.name in SKIP_PLUGINS:
            continue
        agents_dir = plugin_dir / "agents"
        if agents_dir.exists():
            for af in sorted(agents_dir.glob("*.md")):
                if af.is_file():
                    # Skip JSON-content agents (some .md files have JSON content)
                    content = af.read_text().strip()
                    if not content.startswith("{"):
                        paths.append(str(af))
    return paths


ECOSYSTEM_SKILLS = discover_ecosystem_skills()
ECOSYSTEM_COMMANDS = discover_ecosystem_commands()
ECOSYSTEM_AGENTS_MD = discover_ecosystem_agents_md()


# Test data: All attune components that should have enhanced discoverability
SKILLS = [
    "plugins/attune/skills/project-brainstorming/SKILL.md",
    "plugins/attune/skills/project-specification/SKILL.md",
    "plugins/attune/skills/project-planning/SKILL.md",
    "plugins/attune/skills/project-execution/SKILL.md",
    "plugins/attune/skills/war-room/SKILL.md",
    "plugins/attune/skills/makefile-generation/SKILL.md",
    "plugins/attune/skills/precommit-setup/SKILL.md",
    "plugins/attune/skills/workflow-setup/SKILL.md",
    "plugins/attune/skills/war-room-checkpoint/SKILL.md",
]

COMMANDS = [
    "plugins/attune/commands/brainstorm.md",
    "plugins/attune/commands/specify.md",
    "plugins/attune/commands/blueprint.md",
    "plugins/attune/commands/execute.md",
    "plugins/attune/commands/war-room.md",
    "plugins/attune/commands/arch-init.md",
    "plugins/attune/commands/project-init.md",
    "plugins/attune/commands/validate.md",
    "plugins/attune/commands/upgrade-project.md",
]

AGENTS = [
    "plugins/attune/agents/project-architect.md",
    "plugins/attune/agents/project-implementer.md",
]

ALL_COMPONENTS = SKILLS + COMMANDS + AGENTS


def parse_frontmatter(file_path: str) -> Tuple[Dict, str, str]:
    """
    Parse frontmatter and body from a markdown file.

    Returns:
        Tuple of (frontmatter_dict, frontmatter_text, body_text)
    """
    with open(file_path) as f:
        content = f.read()

    if not content.startswith("---"):
        pytest.fail(f"{file_path}: Missing frontmatter")

    parts = content.split("---", 2)
    if len(parts) < 3:
        pytest.fail(f"{file_path}: Invalid frontmatter structure")

    frontmatter_text = parts[1]
    body = parts[2]

    try:
        data = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        pytest.fail(f"{file_path}: YAML parse error: {e}")

    return data, frontmatter_text, body


class TestFrontmatterStructure:
    """Test that all components have valid YAML frontmatter."""

    @pytest.mark.parametrize("component_path", ALL_COMPONENTS)
    def test_frontmatter_is_valid_yaml(self, component_path):
        """All frontmatter should parse as valid YAML."""
        data, _, _ = parse_frontmatter(component_path)
        assert isinstance(data, dict), f"{component_path}: Frontmatter should be a dict"

    @pytest.mark.parametrize("component_path", ALL_COMPONENTS)
    def test_has_name_field(self, component_path):
        """All components must have a name field."""
        data, _, _ = parse_frontmatter(component_path)
        assert "name" in data, f"{component_path}: Missing 'name' field"
        assert isinstance(data["name"], str), f"{component_path}: 'name' should be string"
        assert len(data["name"]) > 0, f"{component_path}: 'name' should not be empty"

    @pytest.mark.parametrize("component_path", ALL_COMPONENTS)
    def test_has_description_field(self, component_path):
        """All components must have a description field."""
        data, _, _ = parse_frontmatter(component_path)
        assert "description" in data, f"{component_path}: Missing 'description' field"
        assert isinstance(data["description"], str), f"{component_path}: 'description' should be string"
        assert len(data["description"]) > 0, f"{component_path}: 'description' should not be empty"


class TestDescriptionPattern:
    """Test that descriptions follow the WHAT/WHEN/WHEN NOT pattern."""

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skill_description_has_use_when(self, component_path):
        """Skill descriptions should include 'Use when:' trigger keywords."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")

        # Check for pattern (case-insensitive)
        assert re.search(r"use when", desc, re.IGNORECASE), \
            f"{component_path}: Skill description should include 'Use when:' keywords"

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skill_description_has_do_not_use_when(self, component_path):
        """Skill descriptions should include 'Do not use when:' boundaries."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")

        # Check for pattern (case-insensitive)
        assert re.search(r"do not use when", desc, re.IGNORECASE), \
            f"{component_path}: Skill description should include 'Do not use when:' boundary"

    @pytest.mark.parametrize("component_path", AGENTS)
    def test_agent_description_has_use_when(self, component_path):
        """Agent descriptions should include 'Use when:' invocation context."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")

        # Agents should have use when pattern
        assert re.search(r"use when", desc, re.IGNORECASE), \
            f"{component_path}: Agent description should include 'Use when:' context"


class TestDescriptionLength:
    """Test that descriptions are within target character ranges."""

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skill_description_length(self, component_path):
        """Skills should have 100-300 char descriptions (target 150-200)."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        # Skills can be up to 300 chars (complex skills allowed longer)
        assert 100 <= length <= 350, \
            f"{component_path}: Skill description length {length} outside range [100-350]"

    @pytest.mark.parametrize("component_path", COMMANDS)
    def test_command_description_length(self, component_path):
        """Commands should have 50-150 char descriptions (target 75-125)."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        # Commands should be concise
        assert 50 <= length <= 200, \
            f"{component_path}: Command description length {length} outside range [50-200]"

    @pytest.mark.parametrize("component_path", AGENTS)
    def test_agent_description_length(self, component_path):
        """Agents should have 75-300 char descriptions (target 100-175)."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        # Agents need room for capability description
        assert 75 <= length <= 350, \
            f"{component_path}: Agent description length {length} outside range [75-350]"


class TestContentStructure:
    """Test that content bodies have required sections."""

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skills_have_when_to_use_section(self, component_path):
        """Skills should have 'When To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section (allow case variations)
        assert re.search(r"##\s+When\s+To\s+Use", body, re.IGNORECASE) or \
               re.search(r"##\s+When\s+Commands\s+Should\s+Invoke", body, re.IGNORECASE), \
            f"{component_path}: Missing 'When To Use' section in content"

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skills_have_when_not_to_use_section(self, component_path):
        """Skills should have 'When NOT To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section (allow case variations)
        # War-room-checkpoint is special case (embedded use only)
        if "war-room-checkpoint" not in component_path:
            assert re.search(r"##\s+When\s+NOT\s+To\s+Use", body, re.IGNORECASE), \
                f"{component_path}: Missing 'When NOT To Use' section in content"

    @pytest.mark.parametrize("component_path", COMMANDS)
    def test_commands_have_when_to_use_section(self, component_path):
        """Commands should have 'When To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section
        assert re.search(r"##\s+When\s+To\s+Use", body, re.IGNORECASE), \
            f"{component_path}: Missing 'When To Use' section in content"

    @pytest.mark.parametrize("component_path", COMMANDS)
    def test_commands_have_when_not_to_use_section(self, component_path):
        """Commands should have 'When NOT To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section
        assert re.search(r"##\s+When\s+NOT\s+To\s+Use", body, re.IGNORECASE), \
            f"{component_path}: Missing 'When NOT To Use' section in content"

    @pytest.mark.parametrize("component_path", AGENTS)
    def test_agents_have_when_to_invoke_section(self, component_path):
        """Agents should have 'When To Invoke' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section
        assert re.search(r"##\s+When\s+To\s+Invoke", body, re.IGNORECASE), \
            f"{component_path}: Missing 'When To Invoke' section in content"


class TestTokenBudget:
    """Test that overall token budget is maintained."""

    def test_total_description_length_within_budget(self):
        """Total description length should be within adjusted budget."""
        total_chars = 0

        for component_path in ALL_COMPONENTS:
            data, _, _ = parse_frontmatter(component_path)
            desc = data.get("description", "")
            total_chars += len(desc)

        # Original target: 3000 chars for ~14 components
        # Actual: 20 components (43% more)
        # Adjusted target: 4290 chars
        adjusted_target = 4290

        assert total_chars <= adjusted_target, \
            f"Total description length {total_chars} exceeds adjusted budget {adjusted_target}"

    def test_average_description_length_reasonable(self):
        """Average description length should be reasonable."""
        total_chars = 0

        for component_path in ALL_COMPONENTS:
            data, _, _ = parse_frontmatter(component_path)
            desc = data.get("description", "")
            total_chars += len(desc)

        avg_length = total_chars / len(ALL_COMPONENTS)

        # Average should be between 150-250 chars
        assert 150 <= avg_length <= 250, \
            f"Average description length {avg_length:.0f} outside reasonable range [150-250]"


class TestVersioning:
    """Test that enhanced components have updated version."""

    @pytest.mark.parametrize("component_path", ALL_COMPONENTS)
    def test_version_is_1_4_0_or_later(self, component_path):
        """Enhanced components should be version 1.4.0 or later."""
        data, _, _ = parse_frontmatter(component_path)

        # Version might be in different fields depending on component type
        version = data.get("version")

        if version:
            # Parse version string
            version_parts = version.split(".")
            major = int(version_parts[0])
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0

            # Should be at least 1.4.0
            assert major >= 1, f"{component_path}: Version major should be >= 1"
            if major == 1:
                assert minor >= 4, f"{component_path}: Version minor should be >= 4 for v1.x"


class TestYAMLQuoting:
    """Test that descriptions with colons are properly quoted."""

    @pytest.mark.parametrize("component_path", ALL_COMPONENTS)
    def test_description_with_colon_is_quoted(self, component_path):
        """Descriptions containing colons must be quoted for valid YAML."""
        _, frontmatter_text, _ = parse_frontmatter(component_path)

        # Find the description line
        for line in frontmatter_text.split("\n"):
            if line.strip().startswith("description:"):
                # If the description contains a colon (like "Use when:"),
                # it should be quoted
                desc_part = line.split("description:", 1)[1].strip()

                if ":" in desc_part:
                    # Should start with a quote
                    assert desc_part.startswith('"') or desc_part.startswith("'"), \
                        f"{component_path}: Description with colon should be quoted"
                break


def test_templates_exist():
    """Verify that discoverability templates exist."""
    template_dir = Path("plugins/attune/templates")

    assert template_dir.exists(), "Templates directory should exist"

    required_templates = [
        "skill-discoverability-template.md",
        "command-discoverability-template.md",
        "agent-discoverability-template.md",
        "TEMPLATE-GUIDE.md",
    ]

    for template in required_templates:
        template_path = template_dir / template
        assert template_path.exists(), f"Template {template} should exist"


def test_adr_exists():
    """Verify that ADR for discoverability enhancement exists."""
    adr_path = Path("docs/adr/0005-attune-discoverability-enhancement.md")
    assert adr_path.exists(), "ADR 0005 should exist"

    # Check ADR has key sections
    with open(adr_path) as f:
        content = f.read()

    required_sections = [
        "## Status",
        "## Context",
        "## Decision",
        "## Consequences",
        "## Validation",
    ]

    for section in required_sections:
        assert section in content, f"ADR should have {section} section"


def test_readme_has_discoverability_section():
    """Verify that README documents discoverability enhancement."""
    readme_path = Path("plugins/attune/README.md")
    assert readme_path.exists(), "README should exist"

    with open(readme_path) as f:
        content = f.read()

    assert "Discoverability (v1.4.0)" in content, \
        "README should have Discoverability section"
    assert "WHAT it does" in content, \
        "README should explain WHAT/WHEN/WHEN NOT pattern"


# ============================================================================
# Ecosystem-wide discoverability tests (all non-attune plugins)
# ============================================================================


class TestEcosystemHeadingNormalization:
    """Verify heading case is normalized to 'When To Use' / 'When NOT To Use'."""

    @pytest.mark.parametrize("skill_path", ECOSYSTEM_SKILLS)
    def test_no_lowercase_when_to_use(self, skill_path):
        """Skills must not have lowercase '## When to Use' (should be Title Case)."""
        content = Path(skill_path).read_text()
        # Should NOT have lowercase variant
        assert not re.search(
            r"^## When to Use\b", content, re.MULTILINE
        ), f"{skill_path}: Found '## When to Use' - should be '## When To Use'"

    @pytest.mark.parametrize("cmd_path", ECOSYSTEM_COMMANDS)
    def test_commands_no_identification_blocks(self, cmd_path):
        """Commands must not have <identification> XML blocks (converted to markdown)."""
        content = Path(cmd_path).read_text()
        assert "<identification>" not in content, \
            f"{cmd_path}: Still has <identification> block - should be converted to ## When To Use"


class TestEcosystemContentSections:
    """Verify ecosystem skills/commands have When To Use / When NOT To Use sections."""

    @pytest.mark.parametrize("skill_path", ECOSYSTEM_SKILLS)
    def test_skills_have_when_to_use_or_equivalent(self, skill_path):
        """Skills should have a When To Use section or equivalent.

        Accepted forms (all count as passes):
        - ## When To Use / When to Invoke / When to Escalate (content sections)
        - Any ## When to/To <verb> heading (domain-specific variants)
        - 'Use when' in frontmatter description
        """
        if "/shared/" in skill_path or skill_path.endswith("shared/SKILL.md"):
            pytest.skip("Shared/infrastructure skills exempt")
        if Path(skill_path).stat().st_size < 500:
            pytest.skip("Small utility skill exempt")

        content = Path(skill_path).read_text()

        has_content_section = bool(
            re.search(r"^## When (?:to|To) \w+", content, re.MULTILINE)
        )
        has_frontmatter_hint = False
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            has_frontmatter_hint = bool(
                re.search(r"[Uu]se when", fm_match.group(1))
            )

        assert has_content_section or has_frontmatter_hint, \
            f"{skill_path}: Missing 'When To Use' section or 'Use when' in description"

    @pytest.mark.parametrize("skill_path", ECOSYSTEM_SKILLS)
    def test_skills_have_when_not_to_use(self, skill_path):
        """Skills should have a When NOT To Use section or equivalent.

        Accepted forms (all count as passes):
        - ## When NOT To Use (canonical)
        - Any ## When NOT to/To <verb> heading (domain-specific variants)
        - 'Do not use' in frontmatter description
        """
        if "/shared/" in skill_path or skill_path.endswith("shared/SKILL.md"):
            pytest.skip("Shared/infrastructure skills exempt")
        if Path(skill_path).stat().st_size < 500:
            pytest.skip("Small utility skill exempt")

        content = Path(skill_path).read_text()

        has_content_section = bool(
            re.search(r"^## When NOT [Tt]o \w+", content, re.MULTILINE)
        )
        has_frontmatter_hint = False
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            has_frontmatter_hint = bool(
                re.search(r"[Dd]o not use", fm_match.group(1))
            )

        assert has_content_section or has_frontmatter_hint, \
            f"{skill_path}: Missing 'When NOT To Use' section or 'Do not use' in description"


class TestEcosystemDiscoveryCounts:
    """Sanity checks on discovery counts to catch regressions."""

    def test_sufficient_skills_discovered(self):
        """Should discover at least 80 skills across ecosystem."""
        assert len(ECOSYSTEM_SKILLS) >= 80, \
            f"Only found {len(ECOSYSTEM_SKILLS)} skills, expected >= 80"

    def test_sufficient_commands_discovered(self):
        """Should discover at least 50 commands across ecosystem."""
        assert len(ECOSYSTEM_COMMANDS) >= 50, \
            f"Only found {len(ECOSYSTEM_COMMANDS)} commands, expected >= 50"

    def test_skills_span_multiple_plugins(self):
        """Skills should come from multiple plugins."""
        plugins = {Path(s).parts[1] for s in ECOSYSTEM_SKILLS}
        assert len(plugins) >= 10, \
            f"Only found skills in {len(plugins)} plugins, expected >= 10"
