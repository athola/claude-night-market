"""Gate: what SessionStart injects stays small enough to inject always.

Eight plugins register `SessionStart`, and whatever they print is
prepended to every session before the user has said what the session is
for. Three of them carried reference manuals -- 9,973 of the 10,770
characters measured across the set -- so most sessions paid for guidance
about work they were never going to do.

`.claude/rules/bounded-autonomy.md` is the reason this gate exists rather
than a style note. It cites a STAR-structured prompt that scored 100% on
a reasoning task alone and 0% inside a 60-line production prompt grown by
iterative additions of style and format instructions, and names this
repository's session-start injections as the same shape. A second paper
it cites found that a constraint the model was *already satisfying* still
cost accuracy. Injected text is not free when it is right.

The budget is what stops regrowth. Detail belongs in a skill body, which
is loaded when the task calls for it; the injection should be the pointer.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Per-hook ceiling on injected characters. Each was set just above what
# the trimmed payload measures, so a manual cannot creep back without
# turning this red.
BUDGETS = {
    "conserve/hooks/session-start.sh": 1200,
    "imbue/hooks/session-start.sh": 1400,
}

HOOK_INPUT = json.dumps({"session_id": "budget-probe", "source": "startup"})


def _injected_context(hook: Path) -> str:
    """Run *hook* as Claude Code would and return what it injects."""
    result = subprocess.run(
        ["bash", str(hook)],
        input=HOOK_INPUT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    return payload["hookSpecificOutput"]["additionalContext"]


@pytest.mark.parametrize(("relative_path", "budget"), sorted(BUDGETS.items()))
def test_injection_stays_within_budget(relative_path: str, budget: int) -> None:
    """Scenario: a session-start payload cannot grow back into a manual."""
    context = _injected_context(REPO_ROOT / "plugins" / relative_path)
    assert len(context) <= budget, (
        f"{relative_path} injects {len(context)} chars into every session "
        f"(budget {budget}). Move the detail into a skill body and inject a "
        "pointer to it."
    )


@pytest.mark.parametrize("relative_path", sorted(BUDGETS))
def test_injection_still_routes_to_a_skill(relative_path: str) -> None:
    """Scenario: trimming did not leave a payload that points nowhere.

    A budget alone is satisfied by deleting the text. The injection has
    to still say which skill carries what was removed.
    """
    context = _injected_context(REPO_ROOT / "plugins" / relative_path)
    assert "Skill(" in context, f"{relative_path} names no skill to route to"


def test_the_two_hooks_do_not_both_carry_scope_guard() -> None:
    """Scenario: the same quick reference is not injected twice.

    conserve's payload used to end with a "Scope-Guard Principles (from
    imbue)" section restating imbue's own injection, so every session
    paid for the worthiness formula and the branch thresholds twice.
    """
    conserve = _injected_context(REPO_ROOT / "plugins/conserve/hooks/session-start.sh")
    assert "imbue:scope-guard" not in conserve, (
        "conserve injects imbue's scope-guard reference; imbue already does"
    )
