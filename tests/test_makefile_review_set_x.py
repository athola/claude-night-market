"""Plugin Makefile targets fail when their check fails (Makefile review, set X).

Covers scribe, spec-kit, parseltongue, gauntlet and scry. Each test runs
the real target, `make -n` where running it would mutate the tree, or a
sandbox copy of the plugin Makefile where the defect needs a broken tree.
Finding ids from the 2026-10-05 review are in each docstring.

Since common.mk and markdown-only.mk put `-euo pipefail` into SHELL,
`cmd | head -N` has the opposite defect to the one the review found on
make 3.81: a passing command whose output outruns head dies of SIGPIPE
and fails the target. The head tests cover both directions.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"


def _env(path_prefix: str = "", path: str = "") -> dict[str, str]:
    environ = {
        k: v for k, v in os.environ.items() if not k.startswith(("MAKE", "GIT_"))
    }
    environ["PATH"] = path or environ["PATH"]
    if path_prefix:
        environ["PATH"] = f"{path_prefix}:{environ['PATH']}"
    return environ


def _make(
    plugin_dir: Path, *args: str, path_prefix: str = "", path: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["make", "--no-print-directory", "-C", str(plugin_dir), *args],
        env=_env(path_prefix, path),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )


def _sandbox(tmp_path: Path, plugin: str, *keep: str) -> Path:
    """A copy of one plugin's Makefile, plus the `keep` dirs, beside the
    real shared includes.
    """
    plugins = tmp_path / "plugins"
    target = plugins / plugin
    target.mkdir(parents=True)
    shutil.copy(PLUGINS / plugin / "Makefile", target / "Makefile")
    for name in keep:
        shutil.copytree(PLUGINS / plugin / name, target / name)
    (plugins / "abstract").symlink_to(PLUGINS / "abstract")
    return target


def _shim(tmp_path: Path, name: str, body: str) -> Path:
    shims = tmp_path / "shims"
    shims.mkdir(exist_ok=True)
    tool = shims / name
    tool.write_text(f"#!/bin/sh\n{body}\n")
    tool.chmod(0o755)
    return tool


def _commands(plugin: str) -> set[str]:
    return {p.stem for p in (PLUGINS / plugin / "commands").glob("*.md")}


def _demoed_commands(plugin: str, aggregate: str) -> set[str]:
    result = _make(PLUGINS / plugin, aggregate)
    assert result.returncode == 0, result.stdout + result.stderr
    return set(re.findall(r"^Command: /(\S+)$", result.stdout, re.MULTILINE))


def _target_names(plugin: str, prefix: str) -> set[str]:
    database = _make(PLUGINS / plugin, "-pn", "help").stdout
    return set(re.findall(rf"^{prefix}([a-z0-9-]+):", database, re.MULTILINE))


# ---------- scribe ----------


def test_scribe_validate_fails_when_the_plugin_tree_is_empty(tmp_path: Path) -> None:
    """M1-5: every check was `test && echo || echo`, so validate exited 0."""
    result = _make(_sandbox(tmp_path, "scribe"), "validate")
    assert result.returncode != 0, result.stdout
    assert "MISSING: plugin.json" in result.stdout


def test_scribe_validate_passes_on_the_real_tree() -> None:
    """M1-5: the strict validate still accepts the shipped plugin."""
    result = _make(PLUGINS / "scribe", "validate")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "MISSING" not in result.stdout


def test_scribe_typecheck_runs_mypy_on_src_scribe() -> None:
    """M1-6: typecheck printed a no-op over nine Python modules."""
    dry = _make(PLUGINS / "scribe", "-n", "typecheck").stdout
    assert re.search(r"mypy\b.*\bsrc/scribe\b", dry), dry
    result = _make(PLUGINS / "scribe", "typecheck")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Success" in result.stdout


def test_scribe_count_slop_fails_on_a_missing_file() -> None:
    """M1-7: grep's error was discarded and the file reported clean."""
    result = _make(PLUGINS / "scribe", "count-slop", "FILE=no/such/file.md")
    assert result.returncode != 0, result.stdout
    assert "No tier-1 slop words found" not in result.stdout


def test_scribe_count_slop_fails_without_file() -> None:
    """M1-7: with FILE unset grep read stdin and exited 0."""
    result = _make(PLUGINS / "scribe", "count-slop")
    assert result.returncode != 0, result.stdout


