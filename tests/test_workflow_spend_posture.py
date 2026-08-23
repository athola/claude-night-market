"""The workflow spend posture must be a setting, not just a paragraph.

`.claude/rules/plan-before-large-dispatch.md` states two decisions about
how much a dynamic workflow may spend here: the size guideline is pinned
to a named value rather than inherited, and `ultracode` is deliberately
left unset so no workflow starts unasked.

Both live in `.claude/settings.json`, which nothing else reads at test
time. The rule that documents them is prose, and the sibling suite
`test_catalog_rules_mirror_canonical.py` was written for exactly this
failure: a prose note saying what should hold, with nothing that goes
red when it stops holding. This is that guard for the spend posture.

The documented values come from the workflows page of the Claude Code
docs, read 2026-08-23 against CLI 2.1.241.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SETTINGS = REPO_ROOT / ".claude" / "settings.json"
RULE = REPO_ROOT / ".claude" / "rules" / "plan-before-large-dispatch.md"

DOCUMENTED_VALUES = {"unrestricted", "small", "medium", "large"}


def _settings() -> dict:
    return json.loads(SETTINGS.read_text())


def test_size_guideline_is_pinned_to_a_documented_value() -> None:
    """An unpinned guideline is inherited, which is what R8 rejected."""
    value = _settings().get("workflowSizeGuideline")
    assert value is not None, (
        "`.claude/settings.json` must pin `workflowSizeGuideline`; "
        "without it the repo silently inherits whatever the default becomes"
    )
    assert value in DOCUMENTED_VALUES, (
        f"{value!r} is not one of the documented values {sorted(DOCUMENTED_VALUES)}"
    )


def test_the_rule_names_the_value_the_settings_file_sets() -> None:
    """Prose and configuration drift apart unless something compares them."""
    value = _settings()["workflowSizeGuideline"]
    quoted = re.findall(r"`workflowSizeGuideline`\s*\n?to `([a-z]+)`", RULE.read_text())
    assert quoted, "the rule must name the guideline value it documents"
    assert quoted[0] == value, (
        f"the rule documents `{quoted[0]}` but settings.json sets `{value}`"
    )


def test_ultracode_is_not_enabled_in_project_settings() -> None:
    """`ultracode` would plan a workflow per task, unasked.

    The first constraint in the rule is that a workflow never starts
    without being requested. Enabling `ultracode` for everyone who clones
    the repo would void it for every substantive turn.
    """
    assert "ultracode" not in _settings(), (
        "`ultracode` must stay unset in project settings: enabling it starts "
        "a workflow for every substantive task, which the dispatch rule forbids"
    )
