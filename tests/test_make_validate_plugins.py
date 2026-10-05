"""Guard `make validate-plugins`: the marketplace and every plugin go
through `claude plugin validate`.

The validator is the harness's own reading of a plugin: it reports agent
fields the harness ignores, unquoted ${CLAUDE_PLUGIN_ROOT}, and marketplace
keys it strips at load (CLI 2.1.259+ for `--json`, 2.1.281 for the quote
check). Nothing ran it before this target, so seven agents shipped with
inert tool restrictions. Errors fail the target. Warnings are reported:
28 remain on sanctum command module files the loader never reads.

A fake ``claude`` first on PATH drives the recipe without the real CLI.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_MAKEFILE = REPO_ROOT / "Makefile"
SYSTEM_PATH = "/usr/bin:/bin"


def _plugins() -> list[str]:
    return sorted(
        f"plugins/{manifest.parent.parent.name}"
        for manifest in (REPO_ROOT / "plugins").glob("*/.claude-plugin/plugin.json")
    )


def _fake_claude(tmp_path: Path, fail_on: str = "") -> tuple[Path, Path]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.log"
    script = bin_dir / "claude"
    script.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
        f'case "$3" in */{fail_on}) [ -n "{fail_on}" ] && exit 1 ;; esac\n'
        "exit 0\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir, log


def _run_target(path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "--no-print-directory", "validate-plugins"],
        cwd=REPO_ROOT,
        env={**os.environ, "PATH": path},
        capture_output=True,
        text=True,
        check=False,
    )


def test_validate_plugins_is_a_documented_phony_target() -> None:
    text = ROOT_MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^validate-plugins:.*## ", text, re.MULTILINE)
    joined = text.replace("\\\n", " ")
    phony = " ".join(re.findall(r"^\.PHONY:(.*)$", joined, re.MULTILINE))
    assert "validate-plugins" in phony.split()
    assert re.search(r'@echo "  validate-plugins\s', text)


def test_target_validates_the_marketplace_and_every_plugin(tmp_path: Path) -> None:
    bin_dir, log = _fake_claude(tmp_path)
    completed = _run_target(f"{bin_dir}:{SYSTEM_PATH}")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    calls = log.read_text().splitlines()
    assert "plugin validate ." in calls
    for plugin in _plugins():
        assert f"plugin validate {plugin}" in calls


def test_a_plugin_that_fails_validation_fails_the_target(tmp_path: Path) -> None:
    bin_dir, _ = _fake_claude(tmp_path, fail_on="sanctum")
    completed = _run_target(f"{bin_dir}:{SYSTEM_PATH}")
    assert completed.returncode != 0


@pytest.mark.skipif(
    shutil.which("claude", path=SYSTEM_PATH) is not None,
    reason="a claude binary sits on the system PATH",
)
def test_target_skips_with_a_warning_when_claude_is_absent() -> None:
    completed = _run_target(SYSTEM_PATH)
    assert completed.returncode == 0
    assert "SKIP: claude CLI not on PATH" in completed.stdout
