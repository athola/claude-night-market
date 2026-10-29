"""ImprovementQueue shares one file between concurrent hook processes."""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
from typing import Any

import pytest

from abstract.improvement_queue import ImprovementQueue


def test_flag_skill_keeps_a_flag_written_by_another_process(tmp_path: Path) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    first_process = ImprovementQueue(queue_file)
    second_process = ImprovementQueue(queue_file)

    first_process.flag_skill("abstract:alpha", 0.4, "session-1")
    second_process.flag_skill("abstract:beta", 0.6, "session-2")

    on_disk = ImprovementQueue(queue_file)
    assert sorted(on_disk.skills) == ["abstract:alpha", "abstract:beta"]


def _evaluating_queue(queue_file: Path, skill_ref: str) -> ImprovementQueue:
    queue = ImprovementQueue(queue_file)
    for n in range(ImprovementQueue.TRIGGER_THRESHOLD):
        queue.flag_skill(skill_ref, 0.5, f"setup-{n}")
    queue.start_evaluation(skill_ref, 0.5)
    return queue


def test_record_eval_execution_keeps_a_flag_written_after_it_loaded(
    tmp_path: Path,
) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    _evaluating_queue(queue_file, "abstract:beta")
    stale_process = ImprovementQueue(queue_file)
    ImprovementQueue(queue_file).flag_skill("abstract:alpha", 0.4, "session-1")

    stale_process.record_eval_execution("abstract:beta", 0.3)

    on_disk = ImprovementQueue(queue_file)
    assert "abstract:alpha" in on_disk.skills
    assert on_disk.skills["abstract:beta"]["eval_executions"] == 1


def test_start_evaluation_keeps_a_flag_written_after_it_loaded(
    tmp_path: Path,
) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    ImprovementQueue(queue_file).flag_skill("abstract:beta", 0.5, "setup")
    stale_process = ImprovementQueue(queue_file)
    ImprovementQueue(queue_file).flag_skill("abstract:alpha", 0.4, "session-1")

    assert stale_process.start_evaluation("abstract:beta", 0.5)

    on_disk = ImprovementQueue(queue_file)
    assert "abstract:alpha" in on_disk.skills
    assert on_disk.skills["abstract:beta"]["status"] == "evaluating"


def test_evaluate_keeps_a_flag_written_after_it_loaded(tmp_path: Path) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    _evaluating_queue(queue_file, "abstract:beta")
    stale_process = ImprovementQueue(queue_file)
    ImprovementQueue(queue_file).flag_skill("abstract:alpha", 0.4, "session-1")

    stale_process.evaluate("abstract:beta")

    on_disk = ImprovementQueue(queue_file)
    assert "abstract:alpha" in on_disk.skills
    assert on_disk.skills["abstract:beta"]["status"] != "evaluating"


def test_save_does_not_depend_on_a_fixed_shared_temp_path(tmp_path: Path) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    queue = ImprovementQueue(queue_file)
    # Another writer's temp file occupying the fixed sibling name.
    queue_file.with_suffix(".tmp").mkdir()

    queue.flag_skill("abstract:alpha", 0.4, "session-1")

    assert "abstract:alpha" in ImprovementQueue(queue_file).skills


