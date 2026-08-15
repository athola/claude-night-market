"""Contract tests for the harden Finding/Severity/Citation types.

Feature: harden detector findings carry mandatory fields.

As a /harden invocation
I want every emitted finding to carry severity, citation, file, line,
detection signal, and either a remediation proposal or an explicit
ADVISORY status
So that the report cannot ship uncited or empty findings, and the
proposal-shape contract from modules/proposal-shape.md is enforced
in code, not just in docs.
"""

from __future__ import annotations

import typing

import pytest

from pensive.harden.types import Citation, Finding, Severity


class TestFindingContract:
    def test_finding_dataclass_importable(self) -> None:
        assert Finding.__name__ == "Finding"

    def test_severity_literal_matches_skill_md(self) -> None:
        """Severity must match the SKILL.md classification:
        CRITICAL / HIGH / MEDIUM / LOW / ADVISORY.
        """
        args = typing.get_args(Severity)
        assert set(args) == {"CRITICAL", "HIGH", "MEDIUM", "LOW", "ADVISORY"}

    def test_finding_requires_citation(self) -> None:
        """A Finding without a primary CWE is downgraded to ADVISORY."""
        # No-citation finding cannot exceed ADVISORY (constructor enforces it)
        with pytest.raises(ValueError, match="citation"):
            Finding(
                id="X1",
                severity="HIGH",
                citation=None,
                file="a.py",
                line=1,
                detection_signal="x",
                proposal=None,
            )

        # ADVISORY without citation is allowed (informational)
        f = Finding(
            id="X2",
            severity="ADVISORY",
            citation=None,
            file="a.py",
            line=1,
            detection_signal="x",
            proposal=None,
        )
        assert f.severity == "ADVISORY"

        # Citation present + above-advisory severity is allowed
        f2 = Finding(
            id="X3",
            severity="MEDIUM",
            citation=Citation(cwe="CWE-502", nist_ssdf="PW.7"),
            file="a.py",
            line=1,
            detection_signal="x",
            proposal=None,
        )
        assert f2.severity == "MEDIUM"

    def test_citation_renders_human_readable(self) -> None:
        c = Citation(
            cwe="CWE-502",
            nist_ssdf="PW.7",
            extra=("OWASP ASVS V5.5",),
        )
        rendered = str(c)
        assert "CWE-502" in rendered
        assert "PW.7" in rendered
        assert "ASVS V5.5" in rendered
