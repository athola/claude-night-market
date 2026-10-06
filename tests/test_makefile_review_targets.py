"""Plugin Makefile targets do what their help text says (Makefile review).

Each test runs the real `make` target, or `make -n` where running it
would be slow or mutate state, and pins a defect the 2026-10-05 Makefile
review reproduced. Finding ids are in each docstring. A target that
reports success after its command failed is the common shape.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"


def _make(plugin: str, *args: str, path_prefix: str = "", **env: str):
    environ = {
        k: v for k, v in os.environ.items() if not k.startswith(("MAKE", "GIT_"))
    }
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


def test_egregore_names_the_unknown_target() -> None:
    """M0-13: `$$@` reached the shell as an empty $@."""
    result = _make("egregore", "no-such-target")
    assert result.returncode != 0
    assert "Unknown target 'no-such-target'" in result.stdout


@pytest.mark.parametrize("plugin", ["conserve", "imbue"])
def test_help_lists_the_targets_python_mk_adds(plugin: str) -> None:
    """M0-15, M0-16: help read the literal Makefile, missing included targets."""
    result = _make(plugin, "help")
    assert result.returncode == 0, result.stderr
    assert "type-check" in result.stdout


@pytest.mark.parametrize(
    "plugin", ["archetypes", "leyline", "imbue", "conserve", "conjure", "sanctum"]
)
def test_debug_variables_shows_the_shell_flags_in_use(plugin: str) -> None:
    """M0-14: `$(SHELLFLAGS)` is never set; the include sets `.SHELLFLAGS`."""
    result = _make(plugin, "debug-variables")
    assert result.returncode == 0, result.stderr
    line = next(x for x in result.stdout.splitlines() if x.startswith("SHELLFLAGS:"))
    assert line.split(":", 1)[1].strip(), result.stdout


def test_sanctum_test_git_selects_tests() -> None:
    """M0-11: no test carries a `git` marker, so pytest exited 5 every time."""
    result = _make("sanctum", "test-git")
    assert result.returncode == 0, result.stdout[-1500:]


def test_sanctum_test_merge_docs_selects_tests() -> None:
    """M0-12: both selections matched nothing and the target always failed."""
    result = _make("sanctum", "test-merge-docs")
    assert result.returncode == 0, result.stdout[-1500:]


def test_conjure_delegate_verify_fails_when_listing_fails(tmp_path: Path) -> None:
    """M0-8: a failing service listing verified nothing and exited 0."""
    shims = _shim(tmp_path, "uv", "exit 1")
    result = _make("conjure", "delegate-verify", path_prefix=str(shims))
    assert result.returncode != 0


def test_imbue_citation_demo_fails_when_the_verifier_does_not_run() -> None:
    """M0-9: `|| true` then printed "rejected (exit 1)" whatever happened.

    UV_RUN=true stands in for a verifier that accepts both findings (exit 0).
    """
    result = _make("imbue", "demo-citation-verifier", "UV_RUN=true")
    assert result.returncode != 0


def test_imbue_ci_enforces_the_coverage_floor() -> None:
    """M0-21: ci ran test-all, which carries no --cov-fail-under."""
    result = _make("imbue", "-n", "ci")
    assert "--cov-fail-under=85" in result.stdout


def test_leyline_formatting_demo_counts_long_lines() -> None:
    """M0-10: exec() in a comprehension never updated the counter."""
    result = _make("leyline", "demo-formatting")
    assert result.returncode == 0, result.stderr
    skill = (PLUGINS / "leyline/skills/markdown-formatting/SKILL.md").read_text()
    in_code, expected = False, 0
    for line in skill.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        elif (
            not in_code
            and len(line.rstrip()) > 80
            and not line.startswith(("|", "---"))
        ):
            expected += 1
    assert f"{expected} violations found" in result.stdout


def test_leyline_update_demo_lists_plugins_with_versions() -> None:
    """M0-19: `|| echo ?` never fired and __pycache__ was listed."""
    result = _make("leyline", "demo-update-all-plugins")
    assert result.returncode == 0, result.stderr
    rows = [x for x in result.stdout.splitlines() if x.startswith("  ") and ":" in x]
    assert rows
    assert not any("__pycache__" in x for x in rows)
    assert all(x.split(":", 1)[1].strip() for x in rows), rows


def test_leyline_memory_profile_reports_a_missing_profiler(tmp_path: Path) -> None:
    """M0-20: it probed system python3 and exited 0 when the tool was absent."""
    result = _make("leyline", "memory-profile", "UV_RUN=env -i /usr/bin/python3 -S")
    assert result.returncode != 0
    assert "memory_profiler" in result.stdout + result.stderr


def test_conserve_status_counts_its_scripts() -> None:
    """M0-18: it counted a tools/ directory that does not exist."""
    result = _make("conserve", "status")
    line = next(x for x in result.stdout.splitlines() if x.startswith("Scripts:"))
    assert int(line.split(":")[1]) > 0


def test_conserve_context_demo_measures_conserve() -> None:
    """M0-1: bad flags fell back to counting abstract's skills as conserve's."""
    result = _make("conserve", "demo-context")
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    # The fallback line, printed when the optimizer call failed.
    assert "Context optimizer: skills/ =" not in result.stdout


def test_conserve_bloat_scan_demo_runs_the_scanner() -> None:
    """M0-2: `--report` was rejected and `|| echo` reported success."""
    result = _make("conserve", "demo-bloat-scan")
    assert result.returncode == 0, result.stderr
    assert "unrecognized arguments" not in result.stderr