def test_unreadable_queue_raises_and_is_not_moved_aside(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read error is not corruption: the healthy file must stay in place."""
    queue_file = tmp_path / "improvement-queue.json"
    ImprovementQueue(queue_file).flag_skill("abstract:alpha", 0.4, "s1")
    real_read_text = Path.read_text

    def deny(path: Path, *args: object, **kwargs: object) -> str:
        if path == queue_file:
            raise PermissionError("transient read failure")
        return real_read_text(path, *args, **kwargs)

    with monkeypatch.context() as patched:
        patched.setattr(Path, "read_text", deny)
        with pytest.raises(PermissionError):
            ImprovementQueue(queue_file)
    assert "abstract:alpha" in ImprovementQueue(queue_file).skills
    assert not list(tmp_path.glob("*.corrupt*"))


def test_absent_queue_file_loads_empty(tmp_path: Path) -> None:
    """A file another process moved aside reads as an empty queue."""
    queue_file = tmp_path / "improvement-queue.json"
    assert ImprovementQueue(queue_file).skills == {}


def test_corrupt_queue_moved_by_another_process_first_loads_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The corrupt file vanishing before the move-aside is not an error."""
    queue_file = tmp_path / "improvement-queue.json"
    queue_file.write_text("{not json", encoding="utf-8")
    real_read_text = Path.read_text

    def read_then_vanish(path: Path, *args: object, **kwargs: object) -> str:
        text = real_read_text(path, *args, **kwargs)
        if path == queue_file:
            path.unlink()
        return text

    monkeypatch.setattr(Path, "read_text", read_then_vanish)
    assert ImprovementQueue(queue_file).skills == {}


def test_second_corruption_keeps_the_first_backup(tmp_path: Path) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    queue_file.write_text("{first", encoding="utf-8")
    ImprovementQueue(queue_file)
    queue_file.write_text("{second", encoding="utf-8")
    ImprovementQueue(queue_file)
    backups = sorted(p.read_text(encoding="utf-8") for p in tmp_path.glob("*.corrupt*"))
    assert backups == ["{first", "{second"]


def test_constructor_does_not_replace_a_queue_written_after_its_first_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another process filling the file after our read missed it must win."""
    queue_file = tmp_path / "improvement-queue.json"
    ImprovementQueue(queue_file).flag_skill("sk:one", 0.9, "e1")
    real_read_text = Path.read_text
    missed = []

    def miss_first_read(path: Path, *args: object, **kwargs: object) -> str:
        if path == queue_file and not missed:
            missed.append(path)
            raise FileNotFoundError(path)
        return real_read_text(path, *args, **kwargs)

    with monkeypatch.context() as patched:
        patched.setattr(Path, "read_text", miss_first_read)
        late_process = ImprovementQueue(queue_file)

    assert "sk:one" in late_process.skills
    assert "sk:one" in ImprovementQueue(queue_file).skills


def test_flag_skill_skips_a_skill_another_process_put_under_evaluation(
    tmp_path: Path,
) -> None:
    queue_file = tmp_path / "improvement-queue.json"
    ImprovementQueue(queue_file).flag_skill("abstract:beta", 0.5, "setup")
    stale_process = ImprovementQueue(queue_file)
    ImprovementQueue(queue_file).start_evaluation("abstract:beta", 0.5)

    flagged = stale_process.flag_skill("abstract:beta", 0.7, "late-session")

    entry = ImprovementQueue(queue_file).skills["abstract:beta"]
    assert flagged is False
    assert entry["flagged_count"] == 0
    assert entry["execution_ids"] == []


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory write permission")
def test_save_into_read_only_directory_raises_rather_than_reporting_a_flag(
    tmp_path: Path,
) -> None:
    """A flag that was not persisted must not read as one that was.

    The save used to warn and return, and flag_skill then returned True,
    so the hook reported a flag the next run would not see. The hook
    catches OSError and still prints its health report.
    """
    queue_dir = tmp_path / "skills"
    queue_file = queue_dir / "improvement-queue.json"
    queue = ImprovementQueue(queue_file)
    queue_file.with_name(queue_file.name + ".lock").touch()
    queue_dir.chmod(0o500)
    try:
        with pytest.raises(OSError):
            queue.flag_skill("abstract:alpha", 0.4, "session-1")
    finally:
        queue_dir.chmod(0o700)


def test_a_second_evaluation_window_starts_with_no_gaps(tmp_path: Path) -> None:
    queue = ImprovementQueue(tmp_path / "q.json")
    queue.flag_skill("abstract:alpha", 0.5, "s1")
    queue.start_evaluation("abstract:alpha", baseline_gap=0.5)
    for _ in range(10):
        queue.record_eval_execution("abstract:alpha", 0.9)
    queue.evaluate("abstract:alpha")

    queue.start_evaluation("abstract:alpha", baseline_gap=0.5)

    assert queue.skills["abstract:alpha"]["eval_gaps"] == []


def test_execution_ids_stay_bounded(tmp_path: Path) -> None:
    queue = ImprovementQueue(tmp_path / "q.json")
    for run in range(500):
        queue.flag_skill("abstract:alpha", 0.5, f"s{run}")
    ids = queue.skills["abstract:alpha"]["execution_ids"]
    assert len(ids) == ImprovementQueue.MAX_EXECUTION_IDS
    assert ids[-1] == "s499"


def test_saved_queue_is_private_to_its_owner(tmp_path: Path) -> None:
    """The queue lives under ~/.claude and has one reader: its owner."""
    queue_file = tmp_path / "improvement-queue.json"
    ImprovementQueue(queue_file).flag_skill("abstract:alpha", 0.4, "session-1")
    assert queue_file.stat().st_mode & 0o777 == 0o600


_RACE_PROCESSES = 8
_RACE_FLAGS_PER_PROCESS = 40


def _flag_distinct_skills(queue_file: str, worker: int, start: Any) -> None:
    """Flag skills no other worker names, through a fresh queue each time.

    Module level so a spawned process can import it by name. The barrier
    holds every worker until all have started: spawn start-up takes longer
    than one worker's whole run, so without it the workers run in turn.
    """
    start.wait()
    for n in range(_RACE_FLAGS_PER_PROCESS):
        ImprovementQueue(Path(queue_file)).flag_skill(
            f"race:w{worker}-s{n}", 0.5, f"exec-{worker}-{n}"
        )


def test_concurrent_processes_flagging_keep_every_flag(tmp_path: Path) -> None:
    """Real processes race on one queue file and none of their flags is lost.

    Without the flock in _locked_reload, two processes read the same file,
    each adds its own skill and the later os.replace drops the earlier one.
    Measured with the lock off: about 30% of flags lost at this size.
    """
    queue_file = tmp_path / "improvement-queue.json"
    ctx = multiprocessing.get_context("spawn")
    start = ctx.Barrier(_RACE_PROCESSES, timeout=60)
    workers = [
        ctx.Process(target=_flag_distinct_skills, args=(str(queue_file), w, start))
        for w in range(_RACE_PROCESSES)
    ]
    for proc in workers:
        proc.start()
    for proc in workers:
        proc.join(timeout=120)
    assert [proc.exitcode for proc in workers] == [0] * _RACE_PROCESSES

    expected = {
        f"race:w{w}-s{n}"
        for w in range(_RACE_PROCESSES)
        for n in range(_RACE_FLAGS_PER_PROCESS)
    }
    assert set(ImprovementQueue(queue_file).skills) == expected
