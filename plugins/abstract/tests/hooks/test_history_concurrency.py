"""Concurrent access to .history.json by parallel PostToolUse:Skill hooks.

skill_execution_logger and homeostatic_monitor match the same event, and
Claude Code runs matching hooks in parallel. Parallel subagents add more
writers. These tests run real processes because the defect lives in the
filesystem, not in Python state.
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"

SEEDED_SKILLS = 49

WRITER = """
import sys
from pathlib import Path
from skill_execution_logger import ContinualEvaluator
path, skill, count = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
for _ in range(count):
    ContinualEvaluator(path).evaluate_iteration(skill, True, 10)
"""


def _seed(history_file: Path) -> None:
    seeded = {
        f"seed:{i}": {"accuracies": [1] * 8, "durations": [5] * 8}
        for i in range(SEEDED_SKILLS)
    }
    history_file.write_text(json.dumps(seeded))


def _start_writers(
    history_file: Path, writers: int, iterations: int
) -> list[subprocess.Popen[bytes]]:
    return [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                WRITER,
                str(history_file),
                f"writer:{n}",
                str(iterations),
            ],
            cwd=HOOKS_DIR,
            stderr=subprocess.DEVNULL,
        )
        for n in range(writers)
    ]


def _wait(processes: list[subprocess.Popen[bytes]]) -> None:
    for process in processes:
        assert process.wait(timeout=120) == 0


def test_reader_never_sees_partial_history_while_writers_save(
    tmp_path: Path,
) -> None:
    history_file = tmp_path / ".history.json"
    _seed(history_file)
    processes = _start_writers(history_file, writers=2, iterations=100)

    torn_reads = 0
    reads = 0
    while any(process.poll() is None for process in processes):
        reads += 1
        try:
            json.loads(history_file.read_text())
        except ValueError:
            torn_reads += 1
    _wait(processes)

    assert reads > 0
    assert torn_reads == 0


def test_concurrent_writers_keep_seeded_skills_and_every_update(
    tmp_path: Path,
) -> None:
    history_file = tmp_path / ".history.json"
    _seed(history_file)

    _wait(_start_writers(history_file, writers=4, iterations=25))

    history = json.loads(history_file.read_text())
    seeded_left = [key for key in history if key.startswith("seed:")]
    assert len(seeded_left) == SEEDED_SKILLS
    for n in range(4):
        assert len(history[f"writer:{n}"]["accuracies"]) == 25


def test_failed_replace_removes_temp_file_and_keeps_old_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(HOOKS_DIR))
    hook = importlib.import_module("skill_execution_logger")

    history_file = tmp_path / ".history.json"
    _seed(history_file)
    before = history_file.read_text()

    def refuse(src: str, dst: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(hook.os, "replace", refuse)
    evaluator = hook.ContinualEvaluator(history_file)
    with pytest.raises(OSError, match="No space left"):
        evaluator.evaluate_iteration("seed:0", True, 10)

    assert history_file.read_text() == before
    assert list(tmp_path.glob("*.tmp")) == []
