"""Plugin Makefile targets do what their help text says (Makefile review, set Y).

Each test runs the real `make` target, with a shim standing in for a tool
where the real one would install or mutate, or `make -n` where only the
command line matters. Finding ids from the 2026-10-06 review are in each
docstring.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"


def _make(plugin: str, *args: str, path_prefix: str = "", **env: str):
    # `uv run pytest` from the root puts the root venv on PATH, and its
    # tools (bandit among them) would answer for a plugin that lacks them.
    environ = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("MAKE", "GIT_")) and k != "VIRTUAL_ENV"
    }
    environ["PATH"] = os.pathsep.join(
        p
        for p in environ["PATH"].split(os.pathsep)
        if not p.startswith(str(ROOT / ".venv"))
    )
    if path_prefix:
        environ["PATH"] = f"{path_prefix}:{environ['PATH']}"
    environ.update(env)
    return subprocess.run(
        ["make", "--no-print-directory", "-C", str(PLUGINS / plugin), *args],
        env=environ,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )


def _shim(tmp_path: Path, name: str, body: str) -> Path:
    shims = tmp_path / "shims"
    shims.mkdir(exist_ok=True)
    tool = shims / name
    tool.write_text(f"#!/bin/sh\n{body}\n")
    tool.chmod(0o755)
    return shims


# A uv that fails only `uv run pre-commit ...` and succeeds otherwise.
_UV_FAILS_PRE_COMMIT = 'case "$1 $2" in "run pre-commit") exit 1 ;; esac\nexit 0'


@pytest.mark.parametrize(
    "target", ["skills/skill-authoring", "skills/skill-authoring/SKILL.md"]
)
def test_abstract_analyze_skill_accepts_its_documented_target(target: str) -> None:
    """M2-4: the recipe passed --path, which skill_analyzer.py rejects."""
    result = _make("abstract", "analyze-skill", f"TARGET={target}")
    assert result.returncode == 0, result.stderr[-1500:]


@pytest.mark.parametrize(
    "target", ["skills/skill-authoring", "skills/skill-authoring/SKILL.md"]
)
def test_abstract_improve_skill_finds_the_skill(target: str) -> None:
    """M2-5: both TARGET spellings looked for skills/X/X/SKILL.md or similar.

    The recipe printed only counts, so the "not found" result read as a
    one-issue plan. The issue lines are printed now, and the count must
    match a direct call on the skill's real location.
    """
    result = _make("abstract", "improve-skill", f"TARGET={target}")
    assert result.returncode == 0, result.stderr[-1500:]
    assert "Skill file not found" not in result.stdout
    direct = subprocess.run(
        [
            "uv",
            "run",
            "python",
            "-c",
            "from pathlib import Path; "
            "from abstract.skills_eval import ImprovementSuggester; "
            "r = ImprovementSuggester(Path('skills'))"
            ".analyze_skill('skill-authoring'); "
            "print(len(r['issues']))",
        ],
        cwd=PLUGINS / "abstract",
        capture_output=True,
        text=True,
        check=True,
    )
    assert f"Issues: {direct.stdout.strip()}" in result.stdout


def test_abstract_dev_setup_fails_when_uv_sync_fails(tmp_path: Path) -> None:
    """M2-7: `uv sync --dev || true` printed "ready" after the sync failed."""
    uv = _shim(tmp_path, "uv", "exit 1") / "uv"
    result = _make("abstract", "dev-setup", f"UV={uv}")
    assert result.returncode != 0
    assert "Development environment ready" not in result.stdout


def test_abstract_dev_setup_fails_when_hook_install_fails(tmp_path: Path) -> None:
    """M2-7: install-hooks' `pre-commit install || true` hid the failure."""
    uv = _shim(tmp_path, "uv", _UV_FAILS_PRE_COMMIT) / "uv"
    result = _make("abstract", "dev-setup", f"UV={uv}")
    assert result.returncode != 0
    assert "Development environment ready" not in result.stdout


def test_attune_dev_setup_fails_when_hook_install_fails(tmp_path: Path) -> None:
    """M2-8: `pre-commit install || true` exited 0 with no hooks installed."""
    uv = _shim(tmp_path, "uv", _UV_FAILS_PRE_COMMIT) / "uv"
    result = _make("attune", "dev-setup", f"UV={uv}")
    assert result.returncode != 0


def test_pensive_mutation_test_reports_surviving_mutants(tmp_path: Path) -> None:
    """M2-9: any mutmut failure printed "mutmut not installed" and exited 0."""
    shims = _shim(tmp_path, "mutmut", "echo '3 mutants survived'\nexit 2")
    result = _make("pensive", "mutation-test", path_prefix=str(shims))
    assert result.returncode != 0
    assert "not installed" not in result.stdout


