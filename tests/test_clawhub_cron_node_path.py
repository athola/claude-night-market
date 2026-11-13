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


def _alias(home: Path, name: str, target: str) -> None:
    path = home / ".nvm" / "alias" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(target + "\n")


def test_a_major_version_alias_picks_the_newest_of_that_major(tmp_path: Path) -> None:
    _install(tmp_path, "v9.11.2", "v25.2.1", "v25.10.0", "v26.0.0")
    _alias(tmp_path, "default", "25")

    assert _node_bin(tmp_path).endswith("/v25.10.0/bin:")


def test_the_node_alias_picks_the_newest_version_not_the_last_listed(
    tmp_path: Path,
) -> None:
    """v9.x sorts after v25.x by name, which brought the stale node back."""
    _install(tmp_path, "v9.11.2", "v25.2.1")
    _alias(tmp_path, "default", "node")

    assert _node_bin(tmp_path).endswith("/v25.2.1/bin:")


def test_an_lts_alias_is_followed_to_its_version(tmp_path: Path) -> None:
    _install(tmp_path, "v22.11.0", "v25.2.1")
    _alias(tmp_path, "default", "lts/*")
    _alias(tmp_path, "lts/*", "lts/jod")
    _alias(tmp_path, "lts/jod", "v22.11.0")

    assert _node_bin(tmp_path).endswith("/v22.11.0/bin:")


def test_without_an_alias_the_newest_version_is_used(tmp_path: Path) -> None:
    _install(tmp_path, "v9.11.2", "v25.2.1")

    assert _node_bin(tmp_path).endswith("/v25.2.1/bin:")


def test_an_alias_to_an_uninstalled_version_falls_back_to_the_newest(
    tmp_path: Path,
) -> None:
    _install(tmp_path, "v9.11.2", "v25.2.1")
    _alias(tmp_path, "default", "v20.1.0")

    assert _node_bin(tmp_path).endswith("/v25.2.1/bin:")
