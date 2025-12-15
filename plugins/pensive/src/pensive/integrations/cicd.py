"""CI/CD integrations for pensive."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class GitHubActionsIntegration:
    """Integration with GitHub Actions."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize GitHub Actions integration."""
        self.config = config or {}

    def setup(self) -> None:
        """Setup the integration."""

    def post_results(self, _results: dict[str, Any]) -> bool:
        """Post results to GitHub Actions."""
        return True

    def get_workflow_context(self) -> dict[str, Any]:
        """Get current workflow context."""
        return {}

    def detect_configuration(self, repo_path: Path | str) -> dict[str, Any] | None:
        """Detect CI/CD configuration in repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Configuration dict if found, None otherwise
        """
        repo_path = Path(repo_path)

        # Check for GitHub Actions workflows
        workflows_dir = repo_path / ".github" / "workflows"
        if workflows_dir.exists():
            workflow_files = list(workflows_dir.glob("*.yml")) + list(
                workflows_dir.glob("*.yaml")
            )
            if workflow_files:
                return {
                    "type": "github_actions",
                    "workflows": [f.name for f in workflow_files],
                    "path": str(workflows_dir),
                }

        # Check for other CI systems
        if (repo_path / ".gitlab-ci.yml").exists():
            return {"type": "gitlab_ci"}

        if (repo_path / ".travis.yml").exists():
            return {"type": "travis_ci"}

        if (repo_path / "Jenkinsfile").exists():
            return {"type": "jenkins"}

        return None

    def generate_sarif_output(
        self,
        repo_path: Path | str,
        findings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Generate SARIF output for GitHub Code Scanning.

        Args:
            repo_path: Path to the repository
            findings: Optional list of findings to include

        Returns:
            SARIF-formatted output dictionary
        """
        repo_path = Path(repo_path)
        findings = findings or []

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
                    "results": self._generate_results(findings, repo_path),
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "workingDirectory": {
                                "uri": f"file://{repo_path.absolute()}"
                            },
                        }
                    ],
                }
            ],
        }

        return sarif

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
                        "level": self._severity_to_sarif_level(
                            finding.get("severity", "medium")
                        )
                    },
                }

        return list(rules_map.values())

    def _generate_results(
        self,
        findings: list[dict[str, Any]],
        repo_path: Path,
    ) -> list[dict[str, Any]]:
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
                                "artifactLocation": {
                                    "uri": file_path,
                                    "uriBaseId": "%SRCROOT%",
                                },
                                "region": {
                                    "startLine": line_num,
                                },
                            }
                        }
                    ],
                    "level": self._severity_to_sarif_level(
                        finding.get("severity", "medium")
                    ),
                }
            )

        return results

    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note",
        }
        return mapping.get(severity.lower(), "warning")

    def generate_workflow_file(self) -> str:
        """Generate a GitHub Actions workflow file for pensive.

        Returns:
            YAML content for the workflow file
        """
        return """name: Pensive Code Review
on: [pull_request]

jobs:
  pensive-review:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install pensive
      run: pip install pensive
    - name: Run Pensive Review
      run: pensive review --format sarif --output review.sarif
    - name: Upload SARIF
      uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: review.sarif
"""
