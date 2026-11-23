"""The gate decides inside its 2s hook cap even when every git call is slow.

hooks.json kills the gate at 2s, and a killed PreToolUse hook emits no
deny, so the commit runs ungated. Each git call had its own 1s timeout,
but the gate makes four or more in sequence: with git answering in 0.9s
a reviewer measured 4.11s.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from gauntlet.graph import GraphStore

_HOOK = Path(__file__).resolve().parents[2] / "hooks" / "precommit_gate.py"

#: hooks.json "timeout" for the gate.
_HOOK_CAP_SECONDS = 2.0

_SLOW_GIT = """#!/bin/sh
sleep 0.9
case "$1" in
  ls-files) printf '100644 4b825dc642cb6eb9a060e54bf8d69288fbee4904 0\tbilling\n' ;;
  diff) echo billing ;;
  config) echo dev@example.com ;;
  rev-parse) pwd ;;
esac
"""


@pytest.fixture()
def slow_git_project(
    sample_knowledge_base: Path, tmp_path: Path
) -> tuple[Path, dict[str, str]]:
    gauntlet_dir = sample_knowledge_base.parent
    (gauntlet_dir / "config.json").write_text(
        json.dumps({"precommit": {"mode": "gate"}})
    )
    GraphStore(str(gauntlet_dir / "graph.db")).close()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    git = bin_dir / "git"
    git.write_text(_SLOW_GIT)
    git.chmod(0o755)
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    env.pop("GAUNTLET_PRECOMMIT_MODE", None)
    return gauntlet_dir.parent, env


def _run_gate(cwd: Path, env: dict[str, str]) -> tuple[float, dict[str, object]]:
    payload = json.dumps({"tool_input": {"command": "git commit -m x"}})
    start = time.monotonic()
    completed = subprocess.run(
        [sys.executable, str(_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        check=False,
        timeout=30,
    )
    elapsed = time.monotonic() - start
    assert completed.returncode == 0, completed.stderr
    return elapsed, json.loads(completed.stdout or "{}")


@pytest.mark.unit
def test_gate_denies_within_its_hook_cap_when_git_is_slow(
    slow_git_project: tuple[Path, dict[str, str]],
) -> None:
    cwd, env = slow_git_project
    elapsed, output = _run_gate(cwd, env)
    assert elapsed < _HOOK_CAP_SECONDS, f"gate took {elapsed:.2f}s"
    decision = output["hookSpecificOutput"]["permissionDecision"]
    assert decision == "deny"


@pytest.mark.unit
def test_nudge_mode_never_denies_when_git_is_slow(
    slow_git_project: tuple[Path, dict[str, str]],
) -> None:
    cwd, env = slow_git_project
    (cwd / ".gauntlet" / "config.json").write_text(
        json.dumps({"precommit": {"mode": "nudge"}})
    )
    elapsed, output = _run_gate(cwd, env)
    assert elapsed < _HOOK_CAP_SECONDS, f"gate took {elapsed:.2f}s"
    assert "permissionDecision" not in output.get("hookSpecificOutput", {})


@pytest.mark.unit
class TestAdvisoryBlastRadiusYieldsFirst:
    """The blast radius is skipped before the gate decision runs short."""

    @staticmethod
    def _graph_dir(tmp_path: Path) -> Path:
        gauntlet_dir = tmp_path / ".gauntlet"
        gauntlet_dir.mkdir()
        GraphStore(str(gauntlet_dir / "graph.db")).close()
        return gauntlet_dir

    def test_blast_radius_is_skipped_inside_the_decision_reserve(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import precommit_gate  # noqa: PLC0415 - hooks dir is on pytest's pythonpath

        called: list[object] = []
        monkeypatch.setattr(
            "gauntlet.blast_radius.analyze_changes",
            lambda *args, **kwargs: called.append(kwargs) or {},
        )
        deadline = time.monotonic() + precommit_gate._DECISION_RESERVE_SECONDS / 2
        assert (
            precommit_gate._graph_risk_context(self._graph_dir(tmp_path), deadline)
            is None
        )
        assert called == []

    def test_blast_radius_is_skipped_while_a_build_writes_the_graph(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Sqlite waits up to 5s for a writer, past the hook's 2s cap."""
        import precommit_gate  # noqa: PLC0415 - hooks dir is on pytest's pythonpath

        from gauntlet.build_lock import writer_lock  # noqa: PLC0415 - next to its use

        called: list[object] = []
        monkeypatch.setattr(
            "gauntlet.blast_radius.analyze_changes",
            lambda *args, **kwargs: called.append(kwargs) or {},
        )
        gauntlet_dir = self._graph_dir(tmp_path)
        with writer_lock(gauntlet_dir):
            assert precommit_gate._graph_risk_context(gauntlet_dir) is None
        assert called == []


@pytest.mark.unit
def test_slow_graph_analysis_is_abandoned_at_its_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only the analysis's git calls were bounded. Its graph walk took 2s on
    this repository's own graph, past the hook's whole cap.
    """
    import precommit_gate  # noqa: PLC0415 - hooks dir is on pytest's pythonpath

    def slow_analysis(*args: object, **kwargs: object) -> dict[str, object]:
        time.sleep(3)
        return {"overall_risk": "high"}

    monkeypatch.setattr("gauntlet.blast_radius.analyze_changes", slow_analysis)
    gauntlet_dir = tmp_path / ".gauntlet"
    gauntlet_dir.mkdir()
    GraphStore(str(gauntlet_dir / "graph.db")).close()
    deadline = time.monotonic() + precommit_gate._RUN_BUDGET_SECONDS
    start = time.monotonic()
    assert precommit_gate._graph_risk_context(gauntlet_dir, deadline) is None
    elapsed = time.monotonic() - start
    assert (
        elapsed
        < precommit_gate._RUN_BUDGET_SECONDS
        - precommit_gate._DECISION_RESERVE_SECONDS
        + 0.2
    )
