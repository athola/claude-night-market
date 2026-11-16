"""Every plugin's openpackage.yml ships what its plugin.json registers.

`opkg install` reads openpackage.yml (book/src/getting-started/installation.md),
the Claude Code marketplace reads plugin.json. leyline's own test compared
the two for leyline alone, and by 2026-11-13 twelve other plugins had drifted:
about forty skills, commands and agents that an opkg install never received.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = sorted(
    p
    for p in (REPO_ROOT / "plugins").iterdir()
    if (p / ".claude-plugin" / "plugin.json").exists()
    and (p / "openpackage.yml").exists()
)


def _paths(entries: list[str] | None) -> set[str]:
    return {e.removeprefix("./").rstrip("/") for e in entries or []}


def test_plugins_were_found() -> None:
    assert len(PLUGINS) >= 20, (
        "glob found too few plugins, so the check below checks nothing"
    )


@pytest.mark.parametrize("plugin", PLUGINS, ids=lambda p: p.name)
@pytest.mark.parametrize("kind", ["skills", "commands", "agents"])
def test_openpackage_lists_what_plugin_json_registers(plugin: Path, kind: str) -> None:
    manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
    package = yaml.safe_load((plugin / "openpackage.yml").read_text())
    registered = _paths(manifest.get(kind))
    packaged = _paths(package.get(kind))
    assert packaged == registered, (
        f"{plugin.name} {kind}: missing from openpackage.yml {sorted(registered - packaged)}, "
        f"extra {sorted(packaged - registered)}"
    )
