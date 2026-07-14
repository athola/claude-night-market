"""
Test suite for ecosystem-wide discoverability enhancements.

Validates that all skills, commands, and agents follow the discoverability
pattern documented in ``docs/skill-description-guide.md``.

Pattern: [WHAT]. Use when [trigger]. [Optional: Do not use when [boundary].]

The character cap is NOT hardcoded here. It is imported from
``plugins/abstract/scripts/validate_budget.py``, the same module the
``validate-description-budget`` pre-commit hook runs. This suite once carried
its own copy of the cap at 100 chars, a rule ADR-0004 superseded with 160.
Because no CI job runs the root ``tests/`` suite, the dead copy went on failing
169 fully compliant skills for months while the live pre-commit gate passed
them. One cap, one definition, imported: the two gates cannot disagree again.

References:
- docs/skill-description-guide.md (the standard)
- docs/adr/0004-skill-description-budget-optimization.md (160-char cap)
- docs/adr/0005-attune-discoverability-enhancement.md
"""

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

PLUGINS_DIR = Path("plugins")
SKIP_PLUGINS = {"attune"}  # Attune tested separately below

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_description_max() -> int:
    """Import the per-description cap from the module the pre-commit hook runs.

    ``validate_budget.py`` is a script, not an installed package, so it is
    loaded by path. Importing rather than restating the number is the whole
    point: a test that keeps its own copy of a constant is a test that can
    silently outlive the rule it is meant to enforce.
    """
    script = REPO_ROOT / "plugins" / "abstract" / "scripts" / "validate_budget.py"
    spec = importlib.util.spec_from_file_location("validate_budget", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"cannot load the description cap from {script}. The pre-commit hook "
            "'validate-description-budget' runs this same module; if it has moved, "
            "this suite and that hook have drifted apart and both must be updated."
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DESCRIPTION_MAX


DESCRIPTION_MAX = _load_description_max()

# The description and section patterns, defined once and shared by every class
# below. They used to live as private copies inside TestDescriptionPattern and
# TestEcosystemContentSections, and the copies drifted. The first was widened to
# accept the prepositions a trigger actually needs ("Use before declaring
# implementation done"); the second still demanded the literal word "when" and
# failed 12 skills for stating their trigger correctly. That is the same failure
# the DESCRIPTION_MAX comment above describes, in a second place. One rule, one
# definition, and the two gates cannot disagree again.

# A trigger opens with any preposition: "Use when/for/at/before/after/during ...".
# The guide templates on "Use when", but its own examples read "Use before any
# creative work" and "Use for audits". A missing trigger is the defect the guide
# names ("Audits Makefiles for build correctness."), not a temporal one.
USE_PATTERN = re.compile(r"use (?:when|for|at|before|after|during)\b", re.IGNORECASE)

# A boundary in the description: "Do not use ...", "Skip if/for ...". The clause
# is the boundary; which preposition follows it is not the point, exactly as with
# the trigger above. This is the union of the two patterns it replaces, so it can
# only accept more than they did, never less: unifying them cannot redden a skill
# that was green.
SKIP_PATTERN = re.compile(r"(?:do not use|skip (?:if|for))\b", re.IGNORECASE)

# A trigger as a body heading: "## When To Use". Case-insensitive, because the
# heading is prose and the repo cases it both ways. It deliberately does not
# match "## When NOT to Use", whose next word is NOT rather than "to".
USE_SECTION_PATTERN = re.compile(r"^##\s+When\s+to\s+\w+", re.MULTILINE | re.IGNORECASE)

# A boundary as a body heading: "## When NOT To Use". Case-insensitive so that
# "## When Not to Use" counts; requiring uppercase NOT failed a section that was
# present and correct, differing only in how its author shifted a key.
SKIP_SECTION_PATTERN = re.compile(
    r"^##\s+When\s+NOT\s+to\s+\w+", re.MULTILINE | re.IGNORECASE
)

# Excluded: JSON agents, __init__.py, shared skills without full frontmatter
EXCLUDED_PATTERNS = {"__init__.py", ".gitkeep"}


def discover_ecosystem_skills() -> list[str]:
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


def discover_ecosystem_commands() -> list[str]:
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


def discover_ecosystem_agents_md() -> list[str]:
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


def parse_frontmatter(file_path: str) -> tuple[dict, str, str]:
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
        assert isinstance(data["name"], str), (
            f"{component_path}: 'name' should be string"
        )
        assert len(data["name"]) > 0, f"{component_path}: 'name' should not be empty"

    @pytest.mark.parametrize("component_path", ALL_COMPONENTS)
    def test_has_description_field(self, component_path):
        """All components must have a description field."""
        data, _, _ = parse_frontmatter(component_path)
        assert "description" in data, f"{component_path}: Missing 'description' field"
        assert isinstance(data["description"], str), (
            f"{component_path}: 'description' should be string"
        )
        assert len(data["description"]) > 0, (
            f"{component_path}: 'description' should not be empty"
        )


class TestDescriptionPattern:
    """Test that descriptions state WHAT the component does and WHEN to reach for it.

    The trigger preposition is deliberately open. ``docs/skill-description-guide.md``
    templates on "Use when [trigger]", but its own worked example for
    ``attune:brainstorm`` reads "Use before any creative work", and the lifecycle
    skills chain on "Use after brainstorming". A regex accepting only when/for/at
    failed those descriptions for stating their trigger in the one preposition the
    trigger actually needs. What the guide calls a mistake is a *missing* trigger
    ("Audit Makefiles for build correctness."), not a temporal one.
    """

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skill_description_has_use_when(self, component_path):
        """Skill descriptions must name a trigger, not just a capability."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")

        assert USE_PATTERN.search(desc), (
            f"{component_path}: Skill description states WHAT but not WHEN. "
            "Add a 'Use when/before/after ...' trigger."
        )

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skill_has_boundary_somewhere(self, component_path):
        """Skills must state a boundary, in the description or in the body.

        The guide marks the description clause "[Optional: Do not use when ...]"
        and asks for it only "for skills with similar alternatives". Requiring it
        in every description contradicted that, and contradicted this suite's own
        ecosystem check, which accepts a '## When NOT To Use' section instead.
        A boundary must exist; the guide does not dictate which of the two places
        it lives in.
        """
        data, _, body = parse_frontmatter(component_path)
        desc = data.get("description", "")

        in_description = bool(SKIP_PATTERN.search(desc))
        in_body = bool(SKIP_SECTION_PATTERN.search(body))

        assert in_description or in_body, (
            f"{component_path}: no boundary. Add a 'Do not use when ...' clause to "
            "the description or a '## When NOT To Use' section to the body."
        )

    @pytest.mark.parametrize("component_path", AGENTS)
    def test_agent_description_has_use_when(self, component_path):
        """Agent descriptions should include usage trigger context."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")

        assert USE_PATTERN.search(desc), (
            f"{component_path}: Agent description should include 'Use when/for' context"
        )


