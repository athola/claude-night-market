#!/usr/bin/env python3
"""Ratchet guard against new dangling Skill() references.

Reuses ``plugins/abstract/scripts/skill_graph.py`` to count genuine
broken ``Skill(plugin:name)`` references (the ``bugs`` category, which
excludes legitimate cross-marketplace ``external`` refs and template
``placeholders``). Fails the commit only when that count rises above the
committed baseline in ``scripts/skill_graph_baseline.json``.

This stops new breakage without forcing a cleanup of the pre-existing
dangling refs. When the count drops, the guard passes and nudges you to
lower the baseline so the ratchet tightens.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_GRAPH = REPO_ROOT / "plugins" / "abstract" / "scripts" / "skill_graph.py"
BASELINE_FILE = REPO_ROOT / "scripts" / "skill_graph_baseline.json"


def count_dangling_bugs(report: dict) -> int:
    """Count genuine broken refs (the ``bugs`` category only)."""
    return len(report.get("dangling_refs", {}).get("bugs", []))


def count_uncalled_libraries(report: dict) -> int:
    """Count library-role skills with no inbound ``Skill()`` consumer.

    These are the AP-3 risk that ``shared-utility-consumer-rule.md``
    targets: scaffolding for hypothetical composition that never
    materialises.
    """
    return len(report.get("uncalled_libraries", []))


def evaluate_drift(current: int, baseline: int) -> tuple[bool, str]:
    """Compare the current bug count against the baseline.

    Returns (ok, message). ``ok`` is False only when the count rose
    above the baseline (new breakage). A drop is allowed and nudges the
    baseline downward.
    """
    if current > baseline:
        return False, (
            f"New dangling Skill() reference(s): {current} broken refs "
            f"(baseline {baseline}). Fix the new reference, or if it is "
            f"intentional, update {BASELINE_FILE.name}."
        )
    if current < baseline:
        return True, (
            f"Dangling refs dropped to {current} (baseline {baseline}). "
            f"Lower max_dangling_bugs in {BASELINE_FILE.name} to lock the win."
        )
    return True, f"Dangling refs steady at {current} (baseline {baseline})."


def evaluate_uncalled(current: int, baseline: int) -> tuple[bool, str]:
    """Compare the uncalled-library count against the baseline.

    Returns (ok, message). ``ok`` is False only when the count rose above
    the baseline. A new library skill legitimately starts uncalled, so the
    escape hatch is to raise the baseline -- which records the 30-day grace
    period that ``shared-utility-consumer-rule.md`` already grants.
    """
    if current > baseline:
        return False, (
            f"New uncalled library skill(s): {current} library-role skills "
            f"with no inbound Skill() consumer (baseline {baseline}). Wire a "
            f"consumer (shared-utility-consumer-rule), or if this is a new "
            f"library inside its grace period, raise max_uncalled_libraries "
            f"in {BASELINE_FILE.name}."
        )
    if current < baseline:
        return True, (
            f"Uncalled libraries dropped to {current} (baseline {baseline}). "
            f"Lower max_uncalled_libraries in {BASELINE_FILE.name} to lock "
            f"the win."
        )
    return True, f"Uncalled libraries steady at {current} (baseline {baseline})."


def _load_baseline(key: str, default: int = 0) -> int:
    try:
        data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        return int(data.get(key, default))
    except (OSError, ValueError):
        return default


def _run_skill_graph() -> dict:
    result = subprocess.run(  # noqa: S603 - fixed, repo-local script path
        [
            sys.executable,
            str(SKILL_GRAPH),
            "--format",
            "json",
            "--plugins-root",
            str(REPO_ROOT / "plugins"),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return data if isinstance(data, dict) else {}


def main() -> int:
    """Run the ratchet guard; exit non-zero on new breakage."""
    try:
        report = _run_skill_graph()
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        # Never block a commit because the analyzer itself failed.
        print(f"[skill-graph-drift] skipped (analyzer error): {exc}")
        return 0

    ok_bugs, bug_message = evaluate_drift(
        count_dangling_bugs(report), _load_baseline("max_dangling_bugs")
    )
    ok_uncalled, uncalled_message = evaluate_uncalled(
        count_uncalled_libraries(report), _load_baseline("max_uncalled_libraries")
    )
    print(f"[skill-graph-drift] {bug_message}")
    print(f"[skill-graph-drift] {uncalled_message}")
    return 0 if (ok_bugs and ok_uncalled) else 1


if __name__ == "__main__":
    raise SystemExit(main())
