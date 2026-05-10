"""BDD contract tests for the pensive:harden skill.

Feature: pensive:harden skill is loadable, complete, and wired
to real composed skills.

As a Claude Code user invoking /harden
I want the harden SKILL.md to declare a complete contract
So that the command activates a real, composable workflow rather
than a half-written sketch.

The harden skill is mostly markdown plus module composition. These
tests pin the SKILL.md/module contract so a reviewer or future
contributor cannot silently break:

- The frontmatter declares dependencies on skills that actually
  exist on disk (no dangling Skill() refs).
- Every module listed in the frontmatter actually exists.
- Required sections (Exit Criteria, Severity Classification,
  When To Use, Workflow) are present.
- The skill explicitly documents that proposals must be
  citation-backed and apply-on-approval-only.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_DIR = REPO_ROOT / "plugins" / "pensive" / "skills" / "harden"
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"


def _read_skill() -> str:
    if not SKILL_FILE.exists():
        pytest.fail(f"harden SKILL.md missing: {SKILL_FILE}")
    return SKILL_FILE.read_text(encoding="utf-8")


def _read_frontmatter(content: str) -> str:
    """Return the YAML frontmatter block (between leading --- markers)."""
    if not content.startswith("---\n"):
        pytest.fail("SKILL.md must begin with `---` YAML frontmatter")
    end = content.find("\n---\n", 4)
    if end == -1:
        pytest.fail("SKILL.md frontmatter has no closing `---`")
    return content[4:end]


class TestHardenSkillFrontmatter:
    """The SKILL.md frontmatter must declare a complete contract."""

    def test_skill_file_exists(self) -> None:
        """Given the pensive plugin
        When /harden is invoked
        Then the harden SKILL.md must exist on disk."""
        assert SKILL_FILE.is_file(), (
            f"Expected SKILL.md at {SKILL_FILE}, but it is missing."
        )

    def test_frontmatter_declares_required_keys(self) -> None:
        """Given the SKILL.md frontmatter
        When the loader parses it
        Then it must declare name, description, category, complexity,
        modules, and dependencies."""
        fm = _read_frontmatter(_read_skill())
        for key in (
            "name: harden",
            "category: security",
            "complexity: advanced",
            "progressive_loading: true",
            "modules:",
            "dependencies:",
        ):
            assert key in fm, f"Frontmatter missing required key: {key}"

    def test_estimated_tokens_within_budget(self) -> None:
        """Given the project's progressive-loading discipline
        When the skill declares estimated_tokens
        Then the value must be within the project's ~1500-token cap."""
        fm = _read_frontmatter(_read_skill())
        # Find `estimated_tokens: NNN`
        for line in fm.splitlines():
            if line.strip().startswith("estimated_tokens:"):
                value = int(line.split(":", 1)[1].strip())
                assert value <= 1500, (
                    f"estimated_tokens {value} exceeds project cap of 1500"
                )
                return
        pytest.fail("Frontmatter must declare estimated_tokens")


class TestHardenSkillReferences:
    """Skill() refs in dependencies must point at real skills."""

    @pytest.mark.parametrize(
        "dep",
        [
            "pensive:safety-critical-patterns",
            "pensive:rust-review",
            "pensive:bug-review",
            "pensive:tiered-audit",
            "pensive:blast-radius",
            "leyline:supply-chain-advisory",
            "leyline:authentication-patterns",
            "leyline:content-sanitization",
            "abstract:hook-authoring",
            "imbue:proof-of-work",
        ],
    )
    def test_each_dependency_skill_exists(self, dep: str) -> None:
        """Given each declared dependency
        When the skill graph is resolved
        Then the dependency skill directory must exist on disk."""
        plugin, skill = dep.split(":", 1)
        skill_path = REPO_ROOT / "plugins" / plugin / "skills" / skill
        assert skill_path.is_dir(), (
            f"Declared dependency {dep} resolves to {skill_path}, "
            "which does not exist (dangling Skill ref)."
        )


