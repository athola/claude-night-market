"""uv.lock matching must stay inside one [[package]] block."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_HOOK_PATH = Path(__file__).parents[3] / "hooks" / "supply_chain_check.py"
_spec = importlib.util.spec_from_file_location("supply_chain_check_blocks", _HOOK_PATH)
assert _spec is not None
assert _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["supply_chain_check_blocks"] = _mod
_spec.loader.exec_module(_mod)

BLOCKLIST = {
    "litellm": [
        {
            "versions": ["1.82.7"],
            "severity": "critical",
            "description": "compromised release",
        }
    ]
}


def test_safe_litellm_is_not_flagged_by_another_packages_matching_version(
    tmp_path: Path,
) -> None:
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text(
        "[[package]]\n"
        'name = "app"\n'
        'version = "0.1.0"\n'
        'dependencies = [{ name = "litellm" }]\n'
        "\n"
        "[[package]]\n"
        'name = "litellm"\n'
        'version = "1.81.0"\n'
        "\n"
        "[[package]]\n"
        'name = "unrelated"\n'
        'version = "1.82.7"\n'
    )

    assert _mod._scan_uv_lock(lockfile, BLOCKLIST) == []


def test_compromised_litellm_is_still_flagged(tmp_path: Path) -> None:
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text(
        '[[package]]\nname = "litellm"\nversion = "1.82.7"\n'
        'source = { registry = "https://pypi.org/simple" }\n'
    )

    findings = _mod._scan_uv_lock(lockfile, BLOCKLIST)

    assert [f["version"] for f in findings] == ["1.82.7"]
