"""clawhub-cron finds node through nvm instead of a pinned version.

The PATH named node v25.2.1. After an upgrade the clawhub CLI was not
found, every hourly run logged "Partial sync", and the job never
removed itself.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "clawhub-cron.sh"


def _node_bin(home: Path) -> str:
    body = SCRIPT.read_text().split("nvm_node_bin() {", 1)[1].split("\n}\n", 1)[0]
    return subprocess.run(
        ["/bin/bash", "-c", "nvm_node_bin() {" + body + "\n}\nnvm_node_bin"],
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def _install(home: Path, *versions: str) -> None:
    for version in versions:
        (home / ".nvm" / "versions" / "node" / version / "bin").mkdir(parents=True)


def test_the_default_alias_wins(tmp_path: Path) -> None:
    _install(tmp_path, "v20.1.0", "v25.2.1")
    (tmp_path / ".nvm" / "alias").mkdir()
    (tmp_path / ".nvm" / "alias" / "default").write_text("v20.1.0")

    assert _node_bin(tmp_path).endswith("/v20.1.0/bin:")


def test_without_an_alias_an_installed_version_is_used(tmp_path: Path) -> None:
    _install(tmp_path, "v26.0.0")

    assert _node_bin(tmp_path).endswith("/v26.0.0/bin:")


def test_without_nvm_nothing_is_added(tmp_path: Path) -> None:
    assert _node_bin(tmp_path) == ""
