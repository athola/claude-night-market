"""Regression tests for defects found in the 2026-10 bug review."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from parseltongue.analysis.compatibility_checker import CompatibilityChecker
from parseltongue.cli import main

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_recommendation_not_given_to_code_needing_only_py35() -> None:
    """Async code needs 3.5; the 3.10+ advice must not fire on it."""
    report = CompatibilityChecker().check_compatibility(
        "async def f():\n    pass\n", ["3.9"]
    )

    assert report["minimum_version"] == "3.5"
    assert not any("3.10+" in rec for rec in report["recommendations"])


@pytest.mark.unit
def test_recommendation_given_to_code_needing_py310() -> None:
    report = CompatibilityChecker().check_compatibility(
        "match x:\n    case 1:\n        pass\n", ["3.12"]
    )

    assert any("3.10+" in rec for rec in report["recommendations"])


@pytest.mark.unit
def test_cli_rejects_malformed_target_version(tmp_path: Path, capsys) -> None:
    source = tmp_path / "a.py"
    source.write_text("x = 1\n")

    code = main(["check-compat", str(source), "--target-version", "latest"])

    assert code == 1
    assert "target version" in capsys.readouterr().err.lower()


@pytest.mark.unit
def test_cli_reads_non_utf8_file_without_traceback(tmp_path: Path) -> None:
    source = tmp_path / "latin.py"
    source.write_bytes(b"# caf\xe9\nx = 1\n")

    assert main(["check-compat", str(source)]) == 0
