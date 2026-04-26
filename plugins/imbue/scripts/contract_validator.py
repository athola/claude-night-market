#!/usr/bin/env python3
"""Validate agent findings against output contracts.

An output contract specifies what an agent must produce:
required sections, minimum evidence count, expected artifacts.
The validator checks compliance and generates retry feedback
for failed validations.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

# Pattern matching [E1], [E2], etc.
EVIDENCE_TAG_PATTERN = re.compile(r"\[E\d+\]")

# Pattern matching ## or ### headings
HEADING_PATTERN = re.compile(r"^#{2,3}\s+(.+)$", re.MULTILINE)

# YAML frontmatter delimiter
FRONTMATTER_DELIMITER = "---"


@dataclass
class OutputContract:
    """Defines what an agent must produce."""

    required_sections: list[str]
    min_evidence_count: int
    expected_artifacts: list[str] = field(default_factory=list)
    retry_budget: int = 2
    strictness: str = "normal"  # strict | normal | lenient

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OutputContract:
        """Create a contract from a dictionary."""
        return cls(
            required_sections=data["required_sections"],
            min_evidence_count=data.get("min_evidence_count", 0),
            expected_artifacts=data.get("expected_artifacts", []),
            retry_budget=data.get("retry_budget", 2),
            strictness=data.get("strictness", "normal"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)


@dataclass
class ContractValidationResult:
    """Result of validating findings against a contract."""

    passed: bool
    evidence_count: int
    missing_sections: list[str] = field(default_factory=list)
    missing_artifacts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    contract: OutputContract | None = None

    def retry_feedback(self) -> str:
        """Generate specific feedback for a failed validation.

        Lists every missing element so the agent knows exactly
        what to fix on retry.
        """
        parts: list[str] = []
        parts.append("## Contract Validation FAILED\n")
        parts.append("Your output did not meet the required contract.")
        parts.append("Fix the following issues:\n")

        if self.missing_sections:
            parts.append("### Missing Sections\n")
            parts.append(
                "Your findings must include these sections as ## or ### headings:\n"
            )
            for section in self.missing_sections:
                parts.append(f"- {section}")
            parts.append("")

        if self.contract and self.evidence_count < self.contract.min_evidence_count:
            parts.append("### Insufficient Evidence\n")
            parts.append(
                f"Found {self.evidence_count} evidence citations "
                f"([E1], [E2], etc.) but the contract requires "
                f"at least {self.contract.min_evidence_count}.\n"
            )
            parts.append(
                "Add more [EN] evidence tags with actual command "
                "outputs or file references.\n"
            )

        if self.missing_artifacts:
            parts.append("### Missing Artifacts\n")
            parts.append("These files must exist after your work:\n")
            for artifact in self.missing_artifacts:
                parts.append(f"- {artifact}")
            parts.append("")

        parts.append("Retry the dispatch after addressing all issues above.")
        return "\n".join(parts)


def _normalize_section_name(name: str) -> str:
    """Normalize a section name for comparison.

    Lowercases and replaces underscores with spaces so that
    'detailed_findings' matches 'Detailed Findings'.
    """
    return name.lower().strip().replace("_", " ")


def _extract_sections(text: str) -> list[str]:
    """Extract all ## and ### heading names from Markdown text."""
    return [
        _normalize_section_name(match.group(1))
        for match in HEADING_PATTERN.finditer(text)
    ]


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter from Markdown text."""
    stripped = text.strip()
    if not stripped.startswith(FRONTMATTER_DELIMITER):
        return text

    # Find the closing ---
    rest = stripped[len(FRONTMATTER_DELIMITER) :]
    end_idx = rest.find(FRONTMATTER_DELIMITER)
    if end_idx == -1:
        return text

    return rest[end_idx + len(FRONTMATTER_DELIMITER) :].strip()


def _count_evidence_tags(text: str) -> int:
    """Count unique [EN] evidence tags in the text."""
    return len(EVIDENCE_TAG_PATTERN.findall(text))


def _check_sections(
    contract: OutputContract,
    found_sections: list[str],
) -> tuple[list[str], list[str], bool]:
    """Check required sections are present. Returns (missing, warnings, failed)."""
    missing = [
        req
        for req in contract.required_sections
        if _normalize_section_name(req) not in found_sections
    ]
    if not missing:
        return [], [], False
    if contract.strictness in {"strict", "normal"}:
        return missing, [], True
    return missing, [f"Missing section: {s}" for s in missing], False


def _check_evidence(
    contract: OutputContract,
    evidence_count: int,
) -> tuple[list[str], bool]:
    """Check evidence count meets minimum. Returns (warnings, failed)."""
    if evidence_count >= contract.min_evidence_count:
        return [], False
    if contract.strictness in {"strict", "normal"}:
        return [], True
    return [
        f"Evidence count ({evidence_count}) below minimum "
        f"({contract.min_evidence_count})"
    ], False


def _check_artifacts(
    contract: OutputContract,
) -> tuple[list[str], list[str], bool]:
    """Check expected artifacts exist. Returns (missing, warnings, failed)."""
    missing = [p for p in contract.expected_artifacts if not Path(p).exists()]
    if not missing:
        return [], [], False
    if contract.strictness != "lenient":
        return missing, [], True
    return missing, [f"Missing artifact: {a}" for a in missing], False


def validate_findings(
    findings_text: str,
    contract: OutputContract,
) -> ContractValidationResult:
    """Validate agent findings against an output contract.

    Checks in order:
    1. Zero-evidence gate (unconditional reject)
    2. Section presence check
    3. Evidence count check
    4. Artifact existence check

    Args:
        findings_text: Raw Markdown text of the agent's findings.
        contract: The output contract to validate against.

    Returns:
        ContractValidationResult with pass/fail status and detail.

    """
    body = _strip_frontmatter(findings_text)
    evidence_count = _count_evidence_tags(body)
    found_sections = _extract_sections(body)
    warnings: list[str] = []
    failed = False

    # Rule 1: Zero-evidence gate (always reject)
    if evidence_count == 0:
        failed = True

    # Rule 2: Section check
    missing_sections, section_warnings, section_failed = _check_sections(
        contract, found_sections
    )
    warnings.extend(section_warnings)
    failed = failed or section_failed

    # Rule 3: Evidence count check
    evidence_warnings, evidence_failed = _check_evidence(contract, evidence_count)
    warnings.extend(evidence_warnings)
    failed = failed or evidence_failed

    # Rule 4: Artifact check
    missing_artifacts, artifact_warnings, artifact_failed = _check_artifacts(contract)
    warnings.extend(artifact_warnings)
    failed = failed or artifact_failed

    return ContractValidationResult(
        passed=not failed,
        evidence_count=evidence_count,
        missing_sections=missing_sections,
        missing_artifacts=missing_artifacts,
        warnings=warnings,
        contract=contract,
    )


def _load_contract(contract_path: Path) -> OutputContract:
    """Load a contract from a JSON file.

    YAML support is deferred to a follow-up; convert with
    ``yq -o=json contract.yaml > contract.json`` if needed.
    """
    if contract_path.suffix in {".yaml", ".yml"}:
        raise SystemExit(
            "YAML contracts not yet supported by the CLI; "
            "convert to JSON via 'yq -o=json' first."
        )
    data = json.loads(contract_path.read_text())
    # Allow contracts wrapped under output_contract: key
    if isinstance(data, dict) and "output_contract" in data:
        data = data["output_contract"]
    return OutputContract.from_dict(data)


def _format_text(result: ContractValidationResult) -> str:
    """Render a result as a human-readable verdict block."""
    verdict = "PASS" if result.passed else "FAIL"
    lines = [f"Contract validation: {verdict}"]
    lines.append(f"  Evidence count: {result.evidence_count}")
    if result.missing_sections:
        lines.append("  Missing sections:")
        for s in result.missing_sections:
            lines.append(f"    - {s}")
    if result.missing_artifacts:
        lines.append("  Missing artifacts:")
        for a in result.missing_artifacts:
            lines.append(f"    - {a}")
    if result.warnings:
        lines.append("  Warnings:")
        for w in result.warnings:
            lines.append(f"    - {w}")
    if not result.passed:
        lines.append("")
        lines.append(result.retry_feedback())
    return "\n".join(lines)


def main() -> int:
    """CLI entry point: validate a findings file against a contract."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--findings", type=Path, required=True, help="Path to agent findings .md file"
    )
    parser.add_argument(
        "--contract",
        type=Path,
        required=True,
        help="Path to contract JSON or YAML file",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if not args.findings.exists():
        print(f"ERROR: findings file not found: {args.findings}")
        return 2
    if not args.contract.exists():
        print(f"ERROR: contract file not found: {args.contract}")
        return 2

    contract = _load_contract(args.contract)
    findings_text = args.findings.read_text()
    result = validate_findings(findings_text, contract)

    if args.format == "json":
        # Convert dataclass to plain dict; contract field needs special handling.
        payload = {
            "passed": result.passed,
            "evidence_count": result.evidence_count,
            "missing_sections": result.missing_sections,
            "missing_artifacts": result.missing_artifacts,
            "warnings": result.warnings,
            "contract": result.contract.to_dict() if result.contract else None,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(_format_text(result))

    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
