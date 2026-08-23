"""The shipped unified-review workflow must stay loadable and referenced.

A workflow script is discovered by convention from `workflows/` at the
plugin root. Nothing at runtime reports a malformed one back to this
repository, so the contract is checked here.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PLUGIN_ROOT / "workflows" / "unified-review.js"
SKILL = PLUGIN_ROOT / "skills" / "unified-review" / "SKILL.md"


def test_workflow_ships_at_the_discovered_location() -> None:
    """GIVEN the plugin as installed.

    WHEN the harness looks for workflows
    THEN it finds one at workflows/ in the plugin root
    """
    assert WORKFLOW.is_file()


def test_meta_declares_name_and_description_before_any_statement() -> None:
    """GIVEN the shipped script.

    WHEN the runtime reads its meta block
    THEN meta is the first statement and carries name and description

    Only comments may precede it. This mirrors the check in
    abstract's validate_plugin.py, so a break shows up in this
    plugin's own suite rather than only in a cross-plugin gate.
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


def test_the_script_states_that_it_is_not_an_evidence_gate() -> None:
    """GIVEN a workflow that cannot run a command.

    WHEN it returns findings
    THEN the return says they are claims, not proof-of-work evidence
    """
    content = WORKFLOW.read_text()
    assert "proof-of-work evidence" in content
    assert "Reproduce before acting" in content


def test_the_skill_offers_the_workflow_as_a_second_path() -> None:
    """GIVEN the skill that owns this review.

    WHEN a reader reaches the isolation rule
    THEN both paths are named, and the workflow is not the default
    """
    skill = SKILL.read_text()
    assert "workflows/unified-review.js" in skill
    assert "a workflow never starts unasked" in skill
