"""The per-plugin CI suites enforce each plugin's own coverage threshold.

Every plugin declares ``coverage_threshold`` under ``[tool.nightmarket]``,
and no plugin pyproject sets ``fail_under``. Only
``scripts/run-plugin-tests.sh`` read the table, so the PR gate ran with a
threshold of 0 and a drop from 92% to 60% passed every job.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "plugin-tests.yml"


def _suite_step() -> str:
    text = WORKFLOW.read_text()
    start = text.index("- name: Run the plugin suite")
    return text[start:]


def test_the_suite_step_passes_the_plugin_threshold_to_pytest() -> None:
    step = _suite_step()
    assert "coverage_threshold" in step
    assert '--cov-fail-under="$threshold"' in step
    assert re.search(r'pytest tests/ .*"\$\{cov_flag\[@\]\}"', step)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the step runs tomllib on 3.12")
@pytest.mark.parametrize(
    ("table", "expected"),
    [("[tool.nightmarket]\ncoverage_threshold = 85\n", "85"), ("[tool.other]\n", "")],
)
def test_the_threshold_read_matches_the_table(
    tmp_path: Path, table: str, expected: str
) -> None:
    """Run the step's own reader against a pyproject, as CI does."""
    reader = re.search(r"threshold=\$\((python3 -c .*?)\)\n", _suite_step(), re.S)
    assert reader, "the suite step must read the threshold with python3 -c"
    (tmp_path / "pyproject.toml").write_text(table)
    out = subprocess.run(
        ["bash", "-c", reader.group(1)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == expected
