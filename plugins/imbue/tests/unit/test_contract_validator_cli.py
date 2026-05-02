"""Tests for the contract_validator CLI.

Feature: Contract validator CLI
    As a workflow author
    I want to invoke contract validation from the shell
    So that audit / review / research dispatches can gate on output quality.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "contract_validator.py"


def _write_findings(tmp_path: Path, body: str) -> Path:
    f = tmp_path / "findings.md"
    f.write_text(body)
    return f


def _write_contract(tmp_path: Path, contract: dict) -> Path:
    f = tmp_path / "contract.json"
    f.write_text(json.dumps(contract))
    return f


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestContractValidatorCli:
    """Run the validator from the command line."""

    @pytest.mark.unit
    def test_passing_findings_returns_zero(self, tmp_path: Path) -> None:
        """Scenario: A complete findings file passes."""
        findings = _write_findings(
            tmp_path,
            textwrap.dedent("""\
                # Findings

                ## Summary

                A short summary.

                ## Detailed Findings

                Some detail [E1] [E2] [E3].

                ## Evidence

                [E1] command output
                [E2] file ref
                [E3] manual test
            """),
        )
        contract = _write_contract(
            tmp_path,
            {
                "required_sections": ["summary", "detailed_findings", "evidence"],
                "min_evidence_count": 3,
            },
        )
        result = _run_cli("--findings", str(findings), "--contract", str(contract))
        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS" in result.stdout

    @pytest.mark.unit
    def test_failing_findings_returns_nonzero(self, tmp_path: Path) -> None:
        """Scenario: Insufficient evidence triggers FAIL exit code."""
        findings = _write_findings(
            tmp_path,
            "## Summary\n\nNo evidence at all.\n",
        )
        contract = _write_contract(
            tmp_path,
            {
                "required_sections": ["summary"],
                "min_evidence_count": 3,
            },
        )
        result = _run_cli("--findings", str(findings), "--contract", str(contract))
        assert result.returncode == 1
        assert "FAIL" in result.stdout

    @pytest.mark.unit
    def test_json_output_structured(self, tmp_path: Path) -> None:
        """Scenario: --format json emits machine-readable verdict."""
        findings = _write_findings(tmp_path, "## Summary\n\nNo evidence.\n")
        contract = _write_contract(
            tmp_path,
            {"required_sections": ["summary"], "min_evidence_count": 1},
        )
        result = _run_cli(
            "--findings",
            str(findings),
            "--contract",
            str(contract),
            "--format",
            "json",
        )
        payload = json.loads(result.stdout)
        assert payload["passed"] is False
        assert payload["evidence_count"] == 0

    @pytest.mark.unit
    def test_lenient_strictness_passes_warnings(self, tmp_path: Path) -> None:
        """Scenario: lenient strictness with one [E1] returns 0 + warnings."""
        findings = _write_findings(
            tmp_path,
            "## Summary\n\nSome content [E1].\n",
        )
        contract = _write_contract(
            tmp_path,
            {
                "required_sections": ["summary", "missing_section"],
                "min_evidence_count": 1,
                "strictness": "lenient",
            },
        )
        result = _run_cli("--findings", str(findings), "--contract", str(contract))
        assert result.returncode == 0
        assert "PASS" in result.stdout

    @pytest.mark.unit
    def test_missing_findings_file_returns_nonzero(self, tmp_path: Path) -> None:
        """Scenario: nonexistent findings file exits with code 2."""
        contract = _write_contract(tmp_path, {"required_sections": []})
        missing = tmp_path / "nonexistent.md"
        result = _run_cli("--findings", str(missing), "--contract", str(contract))
        assert result.returncode == 2
        assert "findings file not found" in result.stdout

    @pytest.mark.unit
    def test_missing_contract_file_returns_nonzero(self, tmp_path: Path) -> None:
        """Scenario: nonexistent contract file exits with code 2."""
        findings = _write_findings(tmp_path, "## Summary\n\nOk.\n")
        missing = tmp_path / "nonexistent.json"
        result = _run_cli("--findings", str(findings), "--contract", str(missing))
        assert result.returncode == 2
        assert "contract file not found" in result.stdout

    @pytest.mark.unit
    def test_yaml_contract_rejected(self, tmp_path: Path) -> None:
        """Scenario: YAML contract file causes SystemExit."""
        findings = _write_findings(tmp_path, "## Summary\n\nOk.\n")
        yaml_file = tmp_path / "contract.yaml"
        yaml_file.write_text("required_sections: []\n")
        result = _run_cli("--findings", str(findings), "--contract", str(yaml_file))
        assert result.returncode != 0
        assert "YAML" in result.stderr or "YAML" in result.stdout

    @pytest.mark.unit
    def test_text_format_shows_missing_sections_and_warnings(
        self, tmp_path: Path
    ) -> None:
        """Scenario: text output lists missing sections and warnings."""
        findings = _write_findings(tmp_path, "## Summary\n\nOne [E1].\n")
        contract = _write_contract(
            tmp_path,
            {
                "required_sections": ["summary", "missing_section"],
                "min_evidence_count": 1,
            },
        )
        result = _run_cli("--findings", str(findings), "--contract", str(contract))
        assert result.returncode == 1
        assert "Missing sections:" in result.stdout
        assert "missing_section" in result.stdout


class TestContractValidatorDirect:
    """Direct unit tests for CLI internals (coverage-tracked)."""

    @pytest.mark.unit
    def test_load_contract_wrapped_key(self, tmp_path: Path) -> None:
        """_load_contract unwraps output_contract: key."""
        from scripts.contract_validator import _load_contract

        contract_file = tmp_path / "contract.json"
        contract_file.write_text(
            json.dumps({"output_contract": {"required_sections": ["summary"]}})
        )
        contract = _load_contract(contract_file)
        assert "summary" in contract.required_sections

    @pytest.mark.unit
    def test_load_contract_yaml_rejection(self, tmp_path: Path) -> None:
        """_load_contract rejects .yaml/.yml files."""
        from scripts.contract_validator import _load_contract

        yaml_file = tmp_path / "contract.yaml"
        yaml_file.write_text("required_sections: []\n")
        with pytest.raises(SystemExit, match="YAML"):
            _load_contract(yaml_file)

    @pytest.mark.unit
    def test_format_text_fail_with_missing_and_warnings(self) -> None:
        """_format_text renders missing sections, artifacts, and warnings."""
        from scripts.contract_validator import (
            ContractValidationResult,
            _format_text,
        )

        result = ContractValidationResult(
            passed=False,
            evidence_count=0,
            missing_sections=["summary", "evidence"],
            missing_artifacts=["artifact_a"],
            warnings=["low evidence"],
            contract=None,
        )
        text = _format_text(result)
        assert "FAIL" in text
        assert "Missing sections:" in text
        assert "summary" in text
        assert "Missing artifacts:" in text
        assert "artifact_a" in text
        assert "Warnings:" in text
        assert "low evidence" in text
        assert "retry" in text.lower() or "Retry" in text

    @pytest.mark.unit
    def test_main_missing_findings(self, tmp_path: Path) -> None:
        """main() returns 2 when findings file missing."""
        from scripts.contract_validator import main

        contract_file = tmp_path / "contract.json"
        contract_file.write_text('{"required_sections": []}')
        import sys
        from unittest.mock import patch

        with patch.object(
            sys,
            "argv",
            ["cv", "--findings", "/no/such/file.md", "--contract", str(contract_file)],
        ):
            assert main() == 2

    @pytest.mark.unit
    def test_main_missing_contract(self, tmp_path: Path) -> None:
        """main() returns 2 when contract file missing."""
        from scripts.contract_validator import main

        findings_file = tmp_path / "findings.md"
        findings_file.write_text("## Summary\n\nOk.\n")
        import sys
        from unittest.mock import patch

        with patch.object(
            sys,
            "argv",
            [
                "cv",
                "--findings",
                str(findings_file),
                "--contract",
                "/no/such/contract.json",
            ],
        ):
            assert main() == 2
