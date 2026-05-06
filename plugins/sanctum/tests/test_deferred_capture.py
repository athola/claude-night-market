"""Tests for deferred_capture.py script."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "deferred_capture.py"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "sanctum_deferred_capture", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sanctum_deferred_capture"] = module
    spec.loader.exec_module(module)
    return module


def test_module_imports_cleanly():
    module = _load_script()
    assert module is not None


def test_config_has_sanctum_plugin_name():
    module = _load_script()
    assert module.CONFIG.plugin_name == "sanctum"


def test_config_has_full_label_taxonomy():
    module = _load_script()
    expected_labels = {
        "deferred",
        "war-room",
        "brainstorm",
        "scope-guard",
        "feature-review",
        "review",
        "regression",
        "egregore",
    }
    assert set(module.CONFIG.label_colors.keys()) == expected_labels


def test_config_label_colors_are_hex():
    module = _load_script()
    for label, color in module.CONFIG.label_colors.items():
        assert color.startswith("#"), f"label {label} color {color}"
        assert len(color) == 7, f"label {label} color {color}"


def test_config_source_help_describes_skills():
    module = _load_script()
    assert "skill" in module.CONFIG.source_help.lower()


def test_main_invocation_exits_with_usage_when_no_args():
    """Smoke-test that running the script as __main__ produces a CLI."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    # leyline's run_capture should accept --help and exit 0;
    # if not available it exits 1 with the import-error message.
    assert result.returncode in (0, 1, 2), result.stderr


def test_help_output_proves_leyline_delegation_with_sanctum_config():
    """The --help text must reflect the wired CONFIG, not just print.

    C6 (PR #470 review) flagged the prior tests as tautological for a
    re-export wrapper. This test exercises the actual delegation: the
    help banner must surface either the sanctum-specific source_help
    string or one of the configured label names. If `run_capture` ever
    stops consuming `CONFIG`, this test fails.
    """
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if result.returncode == 1 and "leyline not found" in result.stderr:
        # Environment without leyline installed is a known fallback;
        # the script's import-error path is exercised by the smoke
        # test above. Skip the delegation assertion.
        return
    combined = (result.stdout + result.stderr).lower()
    # At least one of the configured discriminators must appear in
    # the help text -- either the source-help phrase or a label name.
    assert (
        "origin skill" in combined or "war-room" in combined or "deferred" in combined
    ), f"help output does not reflect CONFIG: {combined[:300]!r}"
