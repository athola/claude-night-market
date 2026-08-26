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

One principle decides which of these keys the repo may set: project
settings may bound what a workflow spends, not enable the capability
that spends it. `workflowSizeGuideline` bounds, so it is pinned.
`enableWorkflows`, `disableWorkflows` and `ultracode` turn a billable
feature on or off for whoever clones the repo, so they stay unset and
the person decides.

The documented values come from the workflows page of the Claude Code
docs, read 2026-08-23, and were confirmed against CLI 2.1.241 by feeding
the harness an out-of-range value and reading back the rejection.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

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


def test_enable_and_disable_workflows_stay_unset() -> None:
    """Bounding a workflow is the repo's call. Enabling one is not.

    Both keys are booleans this CLI validates, and both switch the
    feature itself on or off against the plan default. Setting either in
    project settings would decide for everyone who clones the repo
    whether their account has a token-expensive capability turned on.
    That is a spend decision belonging to the person, not the checkout.
    """
    settings = _settings()
    for key in ("enableWorkflows", "disableWorkflows"):
        assert key not in settings, (
            f"`{key}` must stay unset in project settings: it enables or "
            "disables the feature for everyone who clones the repo, which is "
            "the contributor's decision, not this file's"
        )


def test_the_harness_accepts_this_repos_settings_file() -> None:
    """The pinned value has to satisfy the schema that actually reads it.

    `claude doctor` parses settings files in the working directory and
    prints an `Invalid settings` line naming the offending file and key.
    Only lines naming this repo's file are checked, so a contributor with
    a broken `~/.claude/settings.json` does not fail this suite for a
    problem in their own configuration.

    A CLI too old to know `workflowSizeGuideline` ignores it silently
    rather than complaining, so this passes there too. It goes red in the
    one case worth catching: a CLI that knows the key and rejects the
    value this repo pins.
    """
    binary = shutil.which("claude")
    if binary is None:
        pytest.skip("the claude CLI is not on PATH")

    try:
        result = subprocess.run(
            [binary, "doctor"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        pytest.skip(f"claude doctor did not complete: {exc}")

    output = result.stdout + result.stderr
    offending = [
        line
        for line in output.splitlines()
        if str(SETTINGS) in line and "Invalid" in line
    ]
    assert not offending, (
        "the harness rejected this repo's settings file:\n" + "\n".join(offending)
    )
