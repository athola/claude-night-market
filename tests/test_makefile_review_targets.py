"""Plugin Makefile targets do what their help text says (Makefile review).

Each test runs the real `make` target, or `make -n` where running it
would be slow or mutate state, and pins a defect the 2026-10-05 Makefile
review reproduced. Finding ids are in each docstring. A target that
reports success after its command failed is the common shape.
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


# --- Test-selection fallbacks (M0-3, M0-4, M1-10, M1-15, M1-17, M2-6) -----
#
# `$(PYTEST) -k sel || $(PYTEST) tests/` ran a second, passing suite whenever
# the first failed, so a failing selected test passed the target. Where a
# selection can legitimately match nothing yet, common.mk's pytest_selection
# turns pytest's exit 5 into a note and lets every other failure through.

COMMON_MK = PLUGINS / "abstract/config/make/common.mk"


def _selection_makefile(tmp_path: Path, fake_exit: int) -> Path:
    fake = tmp_path / "fake-pytest"
    fake.write_text(f"#!/bin/sh\nexit {fake_exit}\n")
    fake.chmod(0o755)
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        f"include {COMMON_MK}\n"
        f"PYTEST := {fake}\n"
        "help:\n\t@true\n"
        "probe:\n\t@$(call pytest_selection,tests/ -m integration)\n"
    )
    return makefile


def _probe(makefile: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "-s", "-f", str(makefile), "probe"],
        cwd=makefile.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_an_empty_selection_is_reported_not_failed(tmp_path: Path) -> None:
    result = _probe(_selection_makefile(tmp_path, 5))
    assert result.returncode == 0, result.stderr
    assert "No tests matched" in result.stdout


@pytest.mark.parametrize("fake_exit", [1, 2, 4])
def test_a_failing_selection_fails_the_target(tmp_path: Path, fake_exit: int) -> None:
    assert _probe(_selection_makefile(tmp_path, fake_exit)).returncode != 0


def test_no_recipe_falls_back_to_another_pytest_run() -> None:
    offenders = []
    for makefile in [ROOT / "Makefile", *sorted(PLUGINS.glob("*/Makefile"))]:
        text = makefile.read_text().replace("\\\n", " ")
        for number, line in enumerate(text.splitlines(), 1):
            if line.startswith("\t") and re.search(
                r"\|\|\s*(\$\(PYTEST\)|\$\(UV_RUN\)\s+(python -m )?pytest)", line
            ):
                offenders.append(f"{makefile.relative_to(ROOT)}:{number}")
    assert not offenders, offenders


# --- Root Makefile (M1-2, M1-3, M1-4) --------------------------------------


def _root_make(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "--no-print-directory", "-f", str(ROOT / "Makefile"), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _fake_plugin(tmp_path: Path, name: str, recipes: str) -> None:
    plugin = tmp_path / "plugins" / name
    plugin.mkdir(parents=True)
    (plugin / "Makefile").write_text(recipes)


def test_root_clean_fails_when_a_plugin_clean_fails(tmp_path: Path) -> None:
    """M1-2: failures and their stderr were discarded, then "Done." rc 0."""
    _fake_plugin(tmp_path, "good", "clean:\n\t@true\n")
    _fake_plugin(tmp_path, "bad", "clean:\n\t@echo boom >&2; false\n")
    result = _root_make(tmp_path, "clean")
    assert result.returncode != 0
    assert "boom" in result.stderr


def test_root_plugin_check_names_the_plugins_it_skips(tmp_path: Path) -> None:
    """M1-3: plugins without plugin-check vanished from the summary."""
    _fake_plugin(tmp_path, "checked", "plugin-check:\n\t@true\n")
    _fake_plugin(tmp_path, "unchecked", "help:\n\t@true\n")
    result = _root_make(tmp_path, "plugin-check")
    assert result.returncode == 0, result.stderr
    assert "SKIP: plugins/unchecked" in result.stdout


def test_root_help_lists_every_documented_target() -> None:
    """M1-4: help was a hand-kept list that omitted `fix`, which lint cites."""
    result = subprocess.run(
        ["make", "--no-print-directory", "-C", str(ROOT), "help"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    documented = re.findall(
        r"^([a-zA-Z][\w-]*):[^=\n]*##", (ROOT / "Makefile").read_text(), re.M
    )
    missing = [
        t for t in documented if not re.search(rf"\b{re.escape(t)}\b", result.stdout)
    ]
    assert not missing, missing


@pytest.mark.parametrize("plugin", ["gauntlet", "herald"])
def test_catch_all_names_the_unknown_target(plugin: str) -> None:
    """M1-18, M1-19: the same `$$@` bug as egregore's."""
    result = _make(plugin, "no-such-target")
    assert "Unknown target 'no-such-target'" in result.stdout


@pytest.mark.parametrize("plugin", ["conserve", "conjure", "imbue"])
def test_plugin_clean_leaves_the_global_uv_cache_alone(plugin: str) -> None:
    """M0-5, M0-6, M0-7: `uv cache clean` wiped ~/.cache/uv for every project."""
    result = _make(plugin, "-n", "clean")
    assert "uv cache clean" not in result.stdout
