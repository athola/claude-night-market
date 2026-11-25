"""Report formatters for pensive."""

from __future__ import annotations

import json
from importlib import metadata
from pathlib import Path
from typing import Any

from pensive import __version__
from pensive.utils.severity_mapper import count_by_severity, normalize_severity


def _tool_version() -> str:
    """Report the installed pensive version in SARIF output."""
    try:
        return metadata.version("pensive")
    except metadata.PackageNotFoundError:
        return __version__


class MarkdownFormatter:
    """Format results as Markdown."""

    def format(
        self,
        findings: list[dict[str, Any]],
        repo_path: Path | str | None = None,
    ) -> str:
        """Format findings as Markdown string.

        Args:
            findings: List of finding dictionaries
            repo_path: Optional repository path for context

        Returns:
            Markdown-formatted string
        """
        if not findings:
            return "# Code Review Results\n\nNo findings."

        lines = ["# Code Review Results", ""]

        # Summary
        counts = count_by_severity(findings)
        critical = counts["critical"]
        high = counts["high"]
        medium = counts["medium"]
        low = counts["low"]

        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"Found **{len(findings)}** issues: "
            f"{critical} critical, {high} high, {medium} medium, {low} low"
        )
        lines.append("")

        # Group by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_findings = [
                f
                for f in findings
                if normalize_severity(f.get("severity", "low")) == severity
            ]
            if severity_findings:
                lines.append(f"## {severity.capitalize()} Priority")
                lines.append("")
                for finding in severity_findings:
                    self._format_finding(finding, lines)
                lines.append("")

        return "\n".join(lines)

    def _format_finding(self, finding: dict[str, Any], lines: list[str]) -> None:
        """Format a single finding."""
        finding_id = finding.get("id", "UNKNOWN")
        title = finding.get("title", "Untitled")
        location = finding.get("location", "Unknown")
        issue = finding.get("issue", "No description")
        fix = finding.get("fix", "")

        lines.append(f"### [{finding_id}] {title}")
        lines.append("")
        lines.append(f"**Location:** `{location}`")
        lines.append("")
        lines.append(f"**Issue:** {issue}")
        if fix:
            lines.append("")
            lines.append(f"**Fix:** {fix}")
        lines.append("")

    def format_findings(self, findings: list[dict[str, Any]]) -> str:
        """Format a list of findings (legacy method)."""
        return self.format(findings)


class SarifFormatter:
    """Format results as SARIF."""

    def format(
        self,
        findings: list[dict[str, Any]],
        repo_path: Path | str | None = None,
    ) -> str:
        """Format findings as SARIF JSON string.

        Args:
            findings: List of finding dictionaries
            repo_path: Repository root; file paths under it are written
                relative to it, which is how code scanning matches a
                result to a file

        Returns:
            SARIF JSON string
        """
        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "pensive",
                            "version": _tool_version(),
                            "informationUri": "https://github.com/athola/claude-night-market",
                            "rules": self._generate_rules(findings),
                        }
                    },
                    "results": self._generate_results(findings, repo_path),
                }
            ],
        }

        return json.dumps(sarif, indent=2)

    def _generate_rules(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate SARIF rules from findings."""
        rules_map: dict[str, dict[str, Any]] = {}

        for finding in findings:
            rule_id = finding.get("id", "UNKNOWN")
            if rule_id not in rules_map:
                rules_map[rule_id] = {
                    "id": rule_id,
                    "name": finding.get("title") or rule_id,
                    "shortDescription": {
                        "text": finding.get("issue")
                        or finding.get("detection_signal", "No description")
                    },
                    "defaultConfiguration": {
                        "level": self._severity_to_level(
                            finding.get("severity", "medium")
                        )
                    },
                }

        return list(rules_map.values())

    def _generate_results(
        self,
        findings: list[dict[str, Any]],
        repo_path: Path | str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate SARIF results from findings."""
        results = []
        root = Path(repo_path).resolve() if repo_path is not None else None

        for finding in findings:
            # harden findings name the file and line separately.
            if "file" in finding:
                location = f"{finding['file']}:{finding.get('line', 1)}"
            else:
                location = finding.get("location", "unknown:1")
            if ":" in location:
                file_path, line = location.rsplit(":", 1)
                try:
                    line_num = int(line)
                except ValueError:
                    line_num = 1
            else:
                file_path = location
                line_num = 1
            if root is not None and Path(file_path).is_absolute():
                resolved = Path(file_path).resolve()
                if resolved.is_relative_to(root):
                    file_path = resolved.relative_to(root).as_posix()

            results.append(
                {
                    "ruleId": finding.get("id", "UNKNOWN"),
                    "message": {
                        "text": finding.get("issue")
                        or finding.get("detection_signal", "No description")
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": file_path},
                                "region": {"startLine": line_num},
                            }
                        }
                    ],
                    "level": self._severity_to_level(finding.get("severity", "medium")),
                }
            )

        return results

    def _severity_to_level(self, severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
        }
        return mapping.get(str(severity).lower(), "warning")
