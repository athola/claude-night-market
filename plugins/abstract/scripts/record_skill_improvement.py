#!/usr/bin/env python3
"""Version an improved skill and open its evaluation window (ADR-0006).

The skill-improver agent runs this after editing a SKILL.md. It bumps
the frontmatter ``adaptation`` version with the skill's current
stability gap as the baseline, then marks the skill ``evaluating`` in
the improvement queue. The homeostatic monitor hook counts the next
executions against that baseline and promotes the change or sends it
to rollback review.

Needs PyYAML, so run it under the plugin environment:
``uv run --directory plugins/abstract python scripts/record_skill_improvement.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PLUGIN = Path(__file__).resolve().parent.parent
for _path in (_PLUGIN / "src", _PLUGIN / "hooks"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from abstract.improvement_queue import ImprovementQueue
from abstract.paths import get_improvement_queue_path, get_log_directory
from abstract.skill_versioning import SkillVersionManager
from abstract.stdlib_helpers import safe_json_load
from shared.stability import stability_gap


def skill_ref_for(skill_file: Path) -> str | None:
    """Return ``plugin:skill`` for ``<plugin>/skills/<skill>/SKILL.md``."""
    skill_dir = skill_file.resolve().parent
    if skill_file.name != "SKILL.md" or skill_dir.parent.name != "skills":
        return None
    plugin_root = skill_dir.parent.parent
    # A marketplace install nests the plugin under its version directory,
    # so the directory name is the version there; the manifest names it.
    manifest = safe_json_load(plugin_root / ".claude-plugin" / "plugin.json", {})
    plugin = manifest.get("name") if isinstance(manifest, dict) else None
    return f"{plugin or plugin_root.name}:{skill_dir.name}"


def current_metrics(skill_ref: str) -> dict[str, float] | None:
    """Read the gap the monitor would compute now, or None without history.

    ``run_count`` is the history position the evaluation window opens at.
    """
    history = safe_json_load(get_log_directory() / ".history.json", {})
    accuracies = (
        history.get(skill_ref, {}).get("accuracies", [])
        if isinstance(history, dict)
        else []
    )
    if not accuracies:
        return None
    return {
        "success_rate": sum(accuracies) / len(accuracies),
        "stability_gap": stability_gap(accuracies),
        "run_count": len(accuracies),
    }


def main(argv: list[str] | None = None) -> int:
    """Bump the version, then start evaluation when a baseline exists."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("skill_file", type=Path, help="path to the SKILL.md")
    parser.add_argument("--summary", required=True, help="what the change did")
    args = parser.parse_args(argv)

    skill_ref = skill_ref_for(args.skill_file)
    if skill_ref is None:
        parser.error(f"{args.skill_file} is not <plugin>/skills/<skill>/SKILL.md")

    metrics = current_metrics(skill_ref)
    baseline = {k: v for k, v in (metrics or {}).items() if k != "run_count"}
    version = SkillVersionManager(args.skill_file).bump_version(args.summary, baseline)
    print(f"{skill_ref}: adaptation version {version}")

    if metrics is None:
        print(f"{skill_ref}: no execution history, so no evaluation window")
        return 0
    queue_file = get_improvement_queue_path()
    queue = ImprovementQueue(queue_file) if queue_file.exists() else None
    if queue is None or skill_ref not in queue.skills:
        print(f"{skill_ref}: not in the improvement queue, so no evaluation window")
        return 0
    queue.start_evaluation(
        skill_ref,
        metrics["stability_gap"],
        history_position=int(metrics["run_count"]),
        version=version,
        change_summary=args.summary,
    )
    print(
        f"{skill_ref}: evaluating against baseline gap {metrics['stability_gap']:.2f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
