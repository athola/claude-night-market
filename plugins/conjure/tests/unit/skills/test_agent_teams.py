"""BDD tests for conjure agent-teams skill structure and protocol correctness.

Feature: Agent Teams Coordination
  As a plugin developer
  I want a skill that documents the Claude Code Agent Teams protocol
  So that agents can coordinate via filesystem-based messaging and task management
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

SKILL_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent / "skills" / "agent-teams"
)
SKILL_FILE = SKILL_DIR / "SKILL.md"
MODULES_DIR = SKILL_DIR / "modules"

# Expected modules for the agent-teams skill
EXPECTED_MODULES = [
    "team-management.md",
    "messaging-protocol.md",
    "task-coordination.md",
    "spawning-patterns.md",
]

# Protocol constants from reverse-engineered spec
VALID_TASK_STATUSES = {"pending", "in_progress", "completed", "deleted"}
VALID_MESSAGE_TYPES = {
    "direct",
    "broadcast",
    "shutdown_request",
    "shutdown_response",
    "plan_approval",
}
REQUIRED_CLI_FLAGS = {
    "--agent-id",
    "--agent-name",
    "--team-name",
    "--agent-color",
    "--parent-session-id",
}
TEAM_NAME_PATTERN = r"^[A-Za-z0-9_-]+$"


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    end = content.index("---", 3)
    return yaml.safe_load(content[3:end])


class TestAgentTeamsSkillStructure:
    """
    Feature: Skill file structure

    As a plugin validator
    I want the agent-teams skill to follow ecosystem conventions
    So that it integrates correctly with the plugin system
    """

    @pytest.mark.bdd
    def test_skill_file_exists(self) -> None:
        """Scenario: Skill file present
        Given the conjure plugin
        When checking for agent-teams skill
        Then SKILL.md should exist
        """
        assert SKILL_FILE.exists(), f"SKILL.md not found at {SKILL_FILE}"

    @pytest.mark.bdd
    def test_frontmatter_has_required_fields(self) -> None:
        """Scenario: Valid frontmatter
        Given the agent-teams SKILL.md
        When parsing frontmatter
        Then all required fields should be present
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)

        assert fm["name"] == "agent-teams"
        assert "description" in fm and len(fm["description"]) > 20
        assert fm["category"] == "delegation-framework"
        assert "agent-teams" in fm["tags"]
        assert "delegation-core" in fm["dependencies"]
        assert fm["complexity"] == "advanced"
        assert isinstance(fm["estimated_tokens"], int)
        assert fm["progressive_loading"] is True

    @pytest.mark.bdd
    def test_frontmatter_declares_modules(self) -> None:
        """Scenario: Module declarations
        Given the agent-teams SKILL.md frontmatter
        When checking module list
        Then all four protocol modules should be declared
        """
        content = SKILL_FILE.read_text()
        fm = _parse_frontmatter(content)

        declared = [Path(m).name for m in fm["modules"]]
        for expected in EXPECTED_MODULES:
            assert expected in declared, (
                f"Module {expected} not declared in frontmatter"
            )

    @pytest.mark.bdd
    def test_skill_has_required_sections(self) -> None:
        """Scenario: Required documentation sections
        Given the agent-teams SKILL.md
        When checking content sections
        Then overview, prerequisites, workflow, and exit criteria should exist
        """
        content = SKILL_FILE.read_text()

        required_sections = [
            "## Overview",
            "## When To Use",
            "## When NOT To Use",
            "## Prerequisites",
            "## Exit Criteria",
        ]
        for section in required_sections:
            assert section in content, f"Missing required section: {section}"