@pytest.mark.parametrize("target", ["enable", "disable", "skills", "install"])
def test_memory_palace_control_targets_fail_when_the_cli_fails(
    tmp_path: Path, target: str
) -> None:
    """M2-10: every CLI failure was labeled "permission denied", exit 0."""
    uv = _shim(tmp_path, "uv", "exit 1") / "uv"
    result = _make("memory-palace", target, f"UV={uv}")
    assert result.returncode != 0
    assert "permission denied" not in result.stdout


def test_memory_palace_plugin_check_never_reads_the_users_store() -> None:
    """M2-11: list and search ran on an exported PALACES_DIR, not the demo."""
    real = "/nonexistent/real-palaces"
    result = _make("memory-palace", "-n", "plugin-check", PALACES_DIR=real)
    assert result.returncode == 0, result.stderr
    assert real not in result.stdout
    demo = str(PLUGINS / "memory-palace/.demo-palaces")
    cli_lines = [x for x in result.stdout.splitlines() if "memory_palace_cli" in x]
    for verb in ("list", "search"):
        assert any(
            f"PALACES_DIR={demo} " in x and f" {verb}" in x for x in cli_lines
        ), (verb, cli_lines)


def test_cartograph_test_quick_runs() -> None:
    """M2-12: python.mk passes --no-cov, which needs pytest-cov installed."""
    result = _make("cartograph", "test-quick")
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]


@pytest.mark.parametrize("plugin", ["cartograph", "pensive", "sanctum"])
def test_security_runs_bandit_from_the_plugin_environment(plugin: str) -> None:
    """M2-13: bandit was not a dependency, so `make security` could not spawn it."""
    result = _make(plugin, "security")
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]


def test_pensive_skill_review_warns_on_missing_frontmatter(tmp_path: Path) -> None:
    """M2-15: `grep -c` exits 1 on zero matches, and pipefail ended the loop.

    The recipe lines come from `make -n` and run under the same
    `bash -euo pipefail` every make here uses, against a skill tree where
    one skill has no frontmatter.
    """
    recipe = _make("pensive", "-n", "demo-skill-review")
    assert recipe.returncode == 0, recipe.stderr
    good = tmp_path / "skills/aa-good/SKILL.md"
    good.parent.mkdir(parents=True)
    good.write_text("---\nname: aa-good\ndescription: d\n---\n")
    bare = tmp_path / "skills/bb-nofm/SKILL.md"
    bare.parent.mkdir(parents=True)
    bare.write_text("# no frontmatter\n")
    result = subprocess.run(
        ["/bin/bash", "-euo", "pipefail", "-c", recipe.stdout],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[OK] aa-good" in result.stdout
    assert "[WARN] bb-nofm - missing frontmatter" in result.stdout


def test_pensive_install_targets_use_the_dev_dependency_group() -> None:
    """M2-16: `pip install -e ".[dev]"` asked for an extra pensive lacks."""
    result = _make("pensive", "-n", "dev-install", "deps-update")
    assert result.returncode == 0, result.stderr
    assert "pip install" not in result.stdout
    assert "uv sync --group dev" in result.stdout


@pytest.mark.parametrize(
    ("plugin", "script"),
    [
        ("tome", "src/tome/scripts/verify_canaries.py"),
        ("memory-palace", "scripts/memory_palace_cli.py"),
    ],
)
def test_memory_profile_probes_and_profiles_in_the_uv_environment(
    tmp_path: Path, plugin: str, script: str
) -> None:
    """M2-17: probed system python3, then profiled __init__.py first.

    The uv shim records each call and reports memory_profiler importable,
    so the target has to reach the profile command through uv.
    """
    log = tmp_path / "uv.log"
    uv = _shim(tmp_path, "uv", f'printf "%s\\n" "$*" >> "{log}"\nexit 0') / "uv"
    result = _make(plugin, "memory-profile", f"UV={uv}")
    assert result.returncode == 0, result.stdout + result.stderr
    calls = log.read_text().splitlines()
    profiled = [x for x in calls if "-m memory_profiler" in x]
    assert profiled == [f"run python -m memory_profiler {script}"], calls
    assert not any(re.search(r"__init__\.py", x) for x in calls)


def test_memory_profile_fails_when_the_profiler_is_missing(tmp_path: Path) -> None:
    """M2-17: the same probe, false in uv's environment, must not pass."""
    uv = _shim(tmp_path, "uv", "exit 1") / "uv"
    result = _make("tome", "memory-profile", f"UV={uv}")
    assert result.returncode != 0
    assert "memory_profiler" in result.stdout + result.stderr
