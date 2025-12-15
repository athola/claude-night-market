"""Report formatters for pensive."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


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
        critical = sum(1 for f in findings if f.get("severity") == "critical")
        high = sum(1 for f in findings if f.get("severity") == "high")
        medium = sum(1 for f in findings if f.get("severity") == "medium")
        low = sum(1 for f in findings if f.get("severity") == "low")

        lines.append("## Summary")
        lines.append("")
        lines.append(
            f"Found **{len(findings)}** issues: "
            f"{critical} critical, {high} high, {medium} medium, {low} low"
        )
        lines.append("")

        # Group by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_findings = [f for f in findings if f.get("severity") == severity]
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
            repo_path: Optional repository path for context

        Returns:
            SARIF JSON string
        """
        import json

        sarif = {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "pensive",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/pensive/pensive",
                            "rules": self._generate_rules(findings),
                        }
                    },
                    "results": self._generate_results(findings),
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
                    "name": finding.get("title", "Unknown Issue"),
                    "shortDescription": {
                        "text": finding.get("issue", "No description")
                    },
                    "defaultConfiguration": {
                        "level": self._severity_to_level(
                            finding.get("severity", "medium")
                        )
                    },
                }

        return list(rules_map.values())

    def _generate_results(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate SARIF results from findings."""
        results = []

        for finding in findings:
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

            results.append(
                {
                    "ruleId": finding.get("id", "UNKNOWN"),
                    "message": {"text": finding.get("issue", "No description")},
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
        return mapping.get(severity.lower(), "warning")

    def to_json(self, results: dict[str, Any]) -> str:
        """Format results as SARIF JSON string (legacy method)."""
        import json

        return json.dumps(results)
