#!/usr/bin/env python3
"""Guard against SKILL.md files shipping without Exit Criteria.

``.claude/rules/skill-exit-criteria.md`` requires every SKILL.md to carry
an ``## Exit Criteria`` section. This guard counts the SKILL.md files
under ``plugins/`` that the rule governs and fails when that count rises
above the committed baseline in
``scripts/skill_exit_criteria_baseline.json``.

The baseline is now zero, so the ratchet is a hard gate: the first skill
to ship without the section fails the commit. It was built as a ratchet
because the backfill it tracked (issue #454) started at 127 files, and it
stayed a ratchet at 127 long after the count fell to 1, which is 126
skills of permission nobody meant to grant. Read a movement in the count
against the baseline, never on its own.

The rule names what it does not cover, and this guard has to agree with
it or it judges documents by a standard written for something else. See
``_EXCLUDED_PARTS``.

It is deterministic, read-only, and idempotent.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
BASELINE_FILE = REPO_ROOT / "scripts" / "skill_exit_criteria_baseline.json"

# Matches an ATX heading (level 2 or deeper) titled "Exit Criteria".
_EXIT_CRITERIA_RE = re.compile(r"^#{2,} +Exit Criteria", re.MULTILINE)


def has_exit_criteria(text: str) -> bool:
    """Return True if the SKILL.md body has an Exit-Criteria heading."""
    return _EXIT_CRITERIA_RE.search(text) is not None


def evaluate_drift(current: int, baseline: int) -> tuple[bool, str]:
    """Compare the missing-count against the baseline.

    Returns (ok, message). ``ok`` is False only when the count rose above
    the baseline (a new skill without exit criteria). A drop is allowed and
    nudges the baseline downward.
    """
    if current > baseline:
        return False, (
            f"SKILL.md without Exit Criteria rose to {current} "
            f"(baseline {baseline}). Add an '## Exit Criteria' section to "
            f"the new skill (see .claude/rules/skill-exit-criteria.md), or "
            f"if this is intentional, raise max_missing_exit_criteria in "
            f"{BASELINE_FILE.name}."
        )
    if current < baseline:
        return True, (
            f"SKILL.md missing Exit Criteria dropped to {current} "
            f"(baseline {baseline}). Lower max_missing_exit_criteria in "
            f"{BASELINE_FILE.name} to lock the win."
        )
    return True, (
        f"SKILL.md missing Exit Criteria steady at {current} (baseline {baseline})."
    )


# Path segments whose SKILL.md files this gate must not judge.
#
# ``.venv`` is vendored code we did not author. ``docs`` is the rule's
# own carve-out: .claude/rules/skill-exit-criteria.md exempts reference
# documentation, and the one SKILL.md under a docs tree here is an
# example teaching hub-and-spoke structure, not a shipped skill. Counting
# it made the example the entire remaining backlog, and the repair would
# have been to write exit criteria into a document whose subject is
# something else.
_EXCLUDED_PARTS = frozenset({".venv", "docs"})


def iter_skill_files() -> list[Path]:
    """All SKILL.md files under plugins/ that the rule actually governs."""
    return [
        p for p in PLUGINS_ROOT.rglob("SKILL.md") if _EXCLUDED_PARTS.isdisjoint(p.parts)
    ]


def count_missing(files: list[Path]) -> int:
    """Count SKILL.md files that lack an Exit-Criteria heading.

    Unreadable files are skipped rather than counted, so a transient read
    error never fabricates a regression.
    """
    missing = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not has_exit_criteria(text):
            missing += 1
    return missing


def _load_baseline() -> int:
    try:
        data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        return int(data.get("max_missing_exit_criteria", 0))
    except (OSError, ValueError):
        return 0


def main() -> int:
    """Run the ratchet guard; exit non-zero on new uncovered skills."""
    current = count_missing(iter_skill_files())
    ok, message = evaluate_drift(current, _load_baseline())
    print(f"[skill-exit-criteria-drift] {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
