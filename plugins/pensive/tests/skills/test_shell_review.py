"""Tests for the shell-review skill.

Fixture-based tests verifying:
- Reference scripts exist and self-validate (shellcheck + shfmt)
- Structural rules (main, library guard, no echo, no exec bit on lib)
- Pattern detection for ruleset violations
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
LOGGING_SH = REPO_ROOT / "scripts" / "logging.sh"
SHELLCHECK_SH = REPO_ROOT / "scripts" / "shellcheck.sh"


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
    def test_logging_sh_passes_shellcheck(self) -> None:
        """logging.sh must pass shellcheck -s sh with no warnings."""
        assert LOGGING_SH.exists()
        result = subprocess.run(
            ["shellcheck", "-s", "sh", str(LOGGING_SH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"shellcheck failed on logging.sh:\n{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_shellcheck_sh_passes_shellcheck(self) -> None:
        """shellcheck.sh must pass shellcheck -s sh -x (follows sources) with no warnings."""
        assert SHELLCHECK_SH.exists()
        result = subprocess.run(
            ["shellcheck", "-s", "sh", "-x", str(SHELLCHECK_SH)],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"shellcheck failed on shellcheck.sh:\n{result.stdout}\n{result.stderr}"
        )

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_logging_sh_formatted_by_shfmt(self) -> None:
        """logging.sh must be formatted exactly as shfmt -p -i 2 -ci produces."""
        assert LOGGING_SH.exists()
        result = subprocess.run(
            ["shfmt", "-p", "-i", "2", "-ci", "-d", str(LOGGING_SH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"shfmt found formatting drift in logging.sh:\n{result.stdout}"
        )

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_shellcheck_sh_formatted_by_shfmt(self) -> None:
        """shellcheck.sh must be formatted exactly as shfmt -p -i 2 -ci produces."""
        assert SHELLCHECK_SH.exists()
        result = subprocess.run(
            ["shfmt", "-p", "-i", "2", "-ci", "-d", str(SHELLCHECK_SH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"shfmt found formatting drift in shellcheck.sh:\n{result.stdout}"
        )


class TestStructuralRules:
    """Structural and architectural shell rules from the project ruleset."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_shellcheck_sh_ends_with_main_call(self) -> None:
        """Last executable line of an invoked script must be main \"${@}\"."""
        assert SHELLCHECK_SH.exists()
        lines = [ln for ln in SHELLCHECK_SH.read_text().splitlines() if ln.strip()]
        assert lines[-1] == 'main "${@}"', (
            f"last line must be 'main \"${{@}}\"', got: {lines[-1]!r}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_logging_sh_has_no_main_call(self) -> None:
        """logging.sh is a library; it must not invoke main."""
        assert LOGGING_SH.exists()
        content = LOGGING_SH.read_text()
        assert 'main "${@}"' not in content

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


class TestPatternDetection:
    """Pattern detection tests verifying the skill flags ruleset violations."""

    def _write_fixture(
        self, tmp_path: Path, content: str, name: str = "fixture.sh"
    ) -> Path:
        script = tmp_path / name
        script.write_text(textwrap.dedent(content))
        return script

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_echo_usage(self, tmp_path: Path) -> None:
        """rg pattern from the skill catches raw echo calls."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            echo "hello world"
            """,
        )
        result = subprocess.run(
            ["rg", "-n", r"^\s*echo\s", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "echo usage must be detectable by rg"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_missing_main_on_last_line(self, tmp_path: Path) -> None:
        """Scripts where last line is not main \"${@}\" should be flagged."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            do_thing() {
              printf '%s\\n' done
            }
            do_thing
            """,
        )
        lines = [ln for ln in script.read_text().splitlines() if ln.strip()]
        assert lines[-1] != 'main "${@}"'

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_unbraced_variable(self, tmp_path: Path) -> None:
        """rg pattern catches $VAR without braces."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            DIR=/tmp
            cd $DIR || exit 1
            """,
        )
        result = subprocess.run(
            ["rg", "-n", r"\$[A-Za-z_][A-Za-z_0-9]*[^}]", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "unbraced variables must be detectable"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_bare_cd_outside_subshell(self, tmp_path: Path) -> None:
        """rg pattern catches cd not wrapped in a subshell."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            cd /tmp
            rm -f ./*.tmp
            """,
        )
        result = subprocess.run(
            ["rg", "-n", r"^\s*cd\s+[^(]", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "bare cd must be detectable"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detects_basename_dirname_usage(self, tmp_path: Path) -> None:
        """rg pattern catches basename/dirname calls."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            name=$(basename "$0")
            dir=$(dirname "$0")
            """,
        )
        result = subprocess.run(
            ["rg", "-n", r"\bbasename\b|\bdirname\b", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "basename/dirname must be detectable"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_good_library_guard_form(self, tmp_path: Path) -> None:
        """case \"${__logging_loaded:-NULL}\" in is the required guard form."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            case "${__logging_loaded:-NULL}" in
              1) return 0 ;;
            esac
            """,
        )
        assert 'case "${__logging_loaded:-NULL}"' in script.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_bad_library_guard_form_detectable(self, tmp_path: Path) -> None:
        """if [ -z \"$__logging_loaded\" ] pattern should be flagged."""
        script = self._write_fixture(
            tmp_path,
            """\
            #!/bin/sh
            if [ -z "$__logging_loaded" ]; then
              return 0
            fi
            """,
        )
        result = subprocess.run(
            ["rg", r"\[ -z.*__\w+_loaded", str(script)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, "non-canonical library guard must be detectable"