class TestAgentTeamsModules:
    """
    Feature: Protocol module files

    As a skill consumer
    I want detailed protocol documentation in modules
    So that I can implement agent coordination correctly
    """

    @pytest.mark.bdd
    def test_all_modules_exist(self) -> None:
        """Scenario: Module files present
        Given the agent-teams skill directory
        When checking for module files
        Then all declared modules should exist on disk
        """
        for module_name in EXPECTED_MODULES:
            module_path = MODULES_DIR / module_name
            assert module_path.exists(), (
                f"Module {module_name} not found at {module_path}"
            )

    @pytest.mark.bdd
    def test_modules_have_frontmatter(self) -> None:
        """Scenario: Module frontmatter
        Given each module file
        When parsing content
        Then each should have valid YAML frontmatter with name and parent_skill
        """
        for module_name in EXPECTED_MODULES:
            content = (MODULES_DIR / module_name).read_text()
            fm = _parse_frontmatter(content)
            assert fm.get("name"), f"{module_name} missing 'name' in frontmatter"
            assert fm.get("parent_skill") == "conjure:agent-teams", (
                f"{module_name} should declare parent_skill: conjure:agent-teams"
            )


class TestTeamManagementModule:
    """
    Feature: Team management protocol

    As an agent coordinator
    I want team lifecycle documentation
    So that I can create, configure, and teardown teams
    """

    @pytest.mark.bdd
    def test_documents_config_json_schema(self) -> None:
        """Scenario: Config format documented
        Given team-management module
        When reading content
        Then it should document the config.json structure
        """
        content = (MODULES_DIR / "team-management.md").read_text()
        assert "config.json" in content
        assert "lead_agent_id" in content
        assert "members" in content

    @pytest.mark.bdd
    def test_documents_team_name_validation(self) -> None:
        """Scenario: Name validation rules
        Given team-management module
        When reading content
        Then it should specify the allowed name pattern
        """
        content = (MODULES_DIR / "team-management.md").read_text()
        # Should mention the alphanumeric + hyphen/underscore constraint
        assert "A-Za-z0-9" in content or "alphanumeric" in content.lower()

    @pytest.mark.bdd
    def test_documents_atomic_writes(self) -> None:
        """Scenario: Atomic write pattern
        Given team-management module
        When reading content
        Then it should describe the atomic write mechanism
        """
        content = (MODULES_DIR / "team-management.md").read_text()
        assert "atomic" in content.lower()


class TestMessagingProtocolModule:
    """
    Feature: Messaging protocol

    As an agent participant
    I want messaging documentation
    So that agents can exchange messages safely
    """

    @pytest.mark.bdd
    def test_documents_message_format(self) -> None:
        """Scenario: Message JSON format
        Given messaging-protocol module
        When reading content
        Then it should document the InboxMessage fields
        """
        content = (MODULES_DIR / "messaging-protocol.md").read_text()
        required_fields = ["from", "text", "timestamp", "read"]
        for field in required_fields:
            assert field in content, f"Message field '{field}' not documented"

    @pytest.mark.bdd
    def test_documents_message_types(self) -> None:
        """Scenario: Message type catalog
        Given messaging-protocol module
        When reading content
        Then it should document all message types
        """
        content = (MODULES_DIR / "messaging-protocol.md").read_text()
        for msg_type in ["direct", "broadcast", "shutdown"]:
            assert msg_type.lower() in content.lower(), (
                f"Message type '{msg_type}' not documented"
            )

    @pytest.mark.bdd
    def test_documents_fcntl_locking(self) -> None:
        """Scenario: Concurrency safety
        Given messaging-protocol module
        When reading content
        Then it should explain fcntl-based file locking
        """
        content = (MODULES_DIR / "messaging-protocol.md").read_text()
        assert "fcntl" in content
        assert "lock" in content.lower()


