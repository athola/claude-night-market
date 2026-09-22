"""``make skrills-build`` must fail when ``cargo build`` fails.

The recipe piped the build into ``tail -1``::

    @cargo build --manifest-path "$(SKRILLS_REPO)/Cargo.toml" --release \\
        -p skrills 2>&1 | tail -1

A pipeline's status is the status of its last command, so the recipe saw
``tail``'s 0 whatever cargo did. ``Makefile:6`` asks for ``-o pipefail``
through ``.SHELLFLAGS``, but GNU make 3.81, which this repository's own
platform runs, ignores ``.SHELLFLAGS`` entirely, and the root ``Makefile``
includes neither shared ``.mk`` file, so it never printed the warning that
says so.

The consequence was not a noisy build. It was a quiet one. A failed
compile left the previous ``target/release/skrills`` in place, the next
line copied that stale binary into ``plugins/abstract/bin/``, the line
after recorded the stale binary's hash, and ``skrills-verify`` then
compared the stale binary against the hash just taken of that same stale
binary and reported OK.

The reproduction below stands a ``cargo`` on PATH that exits 101 beside a
``target/release/skrills`` that already exists, which is exactly the
state after one successful build followed by one broken one.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def failing_cargo_tree(tmp_path: Path) -> dict[str, Path]:
    """A skrills checkout whose cargo always fails and whose binary is stale."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    cargo = fake_bin / "cargo"
    cargo.write_text('#!/bin/sh\necho "error: could not compile" >&2\nexit 101\n')
    cargo.chmod(0o755)

    repo = tmp_path / "skrills"
    release = repo / "target" / "release"
    release.mkdir(parents=True)
    (repo / "Cargo.toml").write_text("[package]\n")
    stale = release / "skrills"
    stale.write_text("#!/bin/sh\necho stale\n")
    stale.chmod(0o755)

    out = tmp_path / "out"
    out.mkdir()
    return {"bin": fake_bin, "repo": repo, "out": out}


def _run_skrills_build(tree: dict[str, Path]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PATH"] = f"{tree['bin']}{os.pathsep}{env['PATH']}"
    return subprocess.run(
        [
            "make",
            "skrills-build",
            f"SKRILLS_REPO={tree['repo']}",
            f"SKRILLS_BIN={tree['out'] / 'skrills'}",
            f"SKRILLS_VERSION_FILE={tree['out'] / '.skrills-version'}",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
        check=False,
    )


def test_skrills_build_exits_non_zero_when_cargo_fails(
    failing_cargo_tree: dict[str, Path],
) -> None:
    """A compile error reaches make rather than being laundered by a pipe."""
    result = _run_skrills_build(failing_cargo_tree)
    assert result.returncode != 0, (
        "make skrills-build reported success while cargo exited 101:\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def test_failed_build_does_not_install_a_stale_binary(
    failing_cargo_tree: dict[str, Path],
) -> None:
    """Nothing is copied into the plugin bin directory after a failed build."""
    _run_skrills_build(failing_cargo_tree)
    installed = failing_cargo_tree["out"] / "skrills"
    assert not installed.exists(), (
        "a failed build installed the previous binary, which is what makes "
        "skrills-verify self-confirming"
    )
