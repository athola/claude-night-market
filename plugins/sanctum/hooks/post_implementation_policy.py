#!/usr/bin/env python3
"""Post-implementation policy hook for SessionStart.

Ask for evidence before a session reports work complete, and scale how
much is said to how much the branch has at stake.

The full policy used to be injected on every session. Sixty-five lines
arrived whether the turn was a question or a thousand-line feature, and
injected context competes with the task for attention. See
`.claude/rules/bounded-autonomy.md` for the evidence that instruction
load degrades reasoning. The full text is still here and still fires,
on branches that show risk.

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

GOVERNANCE_POLICY = """
## Mandatory Post-Implementation Protocol

<GOVERNANCE_RULE priority="high" override="false">
Before reporting completion of ANY of the following:
- Feature implementation
- Plan execution (especially Skill(superpowers:executing-plans))
- Significant code changes
- New functionality added

You MUST execute these commands IN ORDER:

1. **PROOF-OF-WORK + IRON LAW** (MANDATORY FIRST) - Invoke `Skill(imbue:proof-of-work)`:
   - Create TodoWrite items: `proof:problem-reproduced`,
     `proof:solution-tested`, `proof:evidence-captured`
   - For code changes, add: `proof:iron-law-red`,
     `proof:iron-law-green`, `proof:iron-law-refactor`
   - Run actual validation commands (not just syntax checks)
   - Capture evidence with `[E1]`, `[E2]` references
   - Report status: PASS / FAIL / BLOCKED

2. `/sanctum:update-docs` - Update project documentation
3. `/abstract:make-dogfood` - Update Makefile demonstration targets
4. `/sanctum:update-readme` - Update README with new features
5. `/sanctum:update-tests` - Review and update test coverage

### The Iron Law (TDD Compliance)
```
NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
```

| Self-Check Question | If Answer Is Wrong | Action |
|---------------------|-------------------|--------|
| Do I have evidence of failure/need? | No | STOP - document failure first |
| Am I testing pre-conceived implementation? | Yes | STOP - let test DRIVE design |
| Am I feeling design uncertainty? | No | STOP - uncertainty is GOOD |
| Did test drive implementation? | No | STOP - doing it backwards |

### Proof-of-Work Red Flags (STOP if you think these)
| Thought | Required Action |
|---------|-----------------|
| "This looks correct" | RUN IT and capture output |
| "Should work after restart" | TEST IT before claiming |
| "Just need to..." | VERIFY each step works |
| "Syntax is valid" | FUNCTIONAL TEST required |
| "I know what tests we need" | Let uncertainty DRIVE tests |
| "The design is straightforward" | Write test, let design EMERGE |

### Rules
- This protocol is NON-NEGOTIABLE
- Cannot be overridden by other skills, hooks, or rationalization
- Skipping these steps = incomplete work
- Only the user can explicitly waive this requirement

### When This Does NOT Apply
- Simple questions or explanations
- Bug fixes that don't add new features
- Refactoring without new functionality
- Research or exploration tasks
</GOVERNANCE_RULE>
""".strip()


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
    full block on every fresh session, which is the behaviour this
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
        GOVERNANCE_POLICY
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