def test_scribe_count_slop_reports_a_clean_file(tmp_path: Path) -> None:
    """M1-7: the none-found message was unreachable on make 3.81."""
    clean = tmp_path / "clean.md"
    clean.write_text("Plain words only.\n")
    result = _make(PLUGINS / "scribe", "count-slop", f"FILE={clean}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "No tier-1 slop words found" in result.stdout


def test_scribe_count_slop_counts_slop_words(tmp_path: Path) -> None:
    """M1-7: the counting path still works."""
    sloppy = tmp_path / "sloppy.md"
    sloppy.write_text("We delve into a robust and robust design.\n")
    result = _make(PLUGINS / "scribe", "count-slop", f"FILE={sloppy}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert re.search(r"2 robust", result.stdout), result.stdout
    assert "No tier-1 slop words found" not in result.stdout


def test_scribe_command_demos_match_commands_dir() -> None:
    """M1-8: demos named 7 absent commands and skipped 6 shipped ones."""
    demoed = _demoed_commands("scribe", "demo-scribe-commands")
    assert demoed == _commands("scribe")


def test_scribe_has_a_test_target_per_command() -> None:
    """M1-8: test-* targets mirrored the stale demo list."""
    assert _target_names("scribe", "test-") >= _commands("scribe")
    stale = {"slop-scan", "doc-verify", "pr-review", "update-docs"}
    assert not stale & _target_names("scribe", "test-")


# ---------- spec-kit ----------


@pytest.mark.parametrize("target", ["demo-spec", "demo-tasks"])
def test_spec_kit_demo_fails_when_its_skill_is_missing(
    tmp_path: Path, target: str
) -> None:
    """M1-9: printed `[X] skill missing` and exited 0."""
    result = _make(_sandbox(tmp_path, "spec-kit", "commands"), target)
    assert result.returncode != 0, result.stdout
    assert "skill missing" in result.stdout


@pytest.mark.parametrize("target", ["demo-spec", "demo-tasks"])
def test_spec_kit_demo_passes_on_the_real_tree(target: str) -> None:
    """M1-9: the strict demos still accept the shipped skills."""
    result = _make(PLUGINS / "spec-kit", target)
    assert result.returncode == 0, result.stdout + result.stderr


def test_spec_kit_command_demos_match_commands_dir() -> None:
    """M1-12: claimed all commands, covered 9 of 11."""
    demoed = _demoed_commands("spec-kit", "demo-spec-kit-commands")
    assert demoed == _commands("spec-kit")


def test_spec_kit_has_a_test_target_per_command() -> None:
    """M1-12: speckit-converge and speckit-taskstoissues had no test-*."""
    assert _target_names("spec-kit", "test-") >= _commands("spec-kit")


# ---------- parseltongue ----------


@pytest.mark.parametrize("target", ["ci", "quality-check"])
def test_parseltongue_gate_checks_format_without_rewriting(target: str) -> None:
    """M1-13: ci ran `ruff format` and `ruff check --fix` before lint."""
    dry = _make(PLUGINS / "parseltongue", "-n", target).stdout
    assert "--fix" not in dry, dry
    for line in dry.splitlines():
        if re.search(r"ruff format\b", line):
            assert "--check" in line, line
    assert "format --check" in dry, dry


def test_parseltongue_demo_coverage_fails_when_pytest_fails() -> None:
    """M1-14: `pytest | head -30` took head's status on make 3.81."""
    result = _make(PLUGINS / "parseltongue", "demo-coverage", "PYTEST=false")
    assert result.returncode != 0, result.stdout


def test_parseltongue_demo_coverage_passes_on_long_output(tmp_path: Path) -> None:
    """M1-14: under pipefail, head closing early killed a passing pytest."""
    fake = _shim(tmp_path, "fake-pytest", "seq 1 20000")
    result = _make(PLUGINS / "parseltongue", "demo-coverage", f"PYTEST={fake}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "\n30\n" in result.stdout
    assert "\n31\n" not in result.stdout


def test_parseltongue_mutation_test_targets_src(tmp_path: Path) -> None:
    """M1-16: mutmut was pointed at ./parseltongue, not src/parseltongue."""
    log = tmp_path / "mutmut.args"
    mutmut = _shim(tmp_path, "mutmut", f'echo "$@" > "{log}"')
    result = _make(
        PLUGINS / "parseltongue", "mutation-test", path_prefix=str(mutmut.parent)
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "--paths-to-mutate src/parseltongue" in log.read_text()


def test_parseltongue_mutation_test_fails_without_mutmut() -> None:
    """M1-16: a missing mutmut printed a hint and exited 0."""
    result = _make(PLUGINS / "parseltongue", "mutation-test", path="/usr/bin:/bin")
    assert result.returncode != 0, result.stdout


# ---------- gauntlet ----------


def test_gauntlet_extract_demo_fails_when_the_extractor_fails(
    tmp_path: Path,
) -> None:
    """M1-20: `extractor.py | head -20` took head's status on make 3.81."""
    fake = _shim(tmp_path, "fake-uv-run", "echo partial; exit 3")
    result = _make(PLUGINS / "gauntlet", "demo-gauntlet-extract", f"UV_RUN={fake}")
    assert result.returncode != 0, result.stdout
    assert "partial" in result.stdout


def test_gauntlet_extract_demo_passes_on_long_output(tmp_path: Path) -> None:
    """M1-20: under pipefail, head closing early killed a passing extractor."""
    fake = _shim(tmp_path, "fake-uv-run", "seq 1 20000")
    result = _make(PLUGINS / "gauntlet", "demo-gauntlet-extract", f"UV_RUN={fake}")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "\n20\n" in result.stdout
    assert "\n21\n" not in result.stdout


# ---------- scry ----------


def test_scry_lint_fails_on_a_shell_syntax_error(tmp_path: Path) -> None:
    """M2-1: bash -n failures were dropped and lint printed [OK]."""
    plugin = _sandbox(tmp_path, "scry")
    scripts = plugin / "scripts"
    scripts.mkdir()
    (scripts / "a_broken.sh").write_text("if then fi (\n")
    (scripts / "b_fine.sh").write_text("true\n")
    result = _make(plugin, "lint")
    assert result.returncode != 0, result.stdout
    assert "[OK] bash -n" not in result.stdout


def test_scry_lint_passes_on_the_real_scripts() -> None:
    """M2-1: the strict lint still accepts the shipped scripts."""
    result = _make(PLUGINS / "scry", "lint")
    assert result.returncode == 0, result.stdout + result.stderr


def test_scry_validate_fails_when_the_plugin_tree_is_empty(tmp_path: Path) -> None:
    """M2-2: six `[X] ... missing` lines and exit 0."""
    result = _make(_sandbox(tmp_path, "scry"), "validate")
    assert result.returncode != 0, result.stdout
    assert "[X] plugin.json missing" in result.stdout


def test_scry_validate_passes_on_the_real_tree() -> None:
    """M2-2: the strict validate still accepts the shipped plugin."""
    result = _make(PLUGINS / "scry", "validate")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[X]" not in result.stdout


def test_scry_test_integration_fails_and_cleans_up_when_gif_demo_fails(
    tmp_path: Path,
) -> None:
    """M2-3: a failing demo-gif was masked by clean-gif-temp's status."""
    plugin = _sandbox(tmp_path, "scry")
    scripts = plugin / "scripts"
    scripts.mkdir()
    gif = scripts / "gif_demo.sh"
    gif.write_text('#!/bin/sh\nmkdir -p "$TMP_DIR"\necho "gif demo FAILED"\nexit 1\n')
    gif.chmod(0o755)
    _shim(tmp_path, "uv", "exit 0")
    shims = _shim(tmp_path, "ffmpeg", "exit 0").parent
    gif_dir = tmp_path / "gif-tmp"
    result = _make(
        plugin, "test-integration", f"GIF_DEMO_DIR={gif_dir}", path_prefix=str(shims)
    )
    assert "gif demo FAILED" in result.stdout, result.stdout + result.stderr
    assert result.returncode != 0, result.stdout
    assert not gif_dir.exists(), "clean-gif-temp did not run after the failure"


def test_scribe_demo_names_only_commands_scribe_ships() -> None:
    """The demo told users to run /slop-scan, which scribe does not ship."""
    result = subprocess.run(
        ["make", "--no-print-directory", "-C", str(ROOT / "plugins/scribe"), "demo"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    named = set(re.findall(r"^\s+/([a-z][\w-]*)", result.stdout, re.M))
    shipped = {p.stem for p in (ROOT / "plugins/scribe/commands").glob("*.md")}
    assert named and named <= shipped, named - shipped
