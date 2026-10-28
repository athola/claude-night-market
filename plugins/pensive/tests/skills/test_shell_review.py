"""Tests for the shell-review skill.

Fixture-based tests verifying:
- Reference scripts exist and self-validate (shellcheck + shfmt)
- Structural rules (main, library guard, no echo, no exec bit on lib)
- Pattern detection for ruleset violations
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
LOGGING_SH = REPO_ROOT / "scripts" / "logging.sh"
SHELLCHECK_SH = REPO_ROOT / "scripts" / "shellcheck.sh"

# These four are the repository's only automated shell gate, and they
# shell out to tools that are not guaranteed to be present. Without a
# guard they fail rather than skip, which reads as a broken repository
# on any machine that has not installed them. The CI job installs both
# so the assertions do run there; see plugin-tests.yml.
needs_shellcheck = pytest.mark.skipif(
    shutil.which("shellcheck") is None, reason="shellcheck is not installed"
)
needs_shfmt = pytest.mark.skipif(
    shutil.which("shfmt") is None, reason="shfmt is not installed"
)


class TestReferenceScriptsExist:
    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_exists(self) -> None:
        """scripts/logging.sh must be present as the logging library."""
        assert LOGGING_SH.exists(), "scripts/logging.sh not found"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_exists(self) -> None:
        """scripts/shellcheck.sh must be present as the canonical runner."""
        assert SHELLCHECK_SH.exists(), "scripts/shellcheck.sh not found"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_not_executable(self) -> None:
        """logging.sh is a library; it must not carry the execute bit."""
        assert LOGGING_SH.exists()
        assert not os.access(LOGGING_SH, os.X_OK), (
            "logging.sh has execute bit set — libraries must not be executable"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_is_executable(self) -> None:
        """shellcheck.sh is an invoked script; it must be executable."""
        assert SHELLCHECK_SH.exists()
        assert os.access(SHELLCHECK_SH, os.X_OK), "shellcheck.sh missing execute bit"


class TestReferenceScriptsSelfValidate:
    @pytest.mark.bdd
    @pytest.mark.integration
    @needs_shellcheck
    def test_logging_sh_passes_shellcheck(self) -> None:
        """logging.sh must pass shellcheck -s sh with no warnings."""
        assert LOGGING_SH.exists()
        result = subprocess.run(
            ["shellcheck", "-s", "sh", str(LOGGING_SH)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"shellcheck failed on logging.sh:\n{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.bdd
    @pytest.mark.integration
    @needs_shellcheck
    def test_shellcheck_sh_passes_shellcheck(self) -> None:
        """shellcheck.sh must pass shellcheck -s sh -x (follows sources) with no warnings."""
        assert SHELLCHECK_SH.exists()
        result = subprocess.run(
            ["shellcheck", "-s", "sh", "-x", str(SHELLCHECK_SH)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=False,
        )
        assert result.returncode == 0, (
            f"shellcheck failed on shellcheck.sh:\n{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.bdd
    @pytest.mark.integration
    @needs_shfmt
    def test_logging_sh_formatted_by_shfmt(self) -> None:
        """logging.sh must be formatted exactly as shfmt -p -i 2 -ci produces."""
        assert LOGGING_SH.exists()
        result = subprocess.run(
            ["shfmt", "-p", "-i", "2", "-ci", "-d", str(LOGGING_SH)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"shfmt found formatting drift in logging.sh:\n{result.stdout}"
        )

    @pytest.mark.bdd
    @pytest.mark.integration
    @needs_shfmt
    def test_shellcheck_sh_formatted_by_shfmt(self) -> None:
        """shellcheck.sh must be formatted exactly as shfmt -p -i 2 -ci produces."""
        assert SHELLCHECK_SH.exists()
        result = subprocess.run(
            ["shfmt", "-p", "-i", "2", "-ci", "-d", str(SHELLCHECK_SH)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"shfmt found formatting drift in shellcheck.sh:\n{result.stdout}"
        )


class TestStructuralRules:
    """Structural and architectural shell rules from the project ruleset."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_ends_with_main_call(self) -> None:
        """Last executable line of an invoked script must be main \"$@\"."""
        assert SHELLCHECK_SH.exists()
        lines = [ln for ln in SHELLCHECK_SH.read_text().splitlines() if ln.strip()]
        assert lines[-1] == 'main "$@"', (
            f"last line must be 'main \"$@\"', got: {lines[-1]!r}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_has_no_main_call(self) -> None:
        """logging.sh is a library; it must not invoke main."""
        assert LOGGING_SH.exists()
        content = LOGGING_SH.read_text()
        assert 'main "$@"' not in content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_sets_loading_guard(self) -> None:
        """logging.sh must set __logging_loaded so callers can verify it loaded."""
        assert LOGGING_SH.exists()
        assert "__logging_loaded" in LOGGING_SH.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_has_no_set_e_or_set_u(self) -> None:
        """Libraries must not use set -e or set -u (flags leak to caller)."""
        assert LOGGING_SH.exists()
        for line in LOGGING_SH.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert "set -e" not in stripped, f"library uses set -e: {line!r}"
            assert "set -u" not in stripped, f"library uses set -u: {line!r}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_echo_in_logging_sh(self) -> None:
        """logging.sh must not use echo; all output through printf."""
        assert LOGGING_SH.exists()
        for line in LOGGING_SH.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not stripped.startswith("echo "), (
                f"echo found in logging.sh (use printf): {line!r}"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_echo_in_shellcheck_sh(self) -> None:
        """shellcheck.sh must not use echo; all output through log() or printf."""
        assert SHELLCHECK_SH.exists()
        for line in SHELLCHECK_SH.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            assert not stripped.startswith("echo "), (
                f"echo found in shellcheck.sh (use log()): {line!r}"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_defines_required_dependencies(self) -> None:
        """shellcheck.sh must declare REQUIRED_DEPENDENCIES for depcheck()."""
        assert SHELLCHECK_SH.exists()
        content = SHELLCHECK_SH.read_text()
        assert "REQUIRED_DEPENDENCIES" in content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_has_depcheck_function(self) -> None:
        """shellcheck.sh must define depcheck() to verify tool availability."""
        assert SHELLCHECK_SH.exists()
        assert "depcheck()" in SHELLCHECK_SH.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_has_usage_function(self) -> None:
        """shellcheck.sh must define usage() for the -h flag."""
        assert SHELLCHECK_SH.exists()
        assert "usage()" in SHELLCHECK_SH.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_sources_logging_relative(self) -> None:
        """shellcheck.sh must source logging.sh relative to its own location."""
        assert SHELLCHECK_SH.exists()
        content = SHELLCHECK_SH.read_text()
        assert "logging.sh" in content
        assert "${MYDIR" in content or "${0%/*}" in content


SAFETY_MODULE = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "unified-review"
    / "modules"
    / "shell-safety-patterns.md"
)
STRUCTURE_MODULE = SAFETY_MODULE.with_name("shell-structure-patterns.md")


def _detection_pattern(module: Path, heading: str) -> str:
    """Return the single-quoted `rg -n '...'` pattern under a module heading."""
    text = module.read_text(encoding="utf-8")
    section = re.search(rf"^## {re.escape(heading)}.*?(?=^## |\Z)", text, re.M | re.S)
    assert section is not None, f"heading {heading!r} not in {module.name}"
    match = re.search(r"^rg -n '([^']+)'", section.group(0), re.M)
    assert match is not None, f"no rg detection command under {heading!r}"
    return match.group(1)


def _rg_matches(pattern: str, script: Path) -> bool:
    result = subprocess.run(
        ["rg", "-n", pattern, str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


class TestPatternDetection:
    """The detection patterns shipped in the shell-review modules fire on violations."""

    def _write_fixture(
        self, tmp_path: Path, content: str, name: str = "fixture.sh"
    ) -> Path:
        script = tmp_path / name
        script.write_text(textwrap.dedent(content))
        return script

    @pytest.mark.bdd
    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("heading", "violation", "clean"),
        [
            (
                "No echo: use log() or printf",
                'echo "hello world"',
                "printf '%s\\n' hello",
            ),
            (
                "Braced variable references",
                "cd $DIR || exit 1",
                'cd "${DIR}" || exit 1',
            ),
            ("cd inside a subshell", "cd /tmp", '(cd "${dir}" && make)'),
            ("No basename or dirname", 'name=$(basename "$0")', 'name="${0##*/}"'),
            (
                "Library loading check form",
                'if [ -z "$__logging_loaded" ]; then',
                'case "${__logging_loaded:-NULL}" in',
            ),
            ("set -e / set -u in libraries", "set -eu", "log 1 loaded"),
        ],
    )
    def test_shipped_pattern_flags_violation_and_passes_clean_form(
        self, tmp_path: Path, heading: str, violation: str, clean: str
    ) -> None:
        pattern = _detection_pattern(SAFETY_MODULE, heading)
        bad = self._write_fixture(tmp_path, f"#!/bin/sh\n{violation}\n", "bad.sh")
        good = self._write_fixture(tmp_path, f"#!/bin/sh\n{clean}\n", "good.sh")

        assert _rg_matches(pattern, bad)
        assert not _rg_matches(pattern, good)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shipped_missing_main_check_flags_script_without_main_call(
        self, tmp_path: Path
    ) -> None:
        text = STRUCTURE_MODULE.read_text(encoding="utf-8")
        block = re.search(
            r"Detection: executable missing `main \"\$@\"` as last line\n\n```sh\n(.*?)```",
            text,
            re.S,
        )
        assert block is not None, "missing-main detection snippet not found"
        bad = self._write_fixture(
            tmp_path, "#!/bin/sh\ndo_thing() {\n  :\n}\ndo_thing\n", "bad.sh"
        )
        good = self._write_fixture(
            tmp_path, '#!/bin/sh\nmain() {\n  :\n}\nmain "$@"\n', "good.sh"
        )
        for script in (bad, good):
            script.chmod(0o755)

        result = subprocess.run(
            [
                "sh",
                "-c",
                block.group(1).replace("scripts/", f"{tmp_path}/"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert f"Missing main call: {bad}" in result.stdout
        assert f"Missing main call: {good}" not in result.stdout
