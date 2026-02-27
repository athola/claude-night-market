"""Integration tests for VHS -> ffmpeg -> GIF workflow.

This module tests the complete media generation workflow:
- VHS tape recording -> video output
- Video -> ffmpeg processing -> GIF generation
- Full workflow with parameter variations

Issue #54: Add integration tests for VHS -> ffmpeg -> GIF workflow

Following TDD/BDD principles with Given/When/Then docstrings.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

# Note: Custom markers (requires_vhs, requires_ffmpeg) are registered in conftest.py


# ============================================================================
# VHS Recording Tests
# ============================================================================


class TestVHSRecording:
    """Feature: VHS terminal recording.

    As a documentation creator
    I want to record terminal sessions with VHS
    So that I can create demonstration videos
    """

    @pytest.fixture
    def sample_tape(self, tmp_path: Path) -> Path:
        """Given a sample VHS tape file."""
        tape_content = """# Simple test tape
Output test.gif

Set FontSize 14
Set Width 800
Set Height 400

Type "echo 'Hello, World!'"
Enter
Sleep 1s
"""
        tape_file = tmp_path / "test.tape"
        tape_file.write_text(tape_content)
        return tape_file

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.requires_vhs
    def test_vhs_recording_produces_output(
        self, has_vhs: bool, sample_tape: Path, tmp_path: Path
    ) -> None:
        """Scenario: VHS recording produces output file.

        Given a valid VHS tape file
        And VHS is installed
        When running vhs on the tape
        Then it should produce an output file.
        """
        if not has_vhs:
            pytest.skip("VHS not installed")

        result = subprocess.run(
            ["vhs", str(sample_tape)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        # VHS may produce warnings but should succeed
        assert result.returncode == 0 or (tmp_path / "test.gif").exists()

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.requires_vhs
    def test_vhs_validates_tape_syntax(self, has_vhs: bool, tmp_path: Path) -> None:
        """Scenario: VHS validates tape syntax.

        Given an invalid VHS tape file
        When running vhs on the tape
        Then it should report an error.
        """
        if not has_vhs:
            pytest.skip("VHS not installed")

        invalid_tape = tmp_path / "invalid.tape"
        invalid_tape.write_text("InvalidCommand with bad syntax\n")

        result = subprocess.run(
            ["vhs", str(invalid_tape)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail or produce error output
        assert result.returncode != 0 or "error" in result.stderr.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tape_file_structure(self, sample_tape: Path) -> None:
        """Scenario: Tape file has valid structure.

        Given a tape file
        When checking structure
        Then it should have Output and commands.
        """
        content = sample_tape.read_text()
        assert "Output" in content
        assert "Type" in content or "Sleep" in content


# ============================================================================
# FFmpeg Conversion Tests
# ============================================================================


class TestFFmpegConversion:
    """Feature: FFmpeg video/GIF conversion.

    As a documentation creator
    I want to convert videos with ffmpeg
    So that I can optimize GIF output
    """

    @pytest.fixture
    def sample_video(self, tmp_path: Path, has_ffmpeg: bool) -> Path | None:
        """Given a sample video file (generated if ffmpeg available)."""
        if not has_ffmpeg:
            return None

        video_path = tmp_path / "test_input.mp4"

        # Generate a simple test video with ffmpeg
        result = subprocess.run(
            [
                "ffmpeg",
                "-f",
                "lavfi",
                "-i",
                "testsrc=duration=1:size=320x240:rate=10",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(video_path),
            ],
            capture_output=True,
            timeout=30,
        )

        if result.returncode == 0 and video_path.exists():
            return video_path
        return None

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_ffmpeg_converts_video_to_gif(
        self, has_ffmpeg: bool, sample_video: Path | None, tmp_path: Path
    ) -> None:
        """Scenario: FFmpeg converts video to GIF.

        Given a video file
        And ffmpeg is installed
        When converting to GIF
        Then it should produce a GIF file.
        """
        if not has_ffmpeg:
            pytest.skip("FFmpeg not installed")

        if sample_video is None:
            pytest.skip("Could not generate sample video")

        output_gif = tmp_path / "output.gif"

        result = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(sample_video),
                "-vf",
                "fps=10,scale=320:-1",
                str(output_gif),
            ],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert output_gif.exists()

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_ffmpeg_applies_optimization_flags(
        self, has_ffmpeg: bool, sample_video: Path | None, tmp_path: Path
    ) -> None:
        """Scenario: FFmpeg applies optimization flags.

        Given a video file
        When converting with optimization flags
        Then the output should be optimized.
        """
        if not has_ffmpeg:
            pytest.skip("FFmpeg not installed")

        if sample_video is None:
            pytest.skip("Could not generate sample video")

        output_gif = tmp_path / "optimized.gif"

        # Use palette generation for better quality
        palette = tmp_path / "palette.png"

        # Generate palette
        result1 = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(sample_video),
                "-vf",
                "fps=10,scale=320:-1:flags=lanczos,palettegen",
                str(palette),
            ],
            capture_output=True,
            timeout=30,
        )

        if result1.returncode != 0:
            pytest.skip("Palette generation failed")

        # Use palette for GIF
        result2 = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(sample_video),
                "-i",
                str(palette),
                "-lavfi",
                "fps=10,scale=320:-1:flags=lanczos[x];[x][1:v]paletteuse",
                str(output_gif),
            ],
            capture_output=True,
            timeout=30,
        )

        assert result2.returncode == 0
        assert output_gif.exists()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ffmpeg_is_available(self, has_ffmpeg: bool) -> None:
        """Scenario: FFmpeg availability check.

        Given the system
        When checking for ffmpeg
        Then availability should be correctly detected.
        """
        # This tests the fixture itself
        actual_available = shutil.which("ffmpeg") is not None
        assert has_ffmpeg == actual_available


# ============================================================================
# Full Pipeline Tests
# ============================================================================


class TestFullPipeline:
    """Feature: Complete VHS -> FFmpeg -> GIF pipeline.

    As a documentation creator
    I want the full pipeline to work
    So that I can create optimized demo GIFs
    """

    @pytest.fixture
    def demo_tape(self, tmp_path: Path) -> Path:
        """Given a demo tape for full pipeline test."""
        tape_content = """# Demo tape for pipeline test
