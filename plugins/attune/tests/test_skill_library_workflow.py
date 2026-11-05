"""The shipped skill-library workflow must keep its write boundaries.

Two are safety properties. The script may create new files, because that
is the deliverable, but it must not carry a fixer, which edits files that
already exist. And it must not use worktree isolation, because the writes
are disjoint by construction and the isolation would be cost without a
conflict to prevent.
"""

from __future__ import annotations

import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = PLUGIN_ROOT / "workflows" / "skill-library.js"


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


def test_authoring_agents_carry_a_write_fence() -> None:
    """GIVEN subagents that run in acceptEdits.

    WHEN an authoring agent is dispatched
    THEN its prompt fences writes to the skill's own new directory
    """
    content = WORKFLOW.read_text()
    assert "Write fence: create files only under" in content
    assert "Do not modify any file that already exists" in content


def test_no_worktree_isolation_for_disjoint_writes() -> None:
    """GIVEN one new directory per skill.

    WHEN the authoring agents run in parallel
    THEN no worktree is cut, because there is no conflict to prevent

    `.claude/rules/plan-before-large-dispatch.md`: agents modifying
    disjoint files skip isolation. Adding it here would buy a worktree
    per skill and prevent nothing.
    """
    # The word appears in the header comment explaining the choice; what
    # must be absent is the option itself.
    assert "isolation:" not in WORKFLOW.read_text()


def test_the_fixer_stays_in_the_session() -> None:
    """GIVEN findings that require editing files that already exist.

    WHEN the workflow finishes
    THEN it returns them instead of applying them
    """
    content = WORKFLOW.read_text()
    assert "Apply the findings in the session, not here." in content
    assert "Nothing above was verified by running anything." in content


PROTOCOL = (
    PLUGIN_ROOT / "skills" / "skill-library-mission" / "modules" / "review-protocol.md"
)


def test_review_lenses_match_the_protocol_the_skill_promises() -> None:
    """GIVEN the review protocol the skill's exit criteria name.

    WHEN the workflow dispatches its reviewers
    THEN it runs exactly the protocol's lenses, so the mission can meet
    "All three review lenses ran"
    """
    protocol = re.findall(r"^\| ([A-Z]+) \|", PROTOCOL.read_text(), re.MULTILINE)
    content = WORKFLOW.read_text()
    block = content[
        content.index("const LENSES = [") : content.index("phase('Author')")
    ]
    keys = re.findall(r"key: '([a-z]+)'", block)
    assert [k.upper() for k in keys] == protocol


def test_authoring_prompt_asks_for_the_provenance_section() -> None:
    """GIVEN the exit criterion that every skill ends with provenance.

    WHEN an authoring agent is dispatched
    THEN its prompt asks for that section by name
    """
    assert "Provenance and maintenance" in WORKFLOW.read_text()
