"""Tests for gif_demo.sh script functionality."""

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def gif_demo_script(scripts_dir: Path) -> Path:
    """Return path to gif_demo.sh."""
    return scripts_dir / "gif_demo.sh"


class TestGifDemoHelp:
    """Tests for gif_demo.sh help functionality."""

    def test_help_flag_short(self, gif_demo_script: Path) -> None:
        """Script should respond to -h flag."""
        result = subprocess.run(
            [str(gif_demo_script), "-h"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout

    def test_help_flag_long(self, gif_demo_script: Path) -> None:
        """Script should respond to --help flag."""
        result = subprocess.run(
            [str(gif_demo_script), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage" in result.stdout
        assert "TMP_DIR" in result.stdout
        assert "GIF_FPS" in result.stdout


class TestGifDemoDependencies:
    """Tests for gif_demo.sh dependency checking."""

    def test_requires_ffmpeg(self, gif_demo_script: Path, tmp_path: Path) -> None:
        """Script should fail gracefully without ffmpeg.

        This used to be skipped whenever ffmpeg was installed, which is
        every developer machine and every CI runner that can run the rest
        of the suite, so the error path it guards was never exercised.
        The script reaches its ffmpeg check using only bash builtins, so
        handing it a PATH that contains bash and nothing else reproduces
        a machine without ffmpeg without mocking anything.
        """
        stub_bin = tmp_path / "bin"
        stub_bin.mkdir()
        bash = shutil.which("bash")
        assert bash, "bash is required to run the script under test"
        # `#!/usr/bin/env bash` still resolves, `command -v ffmpeg` does not.
        (stub_bin / "bash").symlink_to(bash)

        result = subprocess.run(
            [str(gif_demo_script)],
            capture_output=True,
            text=True,
            env={"TMP_DIR": str(tmp_path), "PATH": str(stub_bin)},
        )
        assert result.returncode != 0
        # Check for the specific error message from the script
        output = result.stderr + result.stdout
        assert "ffmpeg" in output.lower(), (
            f"Expected ffmpeg error message, got: {output}"
        )


@pytest.mark.integration
class TestGifDemoExecution:
    """Integration tests for gif_demo.sh execution (requires ffmpeg)."""

    def test_generates_gif(
        self, gif_demo_script: Path, has_ffmpeg: bool, tmp_path: Path
    ) -> None:
        """Script should generate a GIF file."""
        if not has_ffmpeg:
            pytest.skip("ffmpeg not installed")

        result = subprocess.run(
            [str(gif_demo_script)],
            capture_output=True,
            text=True,
            env={
                "TMP_DIR": str(tmp_path),
                "DURATION": "1",  # Short duration for faster tests
                "PATH": os.environ.get("PATH", ""),
            },
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"

        output_gif = tmp_path / "output.gif"
        assert output_gif.exists(), "GIF file was not created"
        assert output_gif.stat().st_size > 0, "GIF file is empty"

    def test_respects_custom_output(
        self, gif_demo_script: Path, has_ffmpeg: bool, tmp_path: Path
    ) -> None:
        """Script should respect OUTPUT environment variable."""
        if not has_ffmpeg:
            pytest.skip("ffmpeg not installed")

        custom_output = tmp_path / "custom.gif"
        result = subprocess.run(
            [str(gif_demo_script)],
            capture_output=True,
            text=True,
            env={
                "TMP_DIR": str(tmp_path),
                "OUTPUT": str(custom_output),
                "DURATION": "1",
                "PATH": os.environ.get("PATH", ""),
            },
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert custom_output.exists(), "Custom output GIF was not created"

    def test_prints_statistics(
        self, gif_demo_script: Path, has_ffmpeg: bool, tmp_path: Path
    ) -> None:
        """Script should print file statistics."""
        if not has_ffmpeg:
            pytest.skip("ffmpeg not installed")

        result = subprocess.run(
            [str(gif_demo_script)],
            capture_output=True,
            text=True,
            env={
                "TMP_DIR": str(tmp_path),
                "DURATION": "1",
                "PATH": os.environ.get("PATH", ""),
            },
        )
        assert result.returncode == 0

        output = result.stdout
        assert "Input:" in output
        assert "Output:" in output
        assert "size:" in output.lower()


class TestGifDemoShellRules:
    """Feature: the script follows the house shell rules.

    As a maintainer reading any script in this repository
    I want one structure across all of them
    So that behavior lives in functions and output goes through log().

    The rules are in `.claude/rules/shell-scripts.md`: no bare `echo`,
    no top-down logic, and `main "$@"` as the last line.
    """

    @staticmethod
    def _code_lines(script: Path) -> list[str]:
        """Source lines with comments and blank lines dropped."""
        return [
            line
            for line in script.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    def test_last_line_is_main(self, gif_demo_script: Path) -> None:
        """Scenario: the entry point is the last statement in the file."""
        lines = gif_demo_script.read_text(encoding="utf-8").splitlines()

        assert lines[-1].strip() == 'main "$@"', (
            f'last line is {lines[-1]!r}; the house rule requires main "$@"'
        )

    def test_no_bare_echo(self, gif_demo_script: Path) -> None:
        """Scenario: every output goes through the logging helper."""
        offenders = [
            line
            for line in self._code_lines(gif_demo_script)
            if re.search(r"\becho\b", line)
        ]

        assert not offenders, f"bare echo at: {offenders}"

    def test_defines_usage_and_main(self, gif_demo_script: Path) -> None:
        """Scenario: usage and main are functions, not inline branches."""
        source = gif_demo_script.read_text(encoding="utf-8")

        assert re.search(r"^usage\(\)", source, re.MULTILINE)
        assert re.search(r"^main\(\)", source, re.MULTILINE)

    def test_no_fixed_temp_path(self, gif_demo_script: Path) -> None:
        """Scenario: the work directory is not a predictable shared path."""
        source = gif_demo_script.read_text(encoding="utf-8")

        assert "/tmp/scry-gif-test" not in source
        assert "mktemp -d" in source

    def test_parses_under_bash(self, gif_demo_script: Path) -> None:
        """Scenario: the restructured script is still syntactically valid."""
        result = subprocess.run(
            ["bash", "-n", str(gif_demo_script)], capture_output=True, text=True
        )

        assert result.returncode == 0, result.stderr

    def test_is_executable(self, gif_demo_script: Path) -> None:
        """Scenario: a script with a shebang carries the exec bit."""
        assert os.access(gif_demo_script, os.X_OK)

    def test_documents_the_xtrace_flag(self, gif_demo_script: Path) -> None:
        """Scenario: every script supports and documents an xtrace flag."""
        result = subprocess.run(
            [str(gif_demo_script), "-h"], capture_output=True, text=True
        )

        assert result.returncode == 0
        assert "-x" in result.stdout
