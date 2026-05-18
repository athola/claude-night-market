"""Finding / Severity / Citation types for the harden detector pipeline.

These types pin the contract documented in
``plugins/pensive/skills/harden/modules/proposal-shape.md``: every
finding above ADVISORY must carry a primary CWE plus a NIST SSDF
practice. The constructor enforces this so the report cannot ship
uncited high-severity findings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "ADVISORY"]


@dataclass(frozen=True)
class Citation:
    """Citation backbone for a Finding.

    cwe is a primary CWE reference (e.g., "CWE-502"). nist_ssdf is a
    NIST SP 800-218 SSDF practice clause (e.g., "PW.7"). Extra holds
    optional secondary citations (OWASP ASVS, RustSec, PEP, CVE).
    """

    cwe: str
    nist_ssdf: str
    extra: tuple[str, ...] = ()

    def __str__(self) -> str:
        parts = [self.cwe, f"NIST SSDF {self.nist_ssdf}"]
        parts.extend(self.extra)
        return ", ".join(parts)


@dataclass(frozen=True)
class Finding:
    """One detector finding emitted by the harden scanner.

    Every finding above ADVISORY severity MUST carry a citation. A
    finding without a CWE/NIST citation is downgraded to ADVISORY at
    construction (raising ValueError) so the report's findings table
    cannot include uncited high-severity entries.
    """

    id: str
    severity: Severity
    citation: Citation | None
    file: str
    line: int
    detection_signal: str
    proposal: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.severity != "ADVISORY" and self.citation is None:
            raise ValueError(
                f"Finding {self.id} has severity {self.severity} but no "
                "citation; only ADVISORY findings may omit a CWE/NIST "
                "citation. Provide a citation or downgrade to ADVISORY."
            )

    def to_dict(self) -> dict[str, object]:
        d: dict[str, object] = {
            "id": self.id,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "detection_signal": self.detection_signal,
            "proposal": self.proposal,
        }
        if self.citation is not None:
            d["citation"] = {
                "cwe": self.citation.cwe,
                "nist_ssdf": self.citation.nist_ssdf,
                "extra": list(self.citation.extra),
                "rendered": str(self.citation),
            }
        else:
            d["citation"] = None
        if self.extra:
            d["extra"] = dict(self.extra)
        return d