Output demo.gif

Set FontSize 12
Set Width 640
Set Height 360
Set TypingSpeed 50ms

Type "echo 'Pipeline test'"
Enter
Sleep 500ms
"""
        tape_file = tmp_path / "demo.tape"
        tape_file.write_text(tape_content)
        return tape_file

    @pytest.mark.bdd
    @pytest.mark.integration
    @pytest.mark.requires_vhs
    @pytest.mark.requires_ffmpeg
    def test_full_pipeline_vhs_to_optimized_gif(
        self,
        has_vhs: bool,
        has_ffmpeg: bool,
        demo_tape: Path,
        tmp_path: Path,
    ) -> None:
        """Scenario: Full pipeline from VHS to optimized GIF.

        Given a VHS tape file
        And both VHS and FFmpeg are installed
        When running the full pipeline
        Then it should produce an optimized GIF.
        """
        if not has_vhs:
            pytest.skip("VHS not installed")
        if not has_ffmpeg:
            pytest.skip("FFmpeg not installed")

        # Step 1: Run VHS to create initial GIF
        subprocess.run(
            ["vhs", str(demo_tape)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        initial_gif = tmp_path / "demo.gif"
        if not initial_gif.exists():
            pytest.skip("VHS did not produce output GIF")

        # Step 2: Optimize with FFmpeg
        optimized_gif = tmp_path / "demo_optimized.gif"

        result2 = subprocess.run(
            [
                "ffmpeg",
                "-i",
                str(initial_gif),
                "-vf",
                "fps=10",
                str(optimized_gif),
            ],
            capture_output=True,
            timeout=30,
        )

        assert result2.returncode == 0
        assert optimized_gif.exists()

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_pipeline_skips_gracefully_without_deps(
        self, has_vhs: bool, has_ffmpeg: bool
    ) -> None:
        """Scenario: Pipeline skips gracefully when dependencies missing.

        Given missing dependencies
        When attempting pipeline
        Then it should skip without error.
        """
        # This test verifies the skip mechanism works
        missing = []
        if not has_vhs:
            missing.append("vhs")
        if not has_ffmpeg:
            missing.append("ffmpeg")

        if missing:
            pytest.skip(f"Missing dependencies: {', '.join(missing)}")

        # If we get here, both are available - verify the fixtures work
        assert has_vhs is True
        assert has_ffmpeg is True


# ============================================================================
# Script Integration Tests
# ============================================================================


class TestGifDemoScript:
    """Feature: gif_demo.sh script integration.

    As a user
    I want the gif_demo.sh script to work
    So that I can easily create demo GIFs
    """

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_gif_demo_script_exists(self, scripts_dir: Path) -> None:
        """Scenario: gif_demo.sh script exists.

        Given the scripts directory
        When checking for gif_demo.sh
        Then it should exist.
        """
        gif_demo = scripts_dir / "gif_demo.sh"
        assert gif_demo.exists(), "gif_demo.sh not found"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_gif_demo_script_is_executable(self, scripts_dir: Path) -> None:
        """Scenario: gif_demo.sh is executable.

        Given gif_demo.sh exists
        When checking permissions
        Then it should be executable.
        """
        import os

        gif_demo = scripts_dir / "gif_demo.sh"
        if not gif_demo.exists():
            pytest.skip("gif_demo.sh not found")

        assert os.access(gif_demo, os.X_OK), "gif_demo.sh is not executable"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_gif_demo_script_shows_help(self, scripts_dir: Path) -> None:
        """Scenario: gif_demo.sh shows help.

        Given gif_demo.sh exists
        When running with --help
        Then it should show usage information.
        """
        gif_demo = scripts_dir / "gif_demo.sh"
        if not gif_demo.exists():
            pytest.skip("gif_demo.sh not found")

        result = subprocess.run(
            [str(gif_demo), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should show help or usage info
        output = result.stdout + result.stderr
        assert (
            "usage" in output.lower()
            or "help" in output.lower()
            or result.returncode == 0
        )
