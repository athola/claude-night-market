"""Contract tests for the model-and-harness-updates skill.

Feature: A runnable workflow for model and harness releases

As a maintainer
I want the skill's promises to be checkable from outside the prose
So that the workflow cannot drift from the scripts and gates it drives

Each assertion anchors on a clause unique to the passage it guards, so
deleting that passage turns a test red rather than silently weakening
the skill.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "night-market-model-and-harness-updates"
SKILL = SKILL_DIR / "SKILL.md"
LEDGER = REPO_ROOT / ".claude" / "upstream-baseline.json"

REQUIRED_MODULES = (
    "drift-detection.md",
    "research-protocol.md",
    "asset-sweep.md",
    "verification.md",
)


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _frontmatter(text: str) -> str:
    block = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert block, "SKILL.md must open with a frontmatter block"
    return block.group(1)


def _field(body: str, key: str) -> str:
    match = re.search(rf"^{key}:\s*(.+)$", body, re.MULTILINE)
    assert match, f"frontmatter must declare {key}"
    return match.group(1).strip()


class TestSkillStructure:
    """The skill file itself is well formed."""

    def test_skill_file_exists(self) -> None:
        """
        Scenario: The skill is installed
        Given the local skills directory
        When the skill path is resolved
        Then SKILL.md is present
        """
        assert SKILL.is_file()

    def test_frontmatter_declares_name_and_description(self, skill_text: str) -> None:
        """
        Scenario: The skill is discoverable
        Given the leading YAML block
        When name and description are read
        Then both are present and the name matches the directory
        """
        body = _frontmatter(skill_text)
        assert _field(body, "description")
        assert _field(body, "name") == SKILL_DIR.name

    def test_description_states_when_to_use_and_when_not_to(
        self, skill_text: str
    ) -> None:
        """
        Scenario: The description routes the reader
        Given the house description format
        When the description is read
        Then it carries a "Use when" and a "Do not use" clause
        """
        description = _field(_frontmatter(skill_text), "description")
        assert "Use when" in description
        assert "Do not use" in description

    def test_has_exit_criteria_section(self, skill_text: str) -> None:
        """
        Scenario: The skill can be told when it is done
        Given the repo rule requiring exit criteria
        When the headings are scanned
        Then an Exit Criteria section exists with checkbox items
        """
        assert "## Exit Criteria" in skill_text
        tail = skill_text.split("## Exit Criteria", 1)[1]
        assert tail.count("- [ ]") >= 3


class TestModulesResolve:
    """Every module the hub references exists on disk."""

    @pytest.mark.parametrize("module", REQUIRED_MODULES)
    def test_referenced_module_exists(self, module: str, skill_text: str) -> None:
        """
        Scenario: The hub points at a module
        Given a modules/ reference in the skill body
        When the path is resolved
        Then the module file is present
        """
        assert f"modules/{module}" in skill_text, f"hub must reference {module}"
        assert (SKILL_DIR / "modules" / module).is_file()

    def test_no_dangling_module_references(self, skill_text: str) -> None:
        """
        Scenario: The hub references a module that was renamed
        Given every modules/ path mentioned in the body
        When each is resolved against disk
        Then none is missing
        """
        referenced = set(re.findall(r"modules/([\w.-]+\.md)", skill_text))
        missing = {m for m in referenced if not (SKILL_DIR / "modules" / m).is_file()}
        assert not missing, f"dangling module references: {sorted(missing)}"


class TestWorkflowContract:
    """The prose matches the scripts and gates it drives."""

    def test_names_the_drift_script(self, skill_text: str) -> None:
        """
        Scenario: The workflow's first step is deterministic
        Given the five-step sequence
        When step 1 is read
        Then it invokes check_upstream_drift.py
        """
        assert "scripts/check_upstream_drift.py" in skill_text
        assert (REPO_ROOT / "scripts" / "check_upstream_drift.py").is_file()

    def test_names_the_matrix_gate(self, skill_text: str) -> None:
        """
        Scenario: The sweep is proved against the existing gate
        Given the verification step
        When the gate is named
        Then check_agent_model_matrix.py exists
        """
        assert "scripts/check_agent_model_matrix.py" in skill_text
        assert (REPO_ROOT / "scripts" / "check_agent_model_matrix.py").is_file()

    def test_records_all_four_drift_classes(self, skill_text: str) -> None:
        """
        Scenario: The reader learns what the detector reports
        Given the drift class table
        When the classes are read
        Then all four appear
        """
        for kind in ("harness", "vocabulary", "dated_ids", "unknown_tier"):
            assert f"`{kind}`" in skill_text

    def test_states_the_proof_before_ledger_ordering(self, skill_text: str) -> None:
        """
        Scenario: The ledger is written last
        Given the ordering guarantee
        When the sequencing sentence is read
        Then it says the proof runs before the ledger is written
        """
        assert "before the ledger is written, never after" in skill_text

    def test_states_the_deterministic_split(self, skill_text: str) -> None:
        """
        Scenario: The reader learns what cannot be automated
        Given that no local command enumerates the model roster
        When the limits section is read
        Then the skill says so plainly
        """
        assert "No local command enumerates the current" in skill_text


class TestLedgerContract:
    """The watermark the skill depends on is present and valid."""

    def test_ledger_exists_and_parses(self) -> None:
        """
        Scenario: The skill diffs against a recorded baseline
        Given the ledger path the skill names
        When it is loaded
        Then it parses as JSON
        """
        assert LEDGER.is_file()
        json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_ledger_records_harness_and_roster(self) -> None:
        """
        Scenario: The watermark is complete
        Given a loaded ledger
        When its keys are read
        Then harness version, model tiers, and effort levels are recorded
        """
        data = json.loads(LEDGER.read_text(encoding="utf-8"))
        assert data["harness"]["version"]
        assert data["models"]["tiers"]
        assert data["vocabularies"]["effort_levels"]

    def test_ledger_records_a_last_migration(self) -> None:
        """
        Scenario: A run can diff against the previous run
        Given a loaded ledger
        When last_migration is read
        Then it names a trigger and a report path
        """
        migration = json.loads(LEDGER.read_text(encoding="utf-8"))["last_migration"]
        assert migration["trigger"]
        assert migration["report"]

    def test_migration_report_path_is_recorded_but_ephemeral(self) -> None:
        """
        Scenario: The ledger records where a run wrote its notes
        Given the report path in last_migration
        When the path shape and the ignore rules are read
        Then the path names docs/migrations/, and that directory is
        gitignored, so the report is a local working artifact that
        nothing stats
        """
        migration = json.loads(LEDGER.read_text(encoding="utf-8"))["last_migration"]
        assert migration["report"].startswith("docs/migrations/")
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        assert "docs/migrations/" in {line.strip() for line in gitignore.splitlines()}
