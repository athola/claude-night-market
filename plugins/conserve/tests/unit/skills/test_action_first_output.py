"""Structural tests for the action-first-output skill.

The skill ports ayghri/i-have-adhd (MIT) into conserve. These tests guard
the three things that make the port load-bearing rather than decorative:

1. The skill exists, is registered in plugin.json, and carries the repo's
   mandatory Exit Criteria section.
2. It documents the behaviors that response-compression does NOT cover
   (next-action leads, state restatement, time estimates, escape hatches).
3. It resolves the two direct conflicts with response-compression, and
   response-compression points back at it. Without this, both skills fire
   on the same turn and contradict each other on "Next steps:" and recaps.

The precedence tests assert that a resolution EXISTS and names both
skills. They deliberately do not pin the specific policy, so the policy
can be retuned without rewriting tests.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[3]
SKILL = PLUGIN / "skills" / "action-first-output" / "SKILL.md"
COMPRESSION = PLUGIN / "skills" / "response-compression" / "SKILL.md"
MANIFEST = PLUGIN / ".claude-plugin" / "plugin.json"


@pytest.fixture(scope="module")
def skill_text() -> str:
    assert SKILL.is_file(), f"missing skill: {SKILL}"
    return SKILL.read_text(encoding="utf-8")


def test_frontmatter_is_valid(skill_text):
    assert skill_text.startswith("---\n"), "skill needs YAML frontmatter"
    head = skill_text.split("---", 2)[1]
    for field in ("name:", "description:", "category:"):
        assert field in head, f"frontmatter missing {field}"
    assert "name: action-first-output" in head


def test_registered_in_plugin_manifest():
    skills = json.loads(MANIFEST.read_text(encoding="utf-8"))["skills"]
    assert "./skills/action-first-output" in skills


def test_has_exit_criteria(skill_text):
    assert "## Exit Criteria" in skill_text, "repo rule: every SKILL.md needs one"


def test_credits_upstream_source(skill_text):
    """MIT-licensed port. Attribution is a license obligation, not a nicety."""
    assert "ayghri/i-have-adhd" in skill_text
    assert "MIT" in skill_text


@pytest.mark.parametrize(
    "behavior",
    [
        "next action",  # rule 1: lead with the action
        "time estimate",  # rule 6: concrete units, not "some work"
        "5 items",  # rule 9: cap and rank
    ],
)
def test_documents_behaviors_absent_from_response_compression(skill_text, behavior):
    assert behavior in skill_text.lower(), f"skill should cover: {behavior}"


def test_documents_persistence_and_off_switch(skill_text):
    """The skill is sticky. A sticky skill with no off switch is a trap."""
    lowered = skill_text.lower()
    assert "stop adhd mode" in lowered or "normal mode" in lowered
    assert "persist" in lowered


def test_documents_escape_hatches(skill_text):
    """Brevity must lose to safety, explanation, and real ambiguity."""
    lowered = skill_text.lower()
    assert "destructive" in lowered, "safety must outrank brevity"
    assert "explain" in lowered, "explicit explain requests override the shape"
    assert "ambigu" in lowered, "one clarifying question beats guessing"


def test_resolves_conflict_with_response_compression(skill_text):
    """The two skills disagree on 'Next steps:' and on recaps.

    Both directions of the cross-reference must exist, or a reader lands
    on one skill and never learns the other one contradicts it.
    """
    assert "response-compression" in skill_text
    assert "## Precedence" in skill_text
    # The two contested behaviors must both be named in the resolution.
    precedence = skill_text.split("## Precedence", 1)[1]
    lowered = precedence.lower()
    assert "next step" in lowered, "resolve the 'Next steps:' disagreement"
    assert "restate" in lowered or "recap" in lowered, "resolve the recap disagreement"


def test_restatement_never_degrades_under_context_pressure(skill_text):
    """Restatement is ~16 tok/turn. Dropping it saves noise and costs state.

    The policy contract: full form at every pressure tier, promoted into
    the clear-context handoff at EMERGENCY. These assertions pin the
    contract (all four tiers addressed, an explicit never-drop
    invariant, and the handoff link) without pinning the prose.
    """
    precedence = skill_text.split("## Precedence", 1)[1]
    lowered = precedence.lower()

    for tier in ("ok", "warning", "critical", "emergency"):
        assert tier in lowered, f"policy must address the {tier.upper()} tier"

    assert "never drop" in lowered, "the never-drop invariant must be explicit"
    assert "clear-context" in lowered, "EMERGENCY must route to the handoff skill"
    assert "handoff" in lowered


def test_restatement_policy_is_backed_by_measured_cost(skill_text):
    """A policy that overrides a sibling skill must show its arithmetic."""
    precedence = skill_text.split("## Precedence", 1)[1]
    assert "16 tokens" in precedence, "state the measured per-turn cost"
    assert "%" in precedence, "state the cost as a share of the window"


def test_response_compression_points_back():
    text = COMPRESSION.read_text(encoding="utf-8")
    assert "action-first-output" in text, (
        "response-compression must warn that action-first-output overrides "
        "its no-next-steps and no-recap rules when active"
    )


# --- Silent-failure guards -------------------------------------------------
# The four tests below guard invariants whose breakage produces no error.
# Each one, if violated, leaves a skill that loads fine and misbehaves.


def test_skill_never_self_invokes(skill_text):
    """A sticky, session-wide skill must never self-invoke.

    Given a skill that rewrites output style for a whole session,
    When its frontmatter is read,
    Then model invocation must be disabled.

    Without this flag the skill auto-fires on a keyword match and silently
    restyles every subsequent turn. Nothing errors. The reader simply gets
    an output contract they never asked for.
    """
    head = skill_text.split("---", 2)[1]
    assert "disable-model-invocation: true" in head, (
        "action-first-output is sticky and session-wide; it must be "
        "explicitly invoked, never model-triggered"
    )


def test_pressure_thresholds_match_the_skills_that_own_them():
    """Cited pressure thresholds must match the skills that own them.

    Given a Precedence table citing context-pressure percentages,
    When those percentages are compared to their owning skills,
    Then they must agree.

    The 50% and 80% figures belong to context-optimization and
    clear-context. Hardcoding them here couples three documents. This
    test fails when the owners retune and this table goes stale.
    """
    precedence = SKILL.read_text(encoding="utf-8").split("## Precedence", 1)[1]
    clear_ctx = (PLUGIN / "skills" / "clear-context" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    ctx_opt = (PLUGIN / "skills" / "context-optimization" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    assert "80%" in precedence, "EMERGENCY tier must state its threshold"
    assert "80%" in clear_ctx, "clear-context no longer documents an 80% trigger"
    assert "50%" in precedence, "CRITICAL tier must state its threshold"
    assert "50%" in ctx_opt, "context-optimization no longer documents 50% CRITICAL"


@pytest.mark.parametrize("rule_number", range(1, 11))
def test_all_ten_rules_survive(skill_text, rule_number):
    """Each of the ten ported rules must still be present.

    Given the ported ruleset has exactly ten rules,
    When any single rule heading is removed,
    Then this test fails.

    Deleting a rule costs a capability (tangent suppression, error tone)
    without breaking anything that would surface in review.
    """
    assert f"### {rule_number}." in skill_text, f"rule {rule_number} is missing"


def test_every_cross_referenced_skill_resolves(skill_text):
    """Every sibling skill referenced must exist on disk.

    Given the skill routes readers to sibling skills,
    When each Skill(plugin:name) reference is resolved on disk,
    Then every target must exist.

    A dangling reference sends the reader nowhere and inflates the
    repo-wide skill-graph drift count.
    """
    refs = set(re.findall(r"`?Skill\(([a-z0-9-]+):([a-z0-9-]+)\)`?", skill_text))
    assert refs, "skill should route to siblings"
    plugins_root = PLUGIN.parent
    missing = [
        f"{plugin}:{name}"
        for plugin, name in refs
        if not (plugins_root / plugin / "skills" / name / "SKILL.md").is_file()
    ]
    assert not missing, f"dangling Skill() references: {missing}"
