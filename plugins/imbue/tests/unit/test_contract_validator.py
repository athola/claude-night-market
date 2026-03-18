"""Tests for the output contract validator.

Validates agent findings against output contracts.
Covers PASS, FAIL (missing sections), FAIL (low evidence),
FAIL (zero evidence), and retry feedback generation.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from scripts.contract_validator import (
    OutputContract,
    validate_findings,
)

# --------------- fixtures ---------------


@pytest.fixture()
def sample_contract() -> OutputContract:
    """A standard code-review output contract."""
    return OutputContract(
        required_sections=["summary", "detailed findings", "evidence"],
        min_evidence_count=3,
        expected_artifacts=[],
        retry_budget=2,
        strictness="normal",
    )


@pytest.fixture()
def strict_contract() -> OutputContract:
    """A strict audit contract with artifacts."""
    return OutputContract(
        required_sections=[
            "summary",
            "scope analyzed",
            "findings by severity",
            "recommendations",
            "evidence",
        ],
        min_evidence_count=8,
        expected_artifacts=["auditor.findings.md"],
        retry_budget=1,
        strictness="strict",
    )


@pytest.fixture()
def lenient_contract() -> OutputContract:
    """A lenient research contract."""
    return OutputContract(
        required_sections=["summary", "key findings"],
        min_evidence_count=1,
        expected_artifacts=[],
        retry_budget=2,
        strictness="lenient",
    )


@pytest.fixture()
def passing_findings() -> str:
    """Findings that should pass the sample_contract."""
    return textwrap.dedent("""\
        ---
        agent: reviewer
        area: plugins/imbue
        tier: 1
        evidence_count: 4
        ---

        ## Summary

        Found 2 issues in the imbue plugin validation logic.

        ## Detailed Findings

        ### Issue 1: Missing null check

        The validator does not check for empty input.

        [E1] Command: grep -n "def validate" scripts/imbue_validator.py
             Output: 42: def validate(self, data):

        [E2] Command: python -c "from scripts.imbue_validator import ..."
             Output: TypeError: NoneType has no attribute 'get'

        ### Issue 2: Inconsistent error format

        Error messages use different formats across methods.

        [E3] Command: grep -n "logger.error" scripts/imbue_validator.py
             Output: 3 occurrences with different format strings

        ## Evidence

        [E4] Command: cd plugins/imbue && uv run pytest tests/ -v --tb=short
             Output: 12 passed, 0 failed
    """)


@pytest.fixture()
def missing_section_findings() -> str:
    """Findings missing the 'evidence' section."""
    return textwrap.dedent("""\
        ---
        agent: reviewer
        ---

        ## Summary

        Quick review, looks fine.

        ## Detailed Findings

        No significant issues found.

        [E1] Command: grep -rn "TODO" src/
             Output: 2 results
    """)


@pytest.fixture()
def zero_evidence_findings() -> str:
    """Findings with no evidence citations at all."""
    return textwrap.dedent("""\
        ---
        agent: reviewer
        ---

        ## Summary

        Everything looks good.

        ## Detailed Findings

        No issues found.

        ## Evidence

        None needed.
    """)


@pytest.fixture()
def low_evidence_findings() -> str:
    """Findings with fewer evidence citations than required."""
    return textwrap.dedent("""\
        ---
        agent: reviewer
        ---

        ## Summary

        One minor issue found.

        ## Detailed Findings

        Some variable naming inconsistency.

        [E1] Command: grep -n "var_name" src/
             Output: mixed naming styles

        ## Evidence

        See above.
    """)


# --------------- PASS tests ---------------


class TestContractValidationPass:
    """Tests for findings that should pass validation."""

    def test_passing_findings(
        self,
        sample_contract: OutputContract,
        passing_findings: str,
    ) -> None:
        result = validate_findings(passing_findings, sample_contract)
        assert result.passed is True
        assert result.missing_sections == []
        assert result.evidence_count >= sample_contract.min_evidence_count

    def test_extra_sections_still_pass(
        self,
        sample_contract: OutputContract,
        passing_findings: str,
    ) -> None:
        """Extra sections beyond required should not cause failure."""
        findings_with_extra = passing_findings + "\n## Appendix\n\nExtra info.\n"
        result = validate_findings(findings_with_extra, sample_contract)
        assert result.passed is True

    def test_case_insensitive_sections(
        self,
        sample_contract: OutputContract,
    ) -> None:
        """Section matching should be case-insensitive."""
        findings = textwrap.dedent("""\
            ## SUMMARY
            Overview here.

            ## DETAILED FINDINGS
            Details here.
            [E1] cmd: test1
            [E2] cmd: test2
            [E3] cmd: test3

            ## EVIDENCE
            See above.
        """)
        result = validate_findings(findings, sample_contract)
        assert result.passed is True

    def test_underscore_treated_as_space(
        self,
        sample_contract: OutputContract,
    ) -> None:
        """'detailed_findings' in contract matches 'Detailed Findings'."""
        contract = OutputContract(
            required_sections=["summary", "detailed_findings", "evidence"],
            min_evidence_count=1,
            expected_artifacts=[],
            retry_budget=2,
            strictness="normal",
        )
        findings = textwrap.dedent("""\
            ## Summary
            Overview.

            ## Detailed Findings
            Details.
            [E1] cmd: test

            ## Evidence
            See above.
        """)
        result = validate_findings(findings, contract)
        assert result.passed is True


# --------------- FAIL tests ---------------


class TestContractValidationFail:
    """Tests for findings that should fail validation."""

    def test_missing_section(
        self,
        sample_contract: OutputContract,
        missing_section_findings: str,
    ) -> None:
        result = validate_findings(missing_section_findings, sample_contract)
        assert result.passed is False
        assert "evidence" in [s.lower() for s in result.missing_sections]

    def test_zero_evidence_always_rejected(
        self,
        sample_contract: OutputContract,
        zero_evidence_findings: str,
    ) -> None:
        """Zero evidence is unconditionally rejected."""
        result = validate_findings(zero_evidence_findings, sample_contract)
        assert result.passed is False
        assert result.evidence_count == 0

    def test_zero_evidence_rejected_even_lenient(
        self,
        lenient_contract: OutputContract,
        zero_evidence_findings: str,
    ) -> None:
        """Zero evidence is rejected even with lenient strictness."""
        result = validate_findings(zero_evidence_findings, lenient_contract)
        assert result.passed is False

    def test_low_evidence_rejected_normal(
        self,
        sample_contract: OutputContract,
        low_evidence_findings: str,
    ) -> None:
        """Evidence count below minimum is rejected in normal mode."""
        result = validate_findings(low_evidence_findings, sample_contract)
        assert result.passed is False
        assert result.evidence_count < sample_contract.min_evidence_count

    def test_low_evidence_warns_lenient(
        self,
        lenient_contract: OutputContract,
        low_evidence_findings: str,
    ) -> None:
        """Lenient mode passes with low evidence but adds warnings."""
        result = validate_findings(low_evidence_findings, lenient_contract)
        # Lenient: min is 1, findings have 1 → should pass
        assert result.passed is True

    def test_missing_artifact(self, tmp_path: Path) -> None:
        """Missing expected artifact causes failure."""
        contract = OutputContract(
            required_sections=["summary"],
            min_evidence_count=1,
            expected_artifacts=[str(tmp_path / "nonexistent.md")],
            retry_budget=1,
            strictness="normal",
        )
        findings = textwrap.dedent("""\
            ## Summary
            Done.
            [E1] cmd: test
        """)
        result = validate_findings(findings, contract)
        assert result.passed is False
        assert len(result.missing_artifacts) > 0

    def test_present_artifact_passes(self, tmp_path: Path) -> None:
        """Present expected artifact does not cause failure."""
        artifact = tmp_path / "output.md"
        artifact.write_text("findings here")
        contract = OutputContract(
            required_sections=["summary"],
            min_evidence_count=1,
            expected_artifacts=[str(artifact)],
            retry_budget=1,
            strictness="normal",
        )
        findings = textwrap.dedent("""\
            ## Summary
            Done.
            [E1] cmd: test
        """)
        result = validate_findings(findings, contract)
        assert result.passed is True


# --------------- edge case tests ---------------


class TestContractEdgeCases:
    """Tests for defensive branches and unusual inputs."""

    def test_malformed_frontmatter_no_closing_delimiter(
        self,
        sample_contract: OutputContract,
    ) -> None:
        """Frontmatter that opens with --- but never closes is kept intact."""
        findings = textwrap.dedent("""\
            ---
            agent: reviewer
            this frontmatter never closes

            ## Summary
            Overview.

            ## Detailed Findings
            Details.
            [E1] cmd: test1
            [E2] cmd: test2
            [E3] cmd: test3

            ## Evidence
            See above.
        """)
        result = validate_findings(findings, sample_contract)
        assert result.passed is True

    def test_lenient_missing_artifact_warns_but_passes(
        self,
        tmp_path: Path,
    ) -> None:
        """Lenient mode warns about missing artifacts instead of failing."""
        contract = OutputContract(
            required_sections=["summary"],
            min_evidence_count=1,
            expected_artifacts=[str(tmp_path / "optional.md")],
            retry_budget=1,
            strictness="lenient",
        )
        findings = textwrap.dedent("""\
            ## Summary
            Done.
            [E1] cmd: test
        """)
        result = validate_findings(findings, contract)
        assert result.passed is True
        assert any("optional.md" in w for w in result.warnings)


# --------------- feedback tests ---------------


class TestRetryFeedback:
    """Tests for retry feedback message generation."""

    def test_feedback_lists_missing_sections(
        self,
        sample_contract: OutputContract,
        missing_section_findings: str,
    ) -> None:
        result = validate_findings(missing_section_findings, sample_contract)
        assert result.passed is False
        feedback = result.retry_feedback()
        assert "evidence" in feedback.lower()

    def test_feedback_states_evidence_gap(
        self,
        sample_contract: OutputContract,
        low_evidence_findings: str,
    ) -> None:
        result = validate_findings(low_evidence_findings, sample_contract)
        assert result.passed is False
        feedback = result.retry_feedback()
        assert "evidence" in feedback.lower()
        # Should mention how many are needed
        assert str(sample_contract.min_evidence_count) in feedback

    def test_feedback_lists_missing_artifacts(self, tmp_path: Path) -> None:
        contract = OutputContract(
            required_sections=["summary"],
            min_evidence_count=1,
            expected_artifacts=[str(tmp_path / "missing.md")],
            retry_budget=1,
            strictness="normal",
        )
        findings = "## Summary\nDone.\n[E1] cmd: test\n"
        result = validate_findings(findings, contract)
        feedback = result.retry_feedback()
        assert "missing.md" in feedback


# --------------- serialization tests ---------------


class TestContractSerialization:
    """Tests for contract YAML/dict parsing."""

    def test_from_dict(self) -> None:
        data = {
            "required_sections": ["summary", "evidence"],
            "min_evidence_count": 2,
            "expected_artifacts": [],
            "retry_budget": 1,
            "strictness": "strict",
        }
        contract = OutputContract.from_dict(data)
        assert contract.required_sections == ["summary", "evidence"]
        assert contract.min_evidence_count == 2
        assert contract.strictness == "strict"

    def test_from_dict_defaults(self) -> None:
        """Missing optional fields get defaults."""
        data = {
            "required_sections": ["summary"],
            "min_evidence_count": 1,
        }
        contract = OutputContract.from_dict(data)
        assert contract.expected_artifacts == []
        assert contract.retry_budget == 2
        assert contract.strictness == "normal"

    def test_to_dict_roundtrip(self) -> None:
        original = OutputContract(
            required_sections=["a", "b"],
            min_evidence_count=5,
            expected_artifacts=["x.md"],
            retry_budget=3,
            strictness="strict",
        )
        data = original.to_dict()
        restored = OutputContract.from_dict(data)
        assert restored.required_sections == original.required_sections
        assert restored.min_evidence_count == original.min_evidence_count
        assert restored.strictness == original.strictness
