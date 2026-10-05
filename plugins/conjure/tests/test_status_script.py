"""bin/status.sh finds the conjure scripts from any working directory.

Shell review S2-20. It imported usage_logger from the current directory
and ran a quota tracker from ~/.claude/hooks/gemini, a path nothing
installs. Outside plugins/conjure/scripts every section said
"unavailable".
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

STATUS = Path(__file__).resolve().parents[1] / "bin" / "status.sh"


def test_status_reports_from_an_unrelated_directory(tmp_path: Path) -> None:
    """Every section reports, with gemini shimmed to "not authenticated"."""
    shims = tmp_path / "shims"
    shims.mkdir()
    gemini = shims / "gemini"
    gemini.write_text("#!/bin/sh\nexit 1\n")
    gemini.chmod(0o755)
    result = subprocess.run(
        ["/bin/bash", str(STATUS)],
        cwd=tmp_path,
        env={
            **os.environ,
            "HOME": str(tmp_path),
            "PATH": f"{shims}:{os.environ['PATH']}",
        },
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "unavailable" not in result.stdout, result.stdout
