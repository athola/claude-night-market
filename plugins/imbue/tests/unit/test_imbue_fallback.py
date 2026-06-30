"""PLR0913 regression tests for the imbue_validator.py import fallback.

When leyline.bootstrap (and therefore abstract.report_formatter) is
unavailable, imbue_validator.py defines local fallback versions of
ValidatorReport (a frozen dataclass) and format_validator_report().

These tests load the module in isolation with the cross-plugin import
blocked so the except branch executes, then exercise the fallback
formatter and assert its output matches the canonical format.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_IMBUE_VALIDATOR_SCRIPT = (
    Path(__file__).parent.parent.parent / "scripts" / "imbue_validator.py"
)

_FALLBACK_MOD_NAME = "_imbue_validator_fallback_test_isolation"


def _load_fallback_module(monkeypatch: pytest.MonkeyPatch) -> object:
    """Load imbue_validator.py with leyline.bootstrap blocked.

    Returns the freshly-loaded module object whose ValidatorReport and
    format_validator_report come from the except fallback branch.
    The @dataclass decorator requires the module to be registered in
    sys.modules before exec_module runs; monkeypatch handles teardown.
    """
    monkeypatch.setitem(sys.modules, "leyline.bootstrap", None)
    spec = importlib.util.spec_from_file_location(
        _FALLBACK_MOD_NAME,
        _IMBUE_VALIDATOR_SCRIPT,
    )
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, _FALLBACK_MOD_NAME, mod)
    spec.loader.exec_module(mod)
    return mod


class TestImbueValidatorFallback:
    """Feature: imbue_validator uses a local fallback when abstract import fails.

    As an imbue plugin operator running without the abstract plugin on path
    I want the validator to degrade gracefully
    So that reports are still produced in a parseable format.
    """

    def test_fallback_format_validator_report_no_issues(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: Fallback format_validator_report renders the success message.

        Given leyline.bootstrap is unavailable (import blocked at module load)
        When the fallback ValidatorReport is constructed with no issues
        And format_validator_report is called on it
        Then the output contains the title, skill count, and success_message.
        """
        mod = _load_fallback_module(monkeypatch)

        report = mod.ValidatorReport(
            title="Fallback Imbue Report",
            plugin_root=tmp_path,
            skill_file_count=4,
        )
        output = mod.format_validator_report(report)

        assert "Fallback Imbue Report" in output
        assert "=" * 50 in output
        assert "Skill Files: 4" in output
        assert "All validations passed successfully!" in output

    def test_fallback_format_validator_report_enumerates_issues(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: Fallback format_validator_report enumerates issues.

        Given leyline.bootstrap is unavailable (import blocked at module load)
        When the fallback ValidatorReport has two issues
        And format_validator_report is called on it
        Then the output contains the "Issues Found (2)" header.
        And each issue is listed with 1-based numbering.
        """
        mod = _load_fallback_module(monkeypatch)

        report = mod.ValidatorReport(
            title="Imbue Validation",
            plugin_root=tmp_path,
            skill_file_count=2,
            issues=["missing-exit-criteria", "no-evidence-block"],
        )
        output = mod.format_validator_report(report)

        assert "Issues Found (2)" in output
        assert "1. missing-exit-criteria" in output
        assert "2. no-evidence-block" in output

    def test_fallback_with_metadata_labels(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario: Fallback format_validator_report renders metadata pairs.

        Given a ValidatorReport with two metadata (label, value) tuples
        When format_validator_report is called
        Then each label appears in the output.
        And the plugin root path is present.
        """
        mod = _load_fallback_module(monkeypatch)

        report = mod.ValidatorReport(
            title="Meta Report",
            plugin_root=tmp_path,
            skill_file_count=1,
            metadata=[
                ("Review Skills", ["review-core"]),
                ("Evidence Skills", []),
            ],
        )
        output = mod.format_validator_report(report)

        assert "Review Skills" in output
        assert "Evidence Skills" in output
        assert str(tmp_path) in output