class TestTaskCoordinationModule:
    """
    Feature: Task coordination protocol

    As a task manager
    I want task lifecycle documentation
    So that agents can create, claim, and complete tasks with dependencies
    """

    @pytest.mark.bdd
    def test_documents_task_states(self) -> None:
        """Scenario: Task state machine
        Given task-coordination module
        When reading content
        Then all valid task statuses should be documented
        """
        content = (MODULES_DIR / "task-coordination.md").read_text()
        for status in ["pending", "in_progress", "completed", "deleted"]:
            assert status in content, f"Task status '{status}' not documented"

    @pytest.mark.bdd
    def test_documents_forward_only_transitions(self) -> None:
        """Scenario: No backward state transitions
        Given task-coordination module
        When reading content
        Then it should state that backward transitions are prohibited
        """
        content = (MODULES_DIR / "task-coordination.md").read_text()
        assert "backward" in content.lower() or "forward-only" in content.lower()

    @pytest.mark.bdd
    def test_documents_dependency_fields(self) -> None:
        """Scenario: Dependency tracking
        Given task-coordination module
        When reading content
        Then blocks and blocked_by fields should be documented
        """
        content = (MODULES_DIR / "task-coordination.md").read_text()
        assert "blocks" in content
        assert "blocked_by" in content

    @pytest.mark.bdd
    def test_documents_cycle_detection(self) -> None:
        """Scenario: Circular dependency prevention
        Given task-coordination module
        When reading content
        Then it should describe cycle detection via BFS
        """
        content = (MODULES_DIR / "task-coordination.md").read_text()
        assert "cycle" in content.lower()
        assert "bfs" in content.lower() or "breadth" in content.lower()


class TestSpawningPatternsModule:
    """
    Feature: Agent spawning patterns

    As a team lead agent
    I want spawning documentation
    So that I can launch teammate processes correctly
    """

    @pytest.mark.bdd
    def test_documents_cli_flags(self) -> None:
        """Scenario: Required CLI flags
        Given spawning-patterns module
        When reading content
        Then all undocumented Claude CLI flags should be listed
        """
        content = (MODULES_DIR / "spawning-patterns.md").read_text()
        for flag in REQUIRED_CLI_FLAGS:
            assert flag in content, f"CLI flag '{flag}' not documented"

    @pytest.mark.bdd
    def test_documents_tmux_integration(self) -> None:
        """Scenario: tmux pane management
        Given spawning-patterns module
        When reading content
        Then tmux split-window pattern should be documented
        """
        content = (MODULES_DIR / "spawning-patterns.md").read_text()
        assert "tmux" in content.lower()
        assert "split" in content.lower() or "pane" in content.lower()

    @pytest.mark.bdd
    def test_documents_environment_variables(self) -> None:
        """Scenario: Required environment
        Given spawning-patterns module
        When reading content
        Then required env vars should be documented
        """
        content = (MODULES_DIR / "spawning-patterns.md").read_text()
        assert (
            "CLAUDECODE" in content or "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" in content
        )

    @pytest.mark.bdd
    def test_documents_agent_id_format(self) -> None:
        """Scenario: Agent identity format
        Given spawning-patterns module
        When reading content
        Then the name@team format should be documented
        """
        content = (MODULES_DIR / "spawning-patterns.md").read_text()
        # Should mention the name@team format
        assert "@" in content
        assert "agent-id" in content.lower() or "agent_id" in content.lower()


class TestPluginJsonRegistration:
    """
    Feature: Plugin registry integration

    As a plugin system
    I want agent-teams registered in plugin.json
    So that it is discoverable
    """

    @pytest.mark.bdd
    def test_skill_registered_in_plugin_json(self) -> None:
        """Scenario: Plugin.json includes agent-teams
        Given the conjure plugin.json
        When checking skills array
        Then agent-teams should be registered
        """
        plugin_json = (
            Path(__file__).resolve().parent.parent.parent.parent
            / ".claude-plugin"
            / "plugin.json"
        )
        config = json.loads(plugin_json.read_text())
        skill_paths = config.get("skills", [])
        assert any("agent-teams" in s for s in skill_paths), (
            "agent-teams not registered in plugin.json skills array"
        )