class TestHardenSkillModules:
    """Each module listed in the frontmatter must exist on disk."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "nist-controls.md",
            "python-checks.md",
            "rust-checks.md",
            "cross-cutting.md",
            "frontier-checks.md",
            "proposal-shape.md",
        ],
    )
    def test_module_file_exists(self, module_name: str) -> None:
        """Given a module file name listed in SKILL.md frontmatter
        When the harden workflow loads modules progressively
        Then the file must exist on disk and be non-empty."""
        module_path = MODULES_DIR / module_name
        assert module_path.is_file(), (
            f"Module {module_name} listed in SKILL.md but missing at {module_path}."
        )
        assert module_path.stat().st_size > 0, (
            f"Module {module_name} exists but is empty."
        )

    def test_proposal_shape_module_documents_required_fields(self) -> None:
        """Given the proposal-shape module
        When a proposal is drafted from it
        Then the module must document the required proposal fields:
        file/lines, diff or config snippet, blast radius, reversal plan,
        expected-passing test, citation."""
        module = MODULES_DIR / "proposal-shape.md"
        if not module.is_file():
            pytest.fail("proposal-shape.md missing")
        text = module.read_text(encoding="utf-8").lower()
        for required in (
            "citation",
            "blast radius",
            "reversal",
            "test",
            "diff",
        ):
            assert required in text, (
                f"proposal-shape.md must mention '{required}' to define "
                "the required proposal contract"
            )


class TestHardenSkillContract:
    """SKILL.md body must document the apply-on-approval contract."""

    def test_required_sections_present(self) -> None:
        """Given the SKILL.md body
        When a reader scans for the contract
        Then the required sections must be present."""
        body = _read_skill()
        for heading in (
            "## When To Use",
            "## When NOT To Use",
            "## Required TodoWrite Items",
            "## Progressive Loading",
            "## Core Workflow",
            "## Severity Classification",
            "## Safety Rails",
            "## Exit Criteria",
        ):
            assert heading in body, f"SKILL.md missing required heading: {heading}"

    def test_citation_requirement_documented(self) -> None:
        """Given the citation discipline of the harden workflow
        When a finding is generated
        Then the SKILL.md must state that findings without a
        NIST/CWE/RustSec citation are advisory only."""
        body = _read_skill().lower()
        assert "citation is mandatory" in body or (
            "citation" in body and "advisory only" in body
        ), "SKILL.md must document that uncited findings are advisory only"

    def test_apply_on_approval_only(self) -> None:
        """Given the active-proposal feature
        When a proposal is generated
        Then the SKILL.md must state that proposals require user
        approval before being applied."""
        body = _read_skill().lower()
        assert "never apply without approval" in body or (
            "approval gate" in body and "auto-apply" in body
        ), "SKILL.md must document the approval gate for proposals"

    def test_one_finding_per_commit_documented(self) -> None:
        """Given the commit-shape contract
        When proposals are applied
        Then each finding must land as a discrete commit so reverts
        are per-finding."""
        body = _read_skill().lower()
        assert "one finding per commit" in body or (
            "discrete commit" in body and "revert" in body
        ), "SKILL.md must document the one-commit-per-finding rule"


class TestHardenCommandRegistered:
    """The /harden command file must exist and reference the skill."""

    def test_command_file_exists(self) -> None:
        """Given the /harden command
        When the user invokes it
        Then the command markdown must exist."""
        cmd = REPO_ROOT / "plugins" / "pensive" / "commands" / "harden.md"
        assert cmd.is_file(), f"/harden command missing at {cmd}"

    def test_command_references_skill(self) -> None:
        """Given the command file
        When the command activates
        Then it must reference Skill(pensive:harden) so the skill
        loads under the command."""
        cmd = REPO_ROOT / "plugins" / "pensive" / "commands" / "harden.md"
        text = cmd.read_text(encoding="utf-8")
        assert "pensive:harden" in text, (
            "harden.md command must reference Skill(pensive:harden)"
        )

    def test_plugin_json_registers_skill_and_command(self) -> None:
        """Given the pensive plugin manifest
        When Claude Code loads the plugin
        Then plugin.json must register both the skill directory and
        the command file."""
        pj = REPO_ROOT / "plugins" / "pensive" / ".claude-plugin" / "plugin.json"
        text = pj.read_text(encoding="utf-8")
        assert "./skills/harden" in text, (
            "plugin.json must register ./skills/harden in the skills array"
        )
        assert "./commands/harden.md" in text, (
            "plugin.json must register ./commands/harden.md in the commands array"
        )
