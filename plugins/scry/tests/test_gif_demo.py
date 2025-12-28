"""Tests for gif-demo.sh script functionality."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def gif_demo_script(scripts_dir: Path) -> Path:
    """Return path to gif-demo.sh."""
    return scripts_dir / "gif-demo.sh"


class TestGifDemoHelp:
    """Tests for gif-demo.sh help functionality."""

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
    """Tests for gif-demo.sh dependency checking."""

    def test_requires_ffmpeg(
        self, gif_demo_script: Path, has_ffmpeg: bool, tmp_path: Path
    ) -> None:
        """Script should fail gracefully without ffmpeg."""
        if has_ffmpeg:
            pytest.skip("ffmpeg is installed, cannot test missing dependency")

        result = subprocess.run(
            [str(gif_demo_script)],
            capture_output=True,
            text=True,
            env={"TMP_DIR": str(tmp_path), "PATH": ""},
        )
        assert result.returncode != 0
        assert "ffmpeg" in result.stderr.lower() or "ffmpeg" in result.stdout.lower()


@pytest.mark.integration
class TestGifDemoExecution:
    """Integration tests for gif-demo.sh execution (requires ffmpeg)."""

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
                "PATH": subprocess.os.environ.get("PATH", ""),
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
                "PATH": subprocess.os.environ.get("PATH", ""),
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
                "PATH": subprocess.os.environ.get("PATH", ""),
            },
        )
        assert result.returncode == 0

        output = result.stdout
        assert "Input:" in output
        assert "Output:" in output
        assert "size:" in output.lower()
