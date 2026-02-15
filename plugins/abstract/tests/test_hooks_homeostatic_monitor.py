"""Tests for homeostatic_monitor.py PostToolUse hook.

Verifies the monitor reads stability gap from .history.json,
flags degrading skills in improvement-queue.json, and emits
trigger events when threshold is reached.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def run_hook(hook_path: Path, env: dict[str, str]) -> dict[str, object]:
    """Run a hook script with the given environment."""
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        timeout=5,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


class TestHomeostaticMonitorBasics:
    """Test basic hook execution."""

    def test_should_exit_successfully(self, tmp_path: Path) -> None:
        """Given valid Skill env, when hook runs, then exit 0."""
        hook_path = Path(__file__).parent.parent / "hooks" / "homeostatic_monitor.py"
        history = {
            "abstract:test-skill": {
                "accuracies": [1, 1, 1, 1, 1],
                "durations": [100, 200, 150, 120, 180],
            }
        }
        history_file = tmp_path / "skills" / "logs" / ".history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps(history))

        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": "abstract:test-skill"}),
            "CLAUDE_TOOL_OUTPUT": "Success",
            "CLAUDE_SESSION_ID": "test-session",
            "CLAUDE_HOME": str(tmp_path),
        }
        result = run_hook(hook_path, env)
        assert result["returncode"] == 0

    def test_should_skip_non_skill_tools(self, tmp_path: Path) -> None:
        """Given non-Skill tool, when hook runs, then skip."""
        hook_path = Path(__file__).parent.parent / "hooks" / "homeostatic_monitor.py"
        env = {
            "CLAUDE_TOOL_NAME": "Read",
            "CLAUDE_TOOL_INPUT": "{}",
            "CLAUDE_TOOL_OUTPUT": "content",
            "CLAUDE_HOME": str(tmp_path),
        }
        result = run_hook(hook_path, env)
        assert result["returncode"] == 0

    def test_should_flag_degrading_skill(self, tmp_path: Path) -> None:
        """Given stability gap > 0.3, when hook runs, then skill flagged in queue."""
        hook_path = Path(__file__).parent.parent / "hooks" / "homeostatic_monitor.py"
        # Create history with high instability
        history = {
            "abstract:bad-skill": {
                "accuracies": [1, 0, 1, 0, 1, 0],
                "durations": [100, 200, 150, 120, 180, 90],
            }
        }
        history_file = tmp_path / "skills" / "logs" / ".history.json"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps(history))

        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": json.dumps({"skill": "abstract:bad-skill"}),
            "CLAUDE_TOOL_OUTPUT": "Error: something failed",
            "CLAUDE_SESSION_ID": "test-session",
            "CLAUDE_HOME": str(tmp_path),
        }
        result = run_hook(hook_path, env)
        assert result["returncode"] == 0

        queue_file = tmp_path / "skills" / "improvement-queue.json"
        assert queue_file.exists()
        queue_data = json.loads(queue_file.read_text())
        assert "abstract:bad-skill" in queue_data["skills"]
        assert queue_data["skills"]["abstract:bad-skill"]["flagged_count"] >= 1
