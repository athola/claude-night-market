"""Tests for the single UserPromptSubmit entry point (#779).

Feature: One process per prompt
  As someone whose every prompt waits on UserPromptSubmit hooks
  I want memory-palace to spawn one process, not two
  So that URL detection and recall cost one interpreter start-up.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent.parent
HOOK = PLUGIN / "hooks" / "user_prompt.py"
sys.path.insert(0, str(PLUGIN / "hooks"))

import user_prompt  # noqa: E402 - import after sys.path setup


def _run(prompt: str, home: Path) -> subprocess.CompletedProcess:
    """Invoke the hook the way Claude Code does, with HOME isolated."""
    env = {**os.environ, "HOME": str(home), "XDG_DATA_HOME": str(home / "data")}
    env.pop("MEMORY_PALACE_RECALL", None)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"prompt": prompt, "hook_event_name": "UserPromptSubmit"}),
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
        check=False,
    )


def test_prompt_with_neither_url_nor_token_emits_nothing(tmp_path: Path) -> None:
    """Scenario: the common prompt produces no output."""
    result = _run("rename the helper in utils", tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""


def test_url_and_recall_token_merge_into_one_context(tmp_path: Path) -> None:
    """Scenario: both features fire and share one hookSpecificOutput."""
    result = _run("read https://example.org/post and +recall", tmp_path)
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout)
    output = response["hookSpecificOutput"]
    assert output["hookEventName"] == "UserPromptSubmit"
    assert "https://example.org/post" in output["additionalContext"]
    assert "Memory Palace recall" in output["additionalContext"]


def test_recall_alone_still_reaches_the_model(tmp_path: Path) -> None:
    """Scenario: a prompt with only the token gets recall context."""
    result = _run("what did we decide +recall", tmp_path)
    response = json.loads(result.stdout)
    context = response["hookSpecificOutput"]["additionalContext"]
    assert "Memory Palace recall" in context
    assert "Detected" not in context


def test_hooks_json_registers_one_user_prompt_process() -> None:
    """Scenario: the registration spawns the merged hook and nothing else."""
    config = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
    commands = [
        hook["command"]
        for group in config["hooks"]["UserPromptSubmit"]
        for hook in group["hooks"]
    ]
    assert commands == ['"${CLAUDE_PLUGIN_ROOT}/hooks/user_prompt.py"']


def test_user_prompt_hook_runs_synchronously() -> None:
    """Scenario: the context reaches the prompt that asked for it.

    An async hook's output is delivered on the next turn, so `+recall`
    would answer one prompt late. The merged hook injects context and
    must block.
    """
    config = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())
    hooks = [
        hook for group in config["hooks"]["UserPromptSubmit"] for hook in group["hooks"]
    ]
    assert hooks
    assert not any(hook.get("async") for hook in hooks)


def _boom(payload: object) -> str:
    raise RuntimeError("feature failed")


@pytest.mark.parametrize(
    ("broken", "working"), [("_url_detector", "_recall"), ("_recall", "_url_detector")]
)
def test_one_feature_raising_does_not_suppress_the_other(
    broken: str,
    working: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the two features ran as separate processes before #779.

    Given one feature raising and the other returning context
    When the merged hook runs
    Then the working feature's context still reaches the prompt
    And the failure is reported on stderr.
    """
    monkeypatch.setattr(getattr(user_prompt, broken), "prompt_context", _boom)
    monkeypatch.setattr(
        getattr(user_prompt, working), "prompt_context", lambda payload: "kept-ctx"
    )
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"prompt": "https://x.org +recall"}))
    )

    with pytest.raises(SystemExit) as exit_info:
        user_prompt.main()

    captured = capsys.readouterr()
    assert exit_info.value.code == 0
    context = json.loads(captured.out)["hookSpecificOutput"]["additionalContext"]
    assert context == "kept-ctx"
    assert "feature failed" in captured.err
