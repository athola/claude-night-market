"""tool_performance_analyzer.py: probes each executable under a skills tree.

A probe that hangs or cannot start must still produce a row, or the report
silently drops the tools most worth looking at.
"""

from __future__ import annotations

import importlib
import stat
import subprocess
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


@pytest.fixture
def analyzer_module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    # The script imports cli_scaffold as a sibling, the way it runs.
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return importlib.import_module("tool_performance_analyzer")


def _tool(root: Path, name: str, body: str, *, executable: bool = True) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


@pytest.mark.unit
def test_only_visible_non_test_executables_are_probed(
    tmp_path: Path, analyzer_module: ModuleType
) -> None:
    """GIVEN executables, a plain file, a dotfile and a test script
    WHEN the tree is analyzed
    THEN only the visible, non-test executables are probed
    """
    ok = "#!/bin/sh\nexit 0\n"
    _tool(tmp_path, "skill/run.sh", ok)
    _tool(tmp_path, "skill/notes.md", "text", executable=False)
    _tool(tmp_path, "skill/.hidden.sh", ok)
    _tool(tmp_path, "skill/test_run.sh", ok)

    results = analyzer_module.ToolPerformanceAnalyzer(tmp_path).analyze_tools()

    assert results["total_tools"] == 1
    assert set(results["tools"]) == {"run.sh"}
    assert results["tools"]["run.sh"]["success"] is True


@pytest.mark.unit
def test_a_failing_tool_reports_its_exit_code_and_output(
    tmp_path: Path, analyzer_module: ModuleType
) -> None:
    """GIVEN a tool that prints and exits 3
    WHEN it is probed
    THEN its row records the exit code, the output length and a failure
    """
    _tool(tmp_path, "bad.sh", "#!/bin/sh\necho oops >&2\nexit 3\n")

    row = analyzer_module.ToolPerformanceAnalyzer(tmp_path).analyze_tools()["tools"][
        "bad.sh"
    ]

    assert row["exit_code"] == 3
    assert row["success"] is False
    assert row["output_length"] == len("oops\n")


@pytest.mark.unit
def test_a_hanging_tool_is_recorded_as_a_timeout(
    tmp_path: Path, analyzer_module: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GIVEN a tool whose probe exceeds the timeout
    WHEN it is probed
    THEN it gets a timeout row instead of stopping the analysis
    """
    _tool(tmp_path, "slow.sh", "#!/bin/sh\nexit 0\n")

    def hang(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", hang)
    row = analyzer_module.ToolPerformanceAnalyzer(tmp_path).analyze_tools()["tools"][
        "slow.sh"
    ]

    assert row["timeout"] is True
    assert row["success"] is False
    assert row["execution_time"] == 5.0


@pytest.mark.unit
def test_a_tool_that_cannot_start_is_recorded_as_an_error(
    tmp_path: Path, analyzer_module: ModuleType
) -> None:
    """GIVEN an executable file with no interpreter line
    WHEN the probe cannot exec it
    THEN it gets an error row instead of stopping the analysis
    """
    _tool(tmp_path, "garbage.bin", "\x00\x01 not a program")

    row = analyzer_module.ToolPerformanceAnalyzer(tmp_path).analyze_tools()["tools"][
        "garbage.bin"
    ]

    assert row["error"] is True
    assert row["success"] is False


@pytest.mark.unit
def test_a_tool_printing_invalid_utf8_is_recorded_as_an_error(
    tmp_path: Path, analyzer_module: ModuleType
) -> None:
    """GIVEN a tool whose --help output is not valid UTF-8
    WHEN it is probed
    THEN it gets an error row instead of stopping the analysis
    """
    _tool(tmp_path, "binary.sh", "#!/bin/sh\nprintf '\\377'\n")

    row = analyzer_module.ToolPerformanceAnalyzer(tmp_path).analyze_tools()["tools"][
        "binary.sh"
    ]

    assert row["error"] is True
    assert row["success"] is False


@pytest.mark.unit
def test_report_marks_each_row_with_its_outcome(
    tmp_path: Path, analyzer_module: ModuleType
) -> None:
    """GIVEN one passing and one unstartable tool
    WHEN the report is rendered
    THEN each appears as a table row labeled OK or FAIL (error)
    """
    _tool(tmp_path, "good.sh", "#!/bin/sh\nexit 0\n")
    _tool(tmp_path, "garbage.bin", "\x00\x01")

    report = analyzer_module.ToolPerformanceAnalyzer(tmp_path).get_performance_report()

    assert "- **Total Tools:** 2" in report
    assert "| OK good.sh |" in report
    assert "| FAIL (error) garbage.bin |" in report


@pytest.mark.unit
def test_report_without_tools_has_no_results_table(
    tmp_path: Path, analyzer_module: ModuleType
) -> None:
    """GIVEN a tree with no executables
    WHEN the report is rendered
    THEN it states zero tools and omits the results table
    """
    report = analyzer_module.ToolPerformanceAnalyzer(tmp_path).get_performance_report()

    assert "- **Total Tools:** 0" in report
    assert "## Detailed Results" not in report


@pytest.mark.unit
def test_probe_passes_help_flag(tmp_path: Path, analyzer_module: ModuleType) -> None:
    """GIVEN a tool that succeeds only when asked for --help
    WHEN it is probed
    THEN the probe reports success, because the CLI probes with --help
    """
    _tool(tmp_path, "help.sh", '#!/bin/sh\n[ "$1" = "--help" ] || exit 9\n')

    row = analyzer_module.ToolPerformanceAnalyzer(tmp_path).analyze_tools()["tools"][
        "help.sh"
    ]

    assert row["success"] is True
    assert row["exit_code"] == 0


@pytest.mark.unit
def test_cli_delegates_measurement_to_skills_eval(analyzer_module: ModuleType) -> None:
    """GIVEN the CLI and the skills_eval analyzer
    THEN the CLI is built on the library, so the two cannot drift (#815)
    """
    from abstract.skills_eval.performance import (  # noqa: PLC0415 - imported after the fixture puts src on sys.path
        ToolPerformanceAnalyzer as LibraryAnalyzer,
    )

    assert issubclass(analyzer_module.ToolPerformanceAnalyzer, LibraryAnalyzer)
