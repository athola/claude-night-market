"""add-subtitles.sh finds a font on macOS and accepts one by name.

Shell review S2-19. The candidates were Linux paths only, so on macOS the
script always stopped at "no candidate font found", though its comment
promised a graceful fallback. A font path with a space also has to
survive ffmpeg's filtergraph syntax.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(tmp_path: Path, **env: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    shims = tmp_path / "shims"
    shims.mkdir()
    args_log = tmp_path / "ffmpeg.args"
    ffmpeg = shims / "ffmpeg"
    ffmpeg.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$@" > "{args_log}"\n'
        'for last; do :; done; : > "$last"\n'
    )
    ffmpeg.chmod(0o755)
    gif_in = tmp_path / "in.gif"
    gif_in.write_bytes(b"GIF89a")
    result = subprocess.run(
        [
            "/bin/bash",
            str(ROOT / "assets/tapes/add-subtitles.sh"),
            str(gif_in),
            str(tmp_path / "out.gif"),
        ],
        env={**os.environ, "PATH": f"{shims}:{os.environ['PATH']}", **env},
        capture_output=True,
        text=True,
        errors="replace",
        timeout=60,
        check=False,
    )
    return result, args_log


def test_subtitle_font_override_is_used(tmp_path: Path) -> None:
    font = tmp_path / "My Font.ttf"
    font.write_bytes(b"\0")
    result, args_log = _run(tmp_path, SUBTITLE_FONT=str(font))
    assert result.returncode == 0, result.stderr
    assert f"fontfile='{font}'" in args_log.read_text()


def test_a_missing_override_names_the_variable(tmp_path: Path) -> None:
    result, _ = _run(tmp_path, SUBTITLE_FONT=str(tmp_path / "absent.ttf"))
    assert result.returncode != 0
    assert "SUBTITLE_FONT" in result.stderr


def test_bash_3_2_reaches_ffmpeg(tmp_path: Path) -> None:
    """bash 3.2 read the first byte of "…" in "$INPUT…" as part of the name.

    In a UTF-8 locale it stopped with "INPUT\\xe2: unbound variable" before
    ffmpeg ran.
    """
    font = tmp_path / "f.ttf"
    font.write_bytes(b"\0")
    result, args_log = _run(tmp_path, SUBTITLE_FONT=str(font), LC_ALL="en_US.UTF-8")
    assert result.returncode == 0, result.stderr
    assert args_log.exists()
