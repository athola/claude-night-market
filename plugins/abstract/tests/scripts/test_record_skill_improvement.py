"""record_skill_improvement.py: the step between an improvement and its evaluation.

The skill-improver agent runs it after editing a SKILL.md. It must bump
the adaptation version and open the evaluation window with the skill's
current stability gap as the baseline the window is judged against.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from abstract.improvement_queue import ImprovementQueue
from abstract.skill_versioning import SkillVersionManager

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from record_skill_improvement import skill_ref_for  # noqa: E402 - needs the path above

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "record_skill_improvement.py"
SKILL = "demo:widget"
# Worst five-run window rate 0.4: gap 0.6.
CRITICAL = [1, 0, 0, 0, 1]


def _skill_file(root: Path) -> Path:
    skill_file = root / "plugins" / "demo" / "skills" / "widget" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("---\nname: widget\ndescription: 'Demo.'\n---\n\n# W\n")
    return skill_file


def _seed_history(home: Path) -> None:
    logs = home / "skills" / "logs"
    logs.mkdir(parents=True)
    (logs / ".history.json").write_text(
        json.dumps({SKILL: {"accuracies": CRITICAL, "durations": []}})
    )


def _queue(home: Path) -> ImprovementQueue:
    return ImprovementQueue(home / "skills" / "improvement-queue.json")


def _run(home: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, CLAUDE_HOME=str(home))
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


@pytest.mark.unit
def test_queued_skill_is_versioned_and_starts_evaluation(tmp_path: Path) -> None:
    home = tmp_path / "home"
    skill_file = _skill_file(tmp_path)
    _seed_history(home)
    _queue(home).flag_skill(SKILL, 0.6, "exec-1")

    result = _run(home, str(skill_file), "--summary", "added examples")

    assert result.returncode == 0, result.stderr
    assert SkillVersionManager(skill_file).current_version == "1.1.0"
    entry = _queue(home).skills[SKILL]
    assert entry["status"] == "evaluating"
    assert entry["baseline_gap"] == pytest.approx(0.6)
    assert "1.1.0" in result.stdout


@pytest.mark.unit
def test_unqueued_skill_is_versioned_without_a_window(tmp_path: Path) -> None:
    home = tmp_path / "home"
    skill_file = _skill_file(tmp_path)
    _seed_history(home)

    result = _run(home, str(skill_file), "--summary", "added examples")

    assert result.returncode == 0, result.stderr
    assert SkillVersionManager(skill_file).current_version == "1.1.0"
    assert not (home / "skills" / "improvement-queue.json").exists()
    assert "no evaluation window" in result.stdout


@pytest.mark.unit
def test_skill_without_history_is_versioned_without_a_window(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    skill_file = _skill_file(tmp_path)
    _queue(home).flag_skill(SKILL, 0.6, "exec-1")

    result = _run(home, str(skill_file), "--summary", "added examples")

    assert result.returncode == 0, result.stderr
    assert SkillVersionManager(skill_file).current_version == "1.1.0"
    assert _queue(home).skills[SKILL]["status"] == "monitoring"
    assert "no evaluation window" in result.stdout


@pytest.mark.unit
def test_path_outside_a_skills_tree_is_rejected(tmp_path: Path) -> None:
    stray = tmp_path / "SKILL.md"
    stray.write_text("---\nname: stray\n---\n")

    result = _run(tmp_path / "home", str(stray), "--summary", "x")

    assert result.returncode == 2
    assert stray.read_text() == "---\nname: stray\n---\n"


@pytest.mark.unit
def test_window_opens_at_the_history_position_and_carries_the_change(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    skill_file = _skill_file(tmp_path)
    _seed_history(home)
    _queue(home).flag_skill(SKILL, 0.6, "exec-1")

    result = _run(home, str(skill_file), "--summary", "added examples")

    assert result.returncode == 0, result.stderr
    entry = _queue(home).skills[SKILL]
    assert entry["eval_history_start"] == len(CRITICAL)
    assert entry["eval_version"] == "1.1.0"
    assert entry["eval_change_summary"] == "added examples"


@pytest.mark.unit
def test_corrupt_history_is_treated_as_no_history(tmp_path: Path) -> None:
    home = tmp_path / "home"
    skill_file = _skill_file(tmp_path)
    logs = home / "skills" / "logs"
    logs.mkdir(parents=True)
    (logs / ".history.json").write_text("{not json")

    result = _run(home, str(skill_file), "--summary", "added examples")

    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr
    assert "no execution history" in result.stdout


@pytest.mark.unit
def test_versioned_plugin_cache_path_names_the_plugin_not_the_version(
    tmp_path: Path,
) -> None:
    plugin_root = tmp_path / "cache" / "mkt" / "demo" / "1.9.21"
    (plugin_root / ".claude-plugin").mkdir(parents=True)
    (plugin_root / ".claude-plugin" / "plugin.json").write_text('{"name": "demo"}')
    skill_file = plugin_root / "skills" / "widget" / "SKILL.md"
    skill_file.parent.mkdir(parents=True)
    skill_file.write_text("---\nname: widget\n---\n")

    assert skill_ref_for(skill_file) == "demo:widget"
