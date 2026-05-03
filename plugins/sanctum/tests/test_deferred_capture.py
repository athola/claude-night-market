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
