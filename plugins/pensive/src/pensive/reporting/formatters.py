"""Report formatters for pensive."""

from __future__ import annotations

from typing import Any


class MarkdownFormatter:
    """Format results as Markdown."""

    def format(self, results: dict[str, Any]) -> str:
        """Format results as Markdown string."""
        return "# Results\n\nNo findings."

    def format_findings(self, findings: list[dict[str, Any]]) -> str:
        """Format a list of findings."""
        if not findings:
            return "No findings."
        lines = ["# Findings", ""]
        for finding in findings:
            lines.append(f"- {finding.get('message', 'Unknown')}")
        return "\n".join(lines)


class SarifFormatter:
    """Format results as SARIF."""

    def format(self, results: dict[str, Any]) -> dict[str, Any]:
        """Format results as SARIF dict."""
        return {
            "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
            "version": "2.1.0",
            "runs": [],
        }

    def to_json(self, results: dict[str, Any]) -> str:
        """Format results as SARIF JSON string."""
        import json

        return json.dumps(self.format(results))
