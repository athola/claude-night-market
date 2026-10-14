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

import importlib.util
import io
import json
import os
import subprocess
import sys
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
        [sys.executable, str(HOOK_PATH)],
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
        assert "permissionDecision" not in out["hookSpecificOutput"]
        assert "requests" in out["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.unit
    def test_typosquat_blocks_when_blocking_enabled(self):
        """Scenario: with VOW_SHADOW_MODE=0 a typosquat install is blocked."""
        code, out = run_hook("pip install reqeusts", {"VOW_SHADOW_MODE": "0"})
        assert code == 0
        assert out is not None
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

    @pytest.mark.unit
    def test_hook_never_crashes_on_bad_input(self):
        result = run_raw("not json")
        assert result.returncode == 0
        assert result.stdout == ""

    @pytest.mark.unit
    def test_non_object_payload_is_an_internal_error_that_allows_the_call(self):
        """Scenario: valid JSON that is not an object exits 0 and says why."""
        result = run_raw("[1, 2]")
        assert result.returncode == 0
        assert result.stdout == ""
        assert "internal error" in result.stderr

    @pytest.mark.unit
    def test_non_bash_tool_is_ignored_even_with_an_install_command(self):
        result = run_raw(
            json.dumps(
                {
                    "tool_name": "Write",
                    "tool_input": {"command": "pip install reqeusts"},
                }
            ),
            {"VOW_SHADOW_MODE": "0"},
        )
        assert result.returncode == 0
        assert result.stdout == ""


def run_raw(stdin_text: str, env_overrides: dict | None = None):
    env = os.environ.copy()
    env["IMBUE_PKG_REGISTRY_CHECK"] = "0"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
        check=False,
    )


@pytest.fixture
def guard_module():
    """Load the hook in-process so the coverage gate measures main()."""
    spec = importlib.util.spec_from_file_location("guard_pkg_in_process", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMainInProcess:
    """main() decisions with the registry replaced by a stub (no network)."""

    def _main(self, guard_module, monkeypatch, capsys, payload, registry=None):
        monkeypatch.setattr(guard_module, "_registry_exists", lambda n, e: registry)
        text = payload if isinstance(payload, str) else json.dumps(payload)
        monkeypatch.setattr(guard_module.sys, "stdin", io.StringIO(text))
        with pytest.raises(SystemExit) as exc:
            guard_module.main()
        captured = capsys.readouterr()
        out = json.loads(captured.out) if captured.out.strip() else None
        return exc.value.code, out, captured.err

    @staticmethod
    def _bash(command):
        return {"tool_name": "Bash", "tool_input": {"command": command}}

    @pytest.mark.unit
    def test_registry_confirmed_missing_package_is_denied_when_blocking(
        self, guard_module, monkeypatch, capsys
    ):
        monkeypatch.setenv("VOW_SHADOW_MODE", "0")
        code, out, err = self._main(
            guard_module,
            monkeypatch,
            capsys,
            self._bash("pip install zq-made-up-pkg"),
            registry=False,
        )
        assert code == 0
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "BLOCK: nonexistent" in err

    @pytest.mark.unit
    def test_unverified_package_only_warns_even_when_blocking(
        self, guard_module, monkeypatch, capsys
    ):
        monkeypatch.setenv("VOW_SHADOW_MODE", "0")
        _, out, err = self._main(
            guard_module,
            monkeypatch,
            capsys,
            self._bash("pip install zq-made-up-pkg"),
            registry=None,
        )
        assert "permissionDecision" not in out["hookSpecificOutput"]
        assert "WARN: unverified" in err

    @pytest.mark.unit
    def test_typosquat_in_shadow_mode_names_the_blocking_switch(
        self, guard_module, monkeypatch, capsys
    ):
        monkeypatch.setenv("VOW_SHADOW_MODE", "1")
        _, out, _ = self._main(
            guard_module, monkeypatch, capsys, self._bash("pip install reqeusts"), True
        )
        assert "VOW_SHADOW_MODE=0" in out["hookSpecificOutput"]["additionalContext"]

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "payload",
        [
            {"tool_name": "Write", "tool_input": {"command": "pip install reqeusts"}},
            {"tool_name": "Bash", "tool_input": {"command": ""}},
            {"tool_name": "Bash", "tool_input": {"command": "pip install requests"}},
            "not json",
        ],
        ids=["non-bash", "empty-command", "known-package", "malformed"],
    )
    def test_silent_paths(self, guard_module, monkeypatch, capsys, payload):
        code, out, _ = self._main(guard_module, monkeypatch, capsys, payload, True)
        assert code == 0
        assert out is None

    @pytest.mark.unit
    def test_non_object_payload_reports_an_internal_error(
        self, guard_module, monkeypatch, capsys
    ):
        code, out, err = self._main(guard_module, monkeypatch, capsys, "[1, 2]")
        assert (code, out) == (0, None)
        assert "internal error" in err
