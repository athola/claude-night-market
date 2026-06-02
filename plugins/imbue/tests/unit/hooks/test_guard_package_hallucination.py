# ruff: noqa: D101,D102,D103,D205,D212,E501
"""Tests for the package-hallucination guard hook (end-to-end subprocess).

Feature: Block hallucinated and typosquatted dependency installs

As the imbue verification spine
I want the guard hook to flag install commands for fake/typo packages
So that hallucinated dependencies never reach the environment.

Registry network checks are disabled (IMBUE_PKG_REGISTRY_CHECK=0) so
these tests are hermetic and rely on the offline typosquat signal.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).resolve().parents[3] / "hooks" / "guard_package_hallucination.py"
)


def run_hook(
    command: str, env_overrides: dict | None = None
) -> tuple[int, dict | None]:
    env = os.environ.copy()
    env["IMBUE_PKG_REGISTRY_CHECK"] = "0"  # hermetic: no network
    if env_overrides:
        env.update(env_overrides)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    result = subprocess.run(
        [str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )
    parsed = json.loads(result.stdout) if result.stdout.strip() else None
    return result.returncode, parsed


class TestGuardHook:
    @pytest.mark.unit
    def test_clean_install_is_silent(self):
        """Scenario: a known-popular package produces no hook output."""
        code, out = run_hook("pip install requests")
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_non_install_command_is_silent(self):
        code, out = run_hook("git status")
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_typosquat_warns_in_shadow_mode(self):
        """Scenario: a typo of a popular package warns (shadow default)."""
        code, out = run_hook("pip install reqeusts", {"VOW_SHADOW_MODE": "1"})
        assert code == 0
        assert out is not None
        decision = out["hookSpecificOutput"]["permissionDecision"]
        assert decision == "warn"
        assert "requests" in out["hookSpecificOutput"]["permissionDecisionReason"]

    @pytest.mark.unit
    def test_typosquat_blocks_when_blocking_enabled(self):
        """Scenario: with VOW_SHADOW_MODE=0 a typosquat install is blocked."""
        code, out = run_hook("pip install reqeusts", {"VOW_SHADOW_MODE": "0"})
        assert code == 0
        assert out is not None
        assert out["hookSpecificOutput"]["permissionDecision"] == "block"

    @pytest.mark.unit
    def test_hook_never_crashes_on_bad_input(self):
        env = os.environ.copy()
        result = subprocess.run(
            [str(HOOK_PATH)],
            input="not json",
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            check=False,
        )
        assert result.returncode == 0
