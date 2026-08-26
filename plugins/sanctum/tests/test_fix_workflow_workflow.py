"""The shipped fix-workflow analysis script must keep its boundaries.

Two of them are safety properties rather than style: the script must not
carry an implement or validate stage, because a workflow's subagents run
in acceptEdits and the script has no shell to check its own work.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PLUGIN_ROOT / "workflows" / "fix-workflow-analysis.js"
COMMAND = PLUGIN_ROOT / "commands" / "fix-workflow.md"


def test_workflow_ships_at_the_discovered_location() -> None:
    """GIVEN the plugin as installed.

    WHEN the harness looks for workflows
    THEN it finds one at workflows/ in the plugin root
    """
    assert WORKFLOW.is_file()


def test_meta_is_the_first_statement_and_is_complete() -> None:
    """GIVEN the shipped script.

    WHEN the runtime reads meta
    THEN only comments precede it and it carries name and description
    """
    content = WORKFLOW.read_text()
    match = re.search(r"^export\s+const\s+meta\s*=", content, re.MULTILINE)
    assert match is not None
    for line in content[: match.start()].splitlines():
        stripped = line.strip()
        assert not stripped or stripped.startswith(("//", "/*", "*", "*/"))
    meta = content[match.end() : content.index("\n}\n", match.end())]
    assert "name:" in meta
    assert "description:" in meta


def test_the_script_stops_before_the_implementer() -> None:
    """GIVEN subagents that run in acceptEdits regardless of session mode.

    WHEN the analysis workflow runs
    THEN it dispatches no implementer and no validator agent

    Editing from inside a workflow applies changes nobody saw proposed,
    and the script has no shell, so it could not verify them either.
    """
    content = WORKFLOW.read_text()
    for editing_agent in (
        "workflow-improvement-implementer-agent",
        "workflow-improvement-validator-agent",
    ):
        assert f"agentType: 'sanctum:{editing_agent}'" not in content
        assert f'agentType: "sanctum:{editing_agent}"' not in content


def test_the_return_refuses_to_be_evidence() -> None:
    """GIVEN acceptance criteria that no command checked.

    WHEN the workflow returns its plan
    THEN it says so, and sends the criteria back to the session
    """
    content = WORKFLOW.read_text()
    assert "no acceptance criterion above has been checked" in content


def test_the_command_explains_when_to_use_which_path() -> None:
    """GIVEN a command that can run agents directly or as a pipeline.

    WHEN a reader reaches Phase 1
    THEN both paths are named, with the reason the script stops early
    """
    command = COMMAND.read_text()
    assert "workflows/fix-workflow-analysis.js" in command
    assert "a workflow never starts unasked" in command
    assert "acceptEdits" in command
