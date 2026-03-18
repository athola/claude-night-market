"""Tests for egregore UserPromptSubmit hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"


def run_hook(tmp_path, manifest_data=None):
    """Run user_prompt_hook.py as a subprocess with stdin."""
    hook_script = HOOKS_DIR / "user_prompt_hook.py"
    if not hook_script.exists():
        pytest.skip("user_prompt_hook.py not yet created")

    if manifest_data is not None:
        egregore_dir = tmp_path / ".egregore"
        egregore_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = egregore_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest_data))

    stdin_payload = json.dumps({"hook_event": "UserPromptSubmit"})
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=stdin_payload,
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        timeout=5,
        check=False,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": str(HOOKS_DIR),
        },
    )
    return result


def test_injects_context_when_active_items(tmp_path):
    """Hook injects orchestration resume context for active items."""
    manifest = {
        "items": [
            {
                "id": "TASK-001",
                "status": "active",
                "pipeline_stage": "build",
                "pipeline_step": "execute",
            },
        ]
    }
    result = run_hook(tmp_path, manifest)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    ctx = output["hookSpecificOutput"]["additionalContext"]
    assert "TASK-001" in ctx
    assert "resume" in ctx.lower() or "orchestration" in ctx.lower()


def test_injects_context_when_pending_items(tmp_path):
    """Hook injects context for pending items too."""
    manifest = {
        "items": [
            {"id": "DONE-001", "status": "completed"},
            {
                "id": "TODO-001",
                "status": "pending",
                "pipeline_stage": "build",
                "pipeline_step": "execute",
            },
        ]
    }
    result = run_hook(tmp_path, manifest)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    ctx = output["hookSpecificOutput"]["additionalContext"]
    assert "TODO-001" in ctx


def test_silent_when_no_manifest(tmp_path):
    """Hook produces no output when no manifest exists."""
    result = run_hook(tmp_path, manifest_data=None)
    assert result.returncode == 0
    # Should either produce empty output or no hookSpecificOutput
    if result.stdout.strip():
        output = json.loads(result.stdout)
        assert (
            "hookSpecificOutput" not in output
            or output.get("hookSpecificOutput", {}).get("additionalContext", "") == ""
        )


def test_silent_when_all_completed(tmp_path):
    """Hook silent when all items are done."""
    manifest = {
        "items": [
            {"id": "DONE-001", "status": "completed"},
            {"id": "DONE-002", "status": "failed"},
        ]
    }
    result = run_hook(tmp_path, manifest)
    assert result.returncode == 0
    if result.stdout.strip():
        output = json.loads(result.stdout)
        # Should not inject context
        ctx = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "resume" not in ctx.lower()


def test_works_with_work_items_key(tmp_path):
    """Hook works with legacy 'work_items' key."""
    manifest = {
        "work_items": [
            {
                "id": "WRK-001",
                "status": "active",
                "pipeline_stage": "quality",
                "pipeline_step": "code-review",
            },
        ]
    }
    result = run_hook(tmp_path, manifest)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    ctx = output["hookSpecificOutput"]["additionalContext"]
    assert "WRK-001" in ctx


def test_missing_fields_use_fallback(tmp_path):
    """Item without id/pipeline_stage/pipeline_step uses '?' fallback."""
    manifest = {
        "items": [
            {"status": "active"},
        ]
    }
    result = run_hook(tmp_path, manifest)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    ctx = output["hookSpecificOutput"]["additionalContext"]
    # Fallback values should appear in place of missing fields
    assert "?/?" in ctx
    assert "1 work item" in ctx
