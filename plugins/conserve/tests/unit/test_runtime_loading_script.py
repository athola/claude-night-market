"""test_runtime_loading.sh must not lose a match to SIGPIPE.

Shell review S1-13. Each check piped a whole file through `echo | grep -q`
under pipefail. grep -q exits at the first match, so on a file larger
than the pipe buffer echo took SIGPIPE, the pipeline returned 141, and a
referenced module was reported as unreferenced.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]


def test_a_large_skill_file_still_finds_its_modules(tmp_path: Path) -> None:
    skill = tmp_path / "skills" / "bloat-detector"
    shutil.copytree(PLUGIN / "skills" / "bloat-detector", skill)
    text = (skill / "SKILL.md").read_text()
    padding = "\n".join(f"padding line {i}" for i in range(20000))
    (skill / "SKILL.md").write_text(f"{text}\n{padding}\n")

    result = subprocess.run(
        ["/bin/bash", str(PLUGIN / "tests" / "test_runtime_loading.sh")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout[-1500:]
    assert "NOT referenced" not in result.stdout