class TestDescriptionLength:
    """Test that descriptions are within target character ranges."""

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skill_description_length(self, component_path):
        """Skills must have a description between 20 chars and the ADR-0004 cap."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        assert 20 <= length <= DESCRIPTION_MAX, (
            f"{component_path}: Skill description length {length} outside "
            f"range [20-{DESCRIPTION_MAX}]"
        )

    @pytest.mark.parametrize("component_path", ECOSYSTEM_SKILLS)
    def test_ecosystem_skill_description_within_cap(self, component_path):
        """Ecosystem skill descriptions must be within the ADR-0004 char cap."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        assert length <= DESCRIPTION_MAX, (
            f"{component_path}: description is {length} chars "
            f"(max {DESCRIPTION_MAX}): {desc!r}"
        )

    @pytest.mark.parametrize("component_path", COMMANDS)
    def test_command_description_length(self, component_path):
        """Commands should have 50-150 char descriptions (target 75-125)."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        # Commands should be concise
        assert 50 <= length <= 200, (
            f"{component_path}: Command description length {length} outside range [50-200]"
        )

    @pytest.mark.parametrize("component_path", AGENTS)
    def test_agent_description_length(self, component_path):
        """Agents should have 75-300 char descriptions (target 100-175)."""
        data, _, _ = parse_frontmatter(component_path)
        desc = data.get("description", "")
        length = len(desc)

        # Agents need room for capability description
        assert 75 <= length <= 350, (
            f"{component_path}: Agent description length {length} outside range [75-350]"
        )


class TestContentStructure:
    """Test that content bodies have required sections."""

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skills_have_when_to_use_section(self, component_path):
        """Skills should have 'When To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section (allow case variations)
        assert re.search(r"##\s+When\s+To\s+Use", body, re.IGNORECASE) or re.search(
            r"##\s+When\s+Commands\s+Should\s+Invoke", body, re.IGNORECASE
        ), f"{component_path}: Missing 'When To Use' section in content"

    @pytest.mark.parametrize("component_path", SKILLS)
    def test_skills_have_when_not_to_use_section(self, component_path):
        """Skills should have 'When NOT To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section (allow case variations)
        # War-room-checkpoint is special case (embedded use only)
        if "war-room-checkpoint" not in component_path:
            assert re.search(r"##\s+When\s+NOT\s+To\s+Use", body, re.IGNORECASE), (
                f"{component_path}: Missing 'When NOT To Use' section in content"
            )

    @pytest.mark.parametrize("component_path", COMMANDS)
    def test_commands_have_when_to_use_section(self, component_path):
        """Commands should have 'When To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section
        assert re.search(r"##\s+When\s+To\s+Use", body, re.IGNORECASE), (
            f"{component_path}: Missing 'When To Use' section in content"
        )

    @pytest.mark.parametrize("component_path", COMMANDS)
    def test_commands_have_when_not_to_use_section(self, component_path):
        """Commands should have 'When NOT To Use' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section
        assert re.search(r"##\s+When\s+NOT\s+To\s+Use", body, re.IGNORECASE), (
            f"{component_path}: Missing 'When NOT To Use' section in content"
        )

    @pytest.mark.parametrize("component_path", AGENTS)
    def test_agents_have_when_to_invoke_section(self, component_path):
        """Agents should have 'When To Invoke' section in content body."""
        _, _, body = parse_frontmatter(component_path)

        # Check for section
        assert re.search(r"##\s+When\s+To\s+Invoke", body, re.IGNORECASE), (
            f"{component_path}: Missing 'When To Invoke' section in content"
        )


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

        assert total_chars <= adjusted_target, (
            f"Total description length {total_chars} exceeds adjusted budget {adjusted_target}"
        )

    def test_average_description_length_reasonable(self):
        """Average description length should be reasonable."""
        total_chars = 0

        for component_path in ALL_COMPONENTS:
            data, _, _ = parse_frontmatter(component_path)
            desc = data.get("description", "")
            total_chars += len(desc)

        avg_length = total_chars / len(ALL_COMPONENTS)

        # Commands and agents are allowed longer descriptions than skills, so the
        # per-skill cap is the tightest bound the average can be held to without
        # inventing a number. The real gates are the per-description cap above and
        # the total budget below; this only catches a fleet-wide blowout.
        assert 20 <= avg_length <= DESCRIPTION_MAX, (
            f"Average description length {avg_length:.0f} outside reasonable "
            f"range [20-{DESCRIPTION_MAX}]"
        )


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
                    assert desc_part.startswith('"') or desc_part.startswith("'"), (
                        f"{component_path}: Description with colon should be quoted"
                    )
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

    assert "Discoverability (v1.4.0)" in content, (
        "README should have Discoverability section"
    )
    assert "WHAT it does" in content, "README should explain WHAT/WHEN/WHEN NOT pattern"


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
        assert not re.search(r"^## When to Use\b", content, re.MULTILINE), (
            f"{skill_path}: Found '## When to Use' - should be '## When To Use'"
        )

    @pytest.mark.parametrize("cmd_path", ECOSYSTEM_COMMANDS)
    def test_commands_no_identification_blocks(self, cmd_path):
        """Commands must not have <identification> XML blocks (converted to markdown)."""
        content = Path(cmd_path).read_text()
        assert "<identification>" not in content, (
            f"{cmd_path}: Still has <identification> block - should be converted to ## When To Use"
        )


class TestEcosystemContentSections:
    """Verify ecosystem skills state a trigger and a boundary.

    A skill may state either one in its description or as a body heading; the
    guide does not dictate which. These checks run the module-level patterns
    that ``TestDescriptionPattern`` runs, rather than private copies. The copies
    are what let this class go on demanding the literal word "when" after the
    other class had already accepted "Use before" and "Use after".
    """

    @staticmethod
    def _content_or_skip(skill_path: str) -> str:
        """Read the skill, or skip the exempt ones."""
        if "/shared/" in skill_path or skill_path.endswith("shared/SKILL.md"):
            pytest.skip("Shared/infrastructure skills exempt")
        if Path(skill_path).stat().st_size < 500:
            pytest.skip("Small utility skill exempt")
        return Path(skill_path).read_text()

    @staticmethod
    def _frontmatter(content: str) -> str:
        """Return the frontmatter block, or "" if the file has none.

        The description checks are scoped to this block on purpose. Searching
        the whole file would let a stray "use for" anywhere in the prose satisfy
        a check about what the frontmatter promises.
        """
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        return match.group(1) if match else ""

    @pytest.mark.parametrize("skill_path", ECOSYSTEM_SKILLS)
    def test_skills_have_when_to_use_or_equivalent(self, skill_path):
        """Every ecosystem skill must name a trigger, in its description or body."""
        content = self._content_or_skip(skill_path)

        in_body = bool(USE_SECTION_PATTERN.search(content))
        in_description = bool(USE_PATTERN.search(self._frontmatter(content)))

        assert in_body or in_description, (
            f"{skill_path}: no trigger. Add a 'Use when/for/before/after ...' "
            "clause to the description or a '## When To Use' section to the body."
        )

    @pytest.mark.parametrize("skill_path", ECOSYSTEM_SKILLS)
    def test_skills_have_when_not_to_use(self, skill_path):
        """Every ecosystem skill must state a boundary, in its description or body."""
        content = self._content_or_skip(skill_path)

        in_body = bool(SKIP_SECTION_PATTERN.search(content))
        in_description = bool(SKIP_PATTERN.search(self._frontmatter(content)))

        assert in_body or in_description, (
            f"{skill_path}: no boundary. Add a 'Do not use when ...' clause to the "
            "description or a '## When NOT To Use' section to the body."
        )


class TestEcosystemDiscoveryCounts:
    """Sanity checks on discovery counts to catch regressions."""

    def test_sufficient_skills_discovered(self):
        """Should discover at least 80 skills across ecosystem."""
        assert len(ECOSYSTEM_SKILLS) >= 80, (
            f"Only found {len(ECOSYSTEM_SKILLS)} skills, expected >= 80"
        )

    def test_sufficient_commands_discovered(self):
        """Should discover at least 50 commands across ecosystem."""
        assert len(ECOSYSTEM_COMMANDS) >= 50, (
            f"Only found {len(ECOSYSTEM_COMMANDS)} commands, expected >= 50"
        )

    def test_skills_span_multiple_plugins(self):
        """Skills should come from multiple plugins."""
        plugins = {Path(s).parts[1] for s in ECOSYSTEM_SKILLS}
        assert len(plugins) >= 10, (
            f"Only found skills in {len(plugins)} plugins, expected >= 10"
        )
