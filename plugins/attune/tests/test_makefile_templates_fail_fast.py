"""Generated Makefiles fail a recipe on a failed pipeline stage, on any make.

GNU make 3.81, which macOS ships, ignores ``.SHELLFLAGS``. The templates
used to print a warning and run without ``-euo pipefail`` there. 3.81
honors flags written into ``SHELL`` itself, which is what the repository's
shared ``common.mk`` does.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
STRICT = [
    TEMPLATES / "python" / "Makefile.template",
    TEMPLATES / "typescript" / "Makefile.template",
]

pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="needs make")


def _rendered_head(template: Path) -> str:
    """The template's preamble, up to its first rule, with placeholders filled."""
    text = re.sub(r"\{\{\w+\}\}", "x", template.read_text())
    return text.split("\n# Configuration", 1)[0]


@pytest.mark.parametrize("template", STRICT, ids=lambda p: p.parent.name)
def test_a_failing_pipeline_stage_fails_the_recipe(
    template: Path, tmp_path: Path
) -> None:
    """`false | cat; echo reached` stops at false under the template's shell."""
    makefile = tmp_path / "Makefile"
    makefile.write_text(
        _rendered_head(template) + "\nprobe:\n\t@false | cat; echo reached\n"
    )

    result = subprocess.run(
        ["make", "-s", "-f", str(makefile), "probe"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode != 0
    assert "reached" not in result.stdout
    assert "ignores .SHELLFLAGS" not in result.stderr


def test_the_hand_written_command_stub_fails_instead_of_passing() -> None:
    """``test-attune`` printed "Validating..." and exited 0, which read as a
    passing test for a command nothing tests.
    """
    plugin = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["make", "-C", str(plugin), "test-attune"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode != 0
    assert "Validating" not in result.stdout
    assert "No automated test" in result.stdout
