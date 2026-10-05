"""Guard `make test-mods`: every plugin that ships a mod is validated and tested.

A mod is a TypeScript module that a plugin's ``hooks/hooks.json`` names
under ``"modules"``. pytest and ruff never read it. Its only checks are
``claude plugin validate`` and ``claude plugin test``, so a plugin the
target skips has no gate at all.

Two conditions must not fail the build, because neither is a defect in
the plugin. A machine without the ``claude`` CLI cannot run either check.
And Anthropic can switch installed mods off remotely, in which case
``claude plugin test`` exits 1 with ``hooks modules are turned off``. Both
are reported and skipped.

The tests put a fake ``claude`` first on PATH so the recipe's branches
run without the real CLI or a network.

The house rule for every mod here is observe and draw only: no hook on
``tool.call`` or ``tool.check``. A mod that answered ``tool.call`` would
keep every plugin's Python PreToolUse guard from running, so that rule
is checked statically as well.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_DIR = REPO_ROOT / "plugins"
ROOT_MAKEFILE = REPO_ROOT / "Makefile"
# Enough for make, bash, grep and printf, and nothing that ships claude.
SYSTEM_PATH = "/usr/bin:/bin"

TOOL_HOOK = re.compile(r"""\bon\(\s*['"]tool\.(call|check)['"]""")


def _mod_plugins() -> list[str]:
    """Plugins whose hooks.json declares a modules key, as plugins/<name>."""
    found = []
    for hooks_json in sorted(PLUGINS_DIR.glob("*/hooks/hooks.json")):
        if "modules" in json.loads(hooks_json.read_text(encoding="utf-8")):
            found.append(f"plugins/{hooks_json.parent.parent.name}")
    return found


def _mod_modules() -> list[Path]:
    """Every module file a hooks.json names under modules."""
    modules = []
    for hooks_json in sorted(PLUGINS_DIR.glob("*/hooks/hooks.json")):
        declared = json.loads(hooks_json.read_text(encoding="utf-8"))
        modules += [hooks_json.parent / rel for rel in declared.get("modules", [])]
    return modules


def _fake_claude(tmp_path: Path, test_stdout: str, test_status: int) -> Path:
    """Write a claude stub that logs its argv and answers `plugin test` as told."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "calls.log"
    script = bin_dir / "claude"
    script.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{log}"\n'
        'case "$2" in\n'
        f"  test) printf '%s\\n' '{test_stdout}'; exit {test_status} ;;\n"
        "esac\n"
        "exit 0\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return bin_dir


def _run_target(path: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": path}
    return subprocess.run(
        ["make", "--no-print-directory", "test-mods"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_some_plugin_ships_a_mod() -> None:
    """The discovery matches something, so a green run is not an empty one."""
    assert "plugins/conserve" in _mod_plugins()
    assert "plugins/egregore" in _mod_plugins()


def test_test_mods_is_a_documented_phony_target() -> None:
    """Scenario: `make help` lists it and Make never mistakes it for a file."""
    text = ROOT_MAKEFILE.read_text(encoding="utf-8")
    assert re.search(r"^test-mods:.*## ", text, re.MULTILINE)
    joined = text.replace("\\\n", " ")
    phony = " ".join(re.findall(r"^\.PHONY:(.*)$", joined, re.MULTILINE))
    assert "test-mods" in phony.split()
    assert re.search(r'@echo "  test-mods\s', text)


def test_target_validates_and_tests_every_plugin_with_a_mod(tmp_path: Path) -> None:
    """Scenario: each plugin with a modules key gets both checks, and no other."""
    fake = _fake_claude(tmp_path, "1 pass", 0)
    completed = _run_target(f"{fake}:{SYSTEM_PATH}")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    calls = (tmp_path / "calls.log").read_text(encoding="utf-8").splitlines()
    expected = []
    for plugin in _mod_plugins():
        expected += [f"plugin validate {plugin}", f"plugin test {plugin}"]
    assert calls == expected


def test_a_failing_kit_test_fails_the_target(tmp_path: Path) -> None:
    """Scenario: a real test failure is not laundered into a skip."""
    fake = _fake_claude(tmp_path, "(fail) band shows the context percent", 1)
    completed = _run_target(f"{fake}:{SYSTEM_PATH}")
    assert completed.returncode != 0
    assert "(fail) band shows the context percent" in completed.stdout


def test_mods_turned_off_is_a_reported_skip(tmp_path: Path) -> None:
    """Scenario: the remote kill switch is not a plugin defect."""
    fake = _fake_claude(
        tmp_path, "claude plugin test: hooks modules are turned off in this process", 1
    )
    completed = _run_target(f"{fake}:{SYSTEM_PATH}")
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "SKIP: mods are turned off" in completed.stdout


@pytest.mark.skipif(
    shutil.which("claude", path=SYSTEM_PATH) is not None,
    reason="claude is installed under /usr/bin or /bin",
)
def test_target_skips_with_a_warning_when_claude_is_absent() -> None:
    """Scenario: a machine without the CLI still runs `make test-mods` green."""
    completed = _run_target(SYSTEM_PATH)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "SKIP: claude CLI not on PATH" in completed.stdout
    for plugin in _mod_plugins():
        assert plugin in completed.stdout


@pytest.mark.parametrize(
    "module", _mod_modules(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_mods_never_hook_tool_calls_or_checks(module: Path) -> None:
    """A mod answering tool.call would bypass every Python PreToolUse guard."""
    source = module.read_text(encoding="utf-8")
    assert not TOOL_HOOK.search(source), (
        f"{module.relative_to(REPO_ROOT)} hooks tool.call or tool.check; "
        "night-market mods observe and draw only"
    )
