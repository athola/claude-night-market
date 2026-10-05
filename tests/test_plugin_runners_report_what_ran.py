"""The run-plugin-* gates must fail on a typo and stay quiet on no work.

Shell review S0-1, S0-2, S2-1, S2-2 and S2-3. A gate that ran nothing
reported success for an unknown plugin name, and `--changed` died with
exit 1 and no message when nothing staged was under plugins/.
`run-plugin-lint.sh --fix` silently skipped the fix for plugins that
lint through a Makefile.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNNERS = ["run-plugin-tests.sh", "run-plugin-typecheck.sh", "run-plugin-lint.sh"]


def _sandbox(tmp_path: Path) -> Path:
    """A git repo holding the runner scripts and one staged README."""
    shutil.copytree(ROOT / "scripts", tmp_path / "scripts")
    (tmp_path / "plugins").mkdir()
    (tmp_path / "README.md").write_text("x\n")
    env = _env(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, env=env, check=True)
    return tmp_path


def _env(tmp_path: Path, path_prefix: str = "") -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["HOME"] = str(tmp_path)
    if path_prefix:
        env["PATH"] = f"{path_prefix}:{env['PATH']}"
    return env


def _run(repo: Path, script: str, *args: str, path_prefix: str = ""):
    return subprocess.run(
        ["/bin/bash", f"scripts/{script}", *args],
        cwd=repo,
        env=_env(repo, path_prefix),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.parametrize("script", RUNNERS)
def test_an_unknown_plugin_name_fails_the_gate(script: str, tmp_path: Path) -> None:
    """A typo in a CI matrix ran zero checks and printed a pass."""
    result = _run(_sandbox(tmp_path), script, "no-such-plugin")
    assert result.returncode != 0
    assert "no-such-plugin" in result.stdout + result.stderr


@pytest.mark.parametrize("script", RUNNERS)
def test_changed_with_no_plugin_files_exits_cleanly(
    script: str, tmp_path: Path
) -> None:
    """grep's no-match status killed the script under pipefail."""
    result = _run(_sandbox(tmp_path), script, "--changed")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No plugin changes detected" in result.stdout + result.stderr


def test_fix_reaches_ruff_for_a_makefile_linted_plugin(tmp_path: Path) -> None:
    """`--fix` ran `make lint`, which never passes --fix to ruff."""
    repo = _sandbox(tmp_path)
    plugin = repo / "plugins" / "demo"
    (plugin / "src").mkdir(parents=True)
    (plugin / "Makefile").write_text("lint:\n\t@echo make-lint-ran\n")
    (plugin / "pyproject.toml").write_text("[tool.ruff]\n")
    shims = tmp_path / "shims"
    shims.mkdir()
    log = tmp_path / "uv.log"
    uv = shims / "uv"
    uv.write_text(f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\n')
    uv.chmod(0o755)

    result = _run(repo, "run-plugin-lint.sh", "--fix", "demo", path_prefix=str(shims))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--fix" in log.read_text()
