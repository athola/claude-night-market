#!/usr/bin/env python3
"""Post-implementation policy hook for SessionStart.

Ask for evidence before a session reports work complete, and say what
this branch actually looks like.

Two things changed from the original. The block no longer fires at full
volume on every turn: it scales to what the branch has at stake. And
the escalated form now leads with the measurement that triggered it,
because that is the only part a session cannot work out for itself.

What it dropped were two rationalization tables and the line "Cannot be
overridden by other skills, hooks, or rationalization". A repository
rule forbidding those while its own session-start hook injected them
was a contradiction the hook won, because a hook fires and a rule waits
to be read. See `.claude/rules/bounded-autonomy.md`.

Read `agent_type` from hook input (Claude Code 2.1.2+) to customize policy injection.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
from pathlib import Path

# A branch past this many changed lines has enough at stake to be worth
# the full text. Below it, the reminder carries the same practice.
LARGE_BRANCH_LINES = 500

_TEST_PATH_MARKERS = ("test_", "_test.", "/tests/", "spec.", ".spec.")

# git diff --numstat emits added, removed, path per line.
_NUMSTAT_FIELDS = 3

# Lightweight agents that skip full governance policy
LIGHTWEIGHT_AGENTS = frozenset(
    {
        "quick-query",
        "simple-task",
        "code-reviewer",  # Review agents don't implement features
        "architecture-reviewer",
        "rust-auditor",
        "bloat-auditor",
        "context-optimizer",  # Optimization agents don't add features
    }
)

SHORT_REMINDER = """
## Before Reporting Work Complete

Run it. Paste what it printed. Evidence is the output, not the
assertion: "should work" is the phrasing that precedes finding out it
does not.

Tests come first here by default. Where they did not, say so and say
why, rather than leaving the reader to notice.

After a feature lands these often need updating, and which ones apply
is a judgment call: `/sanctum:update-docs`, `/sanctum:update-tests`,
`/sanctum:update-readme`, `/abstract:make-dogfood`.

Not for questions, refactors, or exploration.
""".strip()

RISK_POLICY = """
## Signals on This Branch

{signals}

That is the reason this is here. It is a measurement, not a verdict:
a large branch can be correct and an untested one can be deliberate.

Before reporting this complete:

- Run what you changed and paste what it printed. Evidence is the
  output, not the assertion.
- Tests come first here by default. Where they did not, say so and say
  why, rather than leaving the reader to notice.
- A change this size usually moves the surface around it. Which of
  these apply is your call: `/sanctum:update-docs`,
  `/sanctum:update-tests`, `/sanctum:update-readme`,
  `/abstract:make-dogfood`.

Exit criteria:

- [ ] Every claim that something works has command output behind it
- [ ] New behavior has a test, or its absence is explained
- [ ] The surface above is updated, or knowingly left alone

Not for questions, refactors, or exploration.
""".strip()


def format_risk_policy(changed_lines: int, *, tests_touched: bool) -> str:
    """Fill the escalated policy with the numbers that triggered it.

    The signal line is the only content here a session cannot
    reconstruct for itself. Advice about evidence is general knowledge;
    "912 lines changed, no test file touched" is a fact about this
    working tree at this moment, and it is what makes the escalation
    legible rather than arbitrary.

    Naming the wrong signal would be worse than naming none, so a large
    branch that does touch tests is told about its size only.
    """
    signals = [f"- {changed_lines} lines changed against HEAD"]
    if not tests_touched:
        signals.append("- no test file among them")
    return RISK_POLICY.format(signals="\n".join(signals))


def measure_branch() -> tuple[int, bool]:
    """Return the branch's changed-line count and whether tests moved.

    Reports (0, False) for anything git cannot answer: a directory that
    is not a repository, a missing binary, a slow filesystem. Not
    knowing the size of a change is not evidence that it is large, and
    the short reminder still carries the practice, so guessing wrong
    here costs a smaller prompt rather than a missing one.
    """
    try:
        result = subprocess.run(  # nosec B603 B607
            ["git", "diff", "--numstat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return 0, False

    if result.returncode != 0:
        return 0, False

    changed = 0
    tests_touched = False
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != _NUMSTAT_FIELDS:
            continue
        added, removed, path = parts
        # Binary files report "-" for both counts.
        changed += sum(int(n) for n in (added, removed) if n.isdigit())
        candidate = f"/{Path(path).as_posix()}"
        if any(marker in candidate for marker in _TEST_PATH_MARKERS):
            tests_touched = True

    return changed, tests_touched


def needs_full_policy(changed_lines: int, *, tests_touched: bool) -> bool:
    """Decide whether this branch has enough at stake for the full text.

    A branch with nothing on it is the case worth naming: no tests have
    been touched there either, and reading that as risk would fire the
    full block on every fresh session, which is the behavior this
    replaces.
    """
    if changed_lines == 0:
        return False
    return changed_lines > LARGE_BRANCH_LINES or not tests_touched


def main() -> None:
    """Inject governance policy at session start.

    Read hook input from stdin to check for agent_type (Claude Code 2.1.2+).
    Skip the full governance policy for lightweight agents to reduce context overhead.
    """
    # Read hook input from stdin (Claude Code 2.1.2+)
    agent_type = ""
    try:
        input_data = sys.stdin.read().strip()
        if input_data:
            hook_input = json.loads(input_data)
            agent_type = hook_input.get("agent_type", "")
    except (OSError, json.JSONDecodeError) as e:
        # Gracefully handle missing or malformed input
        # Log to stderr for debugging (doesn't break hook output)
        print(f"[DEBUG] Hook input parse failed: {e}", file=sys.stderr)

    # Skip full governance for lightweight agents
    if agent_type in LIGHTWEIGHT_AGENTS:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": (
                    f"[sanctum] Agent '{agent_type}'"
                    " - governance policy deferred"
                    " (review/optimization agent)."
                ),
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    changed_lines, tests_touched = measure_branch()
    policy = (
        format_risk_policy(changed_lines, tests_touched=tests_touched)
        if needs_full_policy(changed_lines, tests_touched=tests_touched)
        else SHORT_REMINDER
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": policy,
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
