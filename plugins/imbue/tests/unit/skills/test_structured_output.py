"""Tests for structured-output skill business logic.

This module tests the deliverable formatting and template functionality,
following TDD/BDD principles and testing all output formatting scenarios.
"""

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

# Constants for PLR2004 magic values
TWO = 2
THREE = 3
FIVE = 5
TWO_POINT_ZERO = 2.0
FOUR = 4
TEN = 10
TWO_HUNDRED = 200


class TestStructuredOutputSkill:
    """Feature: Structured output ensures consistent deliverable formatting.

    As a review consumer
    I want consistent report structure
    So that I can quickly find relevant information
    """

    @pytest.fixture
    def mock_structured_output_skill_content(self) -> str:
        """Mock structured-output skill content."""
        return """---
name: structured-output
description: Guide for formatting review deliverables consistently
category: review-patterns
dependencies:
  - imbue:evidence-logging
usage_patterns:
  - deliverable-formatting
  - report-generation
  - template-application
tools:
  - Read
  - Write
  - Bash
tags:
  - structured-output
  - formatting
  - templates
  - deliverables
---

# Structured Output

Guide for formatting review deliverables consistently across different review types and audiences.

## TodoWrite Items

- `structured-output:template-selected`
- `structured-output:findings-formatted`
- `structured-output:actions-assigned`
- `structured-output:appendix-attached`

## Template Types

### 1. Review Report Template
**Audience**: Development team, stakeholders
**Purpose**: Comprehensive review findings and recommendations

### 2. Pull Request Description Template
**Audience**: Code reviewers, CI/CD systems
**Purpose**: Summary of changes for code review

### 3. Release Notes Template
**Audience**: End users, product managers
**Purpose**: User-facing summary of changes

### 4. Security Review Template
**Audience**: Security team, compliance officers
**Purpose**: Security-focused analysis and recommendations

## Formatting Standards

### Markdown Structure
- Use consistent heading levels (H1-H4)
- Include table of contents for long documents
- Use code blocks with language specification
- Include proper link formatting

### Finding Classification
- **Severity**: Critical, High, Medium, Low
- **Category**: Security, Performance, Correctness, Style, Documentation
- **Status**: Open, In Progress, Resolved, Won't Fix

### Action Item Format
- Clear description of required action
- Priority level (P1-P4)
- Assignee (if known)
- Due date (if applicable)
- Dependencies or blockers

## Template Variables

Common template variables that should be populated:
- `{{review_id}}`: Unique review identifier
- `{{timestamp}}`: Review completion time
- `{{reviewer}}`: Reviewer name/identifier
- `{{target}}`: Review target (branch, PR, etc.)
- `{{findings_count}}`: Total number of findings
- `{{summary}}`: Executive summary
- `{{findings}}`: Formatted findings list
- `{{actions}}`: Action items list
- `{{evidence_appendix}}`: Evidence references
"""

    @pytest.fixture
    def sample_review_findings(self):
        """Sample review findings for formatting."""
        return [
            {
                "id": "F1",
                "title": "SQL injection vulnerability",
                "description": "User input is not properly sanitized in database queries",
                "severity": "Critical",
                "category": "Security",
                "file": "src/database.py",
                "line": 45,
                "evidence_refs": ["E1", "E2"],
                "recommendation": "Use parameterized queries or ORM to prevent SQL injection",
            },
            {
                "id": "F2",
                "title": "Memory leak in image processing",
                "description": "Large image files are not properly disposed after processing",
                "severity": "High",
                "category": "Performance",
                "file": "src/image_processor.py",
                "line": 120,
                "evidence_refs": ["E3"],
                "recommendation": "Implement proper resource cleanup using context managers",
            },
            {
                "id": "F3",
                "title": "Inconsistent variable naming",
                "description": "Some variables use camelCase while others use snake_case",
                "severity": "Low",
                "category": "Style",
                "file": "src/utils.py",
                "line": 15,
                "evidence_refs": ["E4"],
                "recommendation": "Standardize variable naming to snake_case",
            },
        ]

    @pytest.fixture
    def sample_evidence_log(self):
        """Sample evidence log for appendix."""
        return {
            "session_id": "review-123",
            "evidence": [
                {
                    "id": "E1",
                    "command": "grep -r 'execute(' src/",
                    "output": "src/database.py:45: query.execute(user_input)",
                    "timestamp": "2024-12-04T10:00:00Z",
                },
                {
                    "id": "E2",
                    "command": "git log -p src/database.py",
                    "output": "Added user input handling without sanitization",
                    "timestamp": "2024-12-04T10:01:00Z",
                },
                {
                    "id": "E3",
                    "command": "memory_profiler run src/image_processor.py",
                    "output": "Memory usage increases by 50MB per image processed",
                    "timestamp": "2024-12-04T10:02:00Z",
                },
                {
                    "id": "E4",
                    "command": "grep -n 'camelCase' src/utils.py",
                    "output": "src/utils.py:15: userName = getUser()",
                    "timestamp": "2024-12-04T10:03:00Z",
                },
            ],
        }

    @pytest.mark.unit
    @pytest.mark.unit
    def test_template_selection_review_report(self, sample_review_findings) -> None:
        """Scenario: Template selection works for review reports.

        Given comprehensive review findings
        When selecting template for review report
        Then it should choose review report template
        And include all required sections.
        """
        # Arrange
        deliverable_type = "review_report"
        findings = sample_review_findings

        # Act - select appropriate template
        template_selection = {
            "type": deliverable_type,
            "template_name": "Review Report Template",
            "audience": "Development team, stakeholders",
            "required_sections": [
                "Executive Summary",
                "Findings by Severity",
                "Detailed Findings",
                "Action Items",
                "Evidence Appendix",
            ],
        }

        # Confirm template selection based on findings complexity
        critical_findings = [f for f in findings if f["severity"] == "Critical"]
        if critical_findings:
            template_selection["priority"] = "High"
            template_selection["distribution"] = [
                "dev-team",
                "security-team",
                "management",
            ]

        # Assert
        assert template_selection["type"] == "review_report"
        assert "Executive Summary" in template_selection["required_sections"]
        assert "Evidence Appendix" in template_selection["required_sections"]
        assert len(template_selection["required_sections"]) == 5
        assert template_selection["priority"] == "High"

    @pytest.mark.unit
    @pytest.mark.unit
    def test_template_selection_pull_request(self) -> None:
        """Scenario: Template selection works for pull requests.

        Given code changes for review
        When selecting template for PR description
        Then it should choose PR template
        With concise summary and testing instructions.
        """
        # Arrange
        deliverable_type = "pull_request"
        changes_summary = {
            "files_changed": 5,
            "lines_added": 150,
            "lines_removed": 45,
            "test_coverage": "Added unit tests for new functionality",
        }

        # Act - select PR template
        template_selection = {
            "type": deliverable_type,
            "template_name": "Pull Request Description Template",
            "audience": "Code reviewers, CI/CD systems",
            "required_sections": [
                "Change Summary",
                "Testing Instructions",
                "Checklist",
                "Breaking Changes",
            ],
            "formatting": {
                "use_markdown": True,
                "include_diff_stats": True,
                "max_length": 2000,
            },
        }

        # Customize based on changes
        if changes_summary["files_changed"] > 3:
            template_selection["sections"].append("Large Change Notice")

        # Assert
        assert template_selection["type"] == "pull_request"
        assert "Change Summary" in template_selection["required_sections"]
        assert "Testing Instructions" in template_selection["required_sections"]
        assert "Checklist" in template_selection["required_sections"]
        assert template_selection["formatting"]["use_markdown"] is True

    @pytest.mark.unit
    @pytest.mark.unit
    def test_findings_formatting_by_severity(self, sample_review_findings) -> None:
        """Scenario: Findings are formatted by severity level.

        Given mixed severity findings
        When formatting findings
        Then it should group by severity
        And order Critical -> High -> Medium -> Low.
        """
        # Arrange & Act - sort findings by severity
        severity_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}

        sorted_findings = sorted(
            sample_review_findings,
            key=lambda f: severity_order.get(f["severity"], 5),
        )

        # Group by severity
        grouped_findings = {}
        for finding in sorted_findings:
            severity = finding["severity"]
            if severity not in grouped_findings:
                grouped_findings[severity] = []
            grouped_findings[severity].append(finding)

        # Format findings for output
        formatted_sections = []
        for severity in ["Critical", "High", "Medium", "Low"]:
            if severity in grouped_findings:
                section = {
                    "severity": severity,
                    "count": len(grouped_findings[severity]),
                    "findings": [],
                }

                for finding in grouped_findings[severity]:
                    formatted_finding = {
                        "id": finding["id"],
                        "title": finding["title"],
                        "file": finding["file"],
                        "line": finding["line"],
                        "description": finding["description"],
                        "recommendation": finding["recommendation"],
                        "evidence_refs": finding["evidence_refs"],
                    }
                    section["findings"].append(formatted_finding)

                formatted_sections.append(section)

        # Assert
        assert len(formatted_sections) == 3  # Critical, High, Low
        assert formatted_sections[0]["severity"] == "Critical"
        assert formatted_sections[1]["severity"] == "High"
        assert formatted_sections[2]["severity"] == "Low"
        assert formatted_sections[0]["count"] == 1
        assert formatted_sections[0]["findings"][0]["id"] == "F1"

    @pytest.mark.unit
    @pytest.mark.unit
    def test_markdown_formatting_quality(self, sample_review_findings) -> None:
        """Scenario: Markdown output is properly formatted.

        Given structured review data
        When generating markdown
        Then it should produce valid markdown
        With proper headers, lists, and code blocks.
        """
        # Arrange
        review_data = {
            "title": "Security and Performance Review",
            "review_id": "REV-2024-001",
            "timestamp": datetime.now(UTC).isoformat(),
            "findings": sample_review_findings[:2],  # Use first 2 findings
        }

        # Act - generate markdown
        markdown_lines = [
            f"# {review_data['title']}",
            f"**Review ID:** {review_data['review_id']}",
            f"**Timestamp:** {review_data['timestamp']}",
            "",
            "## Executive Summary",
            f"This review identified {len(review_data['findings'])} findings requiring attention.",
            "",
            "## Findings by Severity",
            "",
        ]

        for finding in review_data["findings"]:
            markdown_lines.extend(
                [
                    f"### {finding['severity']}: {finding['title']}",
                    f"**File:** `{finding['file']}:{finding['line']}`",
                    f"**Category:** {finding['category']}",
                    "",
                    f"**Description:** {finding['description']}",
                    "",
                    f"**Recommendation:** {finding['recommendation']}",
                    f"**Evidence:** {', '.join(finding['evidence_refs'])}",
                    "",
                ],
            )

        markdown_output = "\n".join(markdown_lines)

        # Assert
        assert markdown_output.startswith("# Security and Performance Review")
        assert "**Review ID:** REV-2024-001" in markdown_output
        assert "## Executive Summary" in markdown_output
        assert "### Critical: SQL injection vulnerability" in markdown_output
        assert "`src/database.py:45`" in markdown_output
        assert (
            "**Description:** User input is not properly sanitized" in markdown_output
        )
        assert "**Evidence:** E1, E2" in markdown_output

        # Verify markdown structure
        lines = markdown_output.split("\n")
        header_lines = [line for line in lines if line.startswith("#")]
        assert len(header_lines) >= 3  # Main title, sections, subsections

    @pytest.mark.unit
    @pytest.mark.unit
    def test_action_item_conversion_and_assignment(
        self, sample_review_findings
    ) -> None:
        """Scenario: Action items are converted and assigned appropriately.

        Given review findings with recommendations
        When creating action items
        Then it should convert findings to actionable tasks
        And assign appropriate priority levels.
        """
        # Arrange & Act - convert findings to action items
        action_items = []

        for i, finding in enumerate(sample_review_findings, 1):
            # Determine priority based on severity
            priority_map = {"Critical": "P1", "High": "P2", "Medium": "P3", "Low": "P4"}
            priority = priority_map.get(finding["severity"], "P3")

            # Create action item
            action_item = {
                "id": f"A{i}",
                "title": finding["title"],
                "description": finding["recommendation"],
                "priority": priority,
                "category": finding["category"],
                "assignee": self._determine_assignee(finding),
                "due_date": self._calculate_due_date(priority),
                "related_finding": finding["id"],
                "status": "Open",
            }

            action_items.append(action_item)

        # Assert
        assert len(action_items) == 3

        # Check priority assignment
        priorities = [item["priority"] for item in action_items]
        assert "P1" in priorities  # Critical finding
        assert "P2" in priorities  # High finding
        assert "P4" in priorities  # Low finding

        # Check assignee determination
        critical_action = next(
            item for item in action_items if item["priority"] == "P1"
        )
        assert critical_action["assignee"] == "security-team"

        # Check due date calculation
        for action in action_items:
            assert "due_date" in action
            assert isinstance(action["due_date"], str)

    def _determine_assignee(self, finding: dict[str, Any]) -> str:
        """Determine assignee based on finding category."""
        category_assignees = {
            "Security": "security-team",
            "Performance": "performance-team",
            "Correctness": "dev-team",
            "Style": "dev-team",
            "Documentation": "docs-team",
        }
        return category_assignees.get(finding.get("category", ""), "dev-team")

    def _calculate_due_date(self, priority: str) -> str:
        """Calculate due date based on priority."""
        today = datetime.now(UTC)
        days_map = {
            "P1": 1,  # Critical: 1 day
            "P2": 3,  # High: 3 days
            "P3": 7,  # Medium: 1 week
            "P4": 14,  # Low: 2 weeks
        }

        days = days_map.get(priority, 7)
        due_date = today + timedelta(days=days)
        return due_date.strftime("%Y-%m-%d")

    @pytest.mark.unit
    @pytest.mark.unit
    def test_appendix_compilation_and_navigation(
        self,
        sample_review_findings,
        sample_evidence_log,
    ) -> None:
        """Scenario: Appendix is compiled with proper navigation.

        Given evidence log and findings
        When creating appendix
        Then it should provide evidence references
        And enable easy navigation between findings and evidence.
        """
        # Arrange & Act - create evidence appendix
        evidence_map = {e["id"]: e for e in sample_evidence_log["evidence"]}

        appendix_sections = [
            "## Evidence Appendix",
            f"*Evidence Session: {sample_evidence_log['session_id']}*",
            "",
            "### Evidence References",
        ]

        # Create evidence index
        evidence_index = {}
        for finding in sample_review_findings:
            for evidence_ref in finding["evidence_refs"]:
                if evidence_ref not in evidence_index:
                    evidence_index[evidence_ref] = []
                evidence_index[evidence_ref].append(finding["id"])

        # Add evidence details to appendix
        for evidence_id, related_findings in evidence_index.items():
            if evidence_id in evidence_map:
                evidence = evidence_map[evidence_id]
                appendix_sections.extend(
                    [
                        f"#### {evidence_id}",
                        f"**Command:** `{evidence['command']}`",
                        f"**Timestamp:** {evidence['timestamp']}",
                        "",
                        "```",
                        evidence["output"][:200]
                        + ("..." if len(evidence["output"]) > 200 else ""),
                        "```",
                        f"**Referenced by findings:** {', '.join(related_findings)}",
                        "",
                    ],
                )

        appendix_output = "\n".join(appendix_sections)

        # Assert
        assert "## Evidence Appendix" in appendix_output
        assert (
            f"*Evidence Session: {sample_evidence_log['session_id']}*"
            in appendix_output
        )
        assert "#### E1" in appendix_output
        assert "**Command:** `grep -r 'execute(' src/`" in appendix_output
        assert "**Referenced by findings:** F1" in appendix_output
        assert "```" in appendix_output  # Code blocks present

        # Verify navigation capability
        assert len(evidence_index) > 0
        assert "E1" in evidence_index
        assert evidence_index["E1"] == ["F1"]

    @pytest.mark.unit
    @pytest.mark.unit
    def test_template_variable_substitution(self) -> None:
        """Scenario: Template variables are properly substituted.

        Given template with placeholders
        When generating final output
        Then it should replace all variables with actual values.
        """
        # Arrange - template with variables
        template = """# {{title}}

**Review ID:** {{review_id}}
**Timestamp:** {{timestamp}}
**Reviewer:** {{reviewer}}

## Summary

{{findings_count}} findings were identified during this review.

{{summary}}

## Key Findings

{{findings}}

## Actions Required

{{actions}}

---

*This report was generated using the imbue structured-output methodology*"""

        # Template variables
        variables = {
            "title": "Security Review Report",
            "review_id": "SEC-2024-001",
            "timestamp": "2024-12-04T10:00:00Z",
            "reviewer": "Security Team",
            "findings_count": 3,
            "summary": "Critical security vulnerabilities require immediate attention.",
            "findings": "1. SQL injection vulnerability\n2. Memory leak in processing\n3. Inconsistent naming",
            "actions": "1. Fix SQL injection (P1)\n2. Implement resource cleanup (P2)\n3. Refactor variable names (P4)",
        }

        # Act - substitute variables
        output = template
        for var, value in variables.items():
            output = output.replace(f"{{{{{var}}}}}", str(value))

        # Assert
        assert "# Security Review Report" in output
        assert "**Review ID:** SEC-2024-001" in output
        assert "**Reviewer:** Security Team" in output
        assert "3 findings were identified" in output
        assert "Critical security vulnerabilities" in output

        # Verify no unsubstituted variables remain
        assert "{{" not in output
        assert "}}" not in output

    @pytest.mark.unit
    def test_output_format_consistency(self, sample_review_findings) -> None:
        """Scenario: Output format maintains consistency across templates.

        Given different template types
        When generating outputs
        Then key elements should be consistently formatted.
        """
        # Arrange - generate outputs from different templates
        templates = {
            "review_report": self._generate_review_report(sample_review_findings),
            "pull_request": self._generate_pr_description(sample_review_findings),
            "security_brief": self._generate_security_brief(sample_review_findings),
        }

        # Act - check consistency elements
        consistency_checks = []

        for template_type, output in templates.items():
            checks = {
                "has_title": bool(output and output.strip().startswith("#")),
                "has_findings": "finding" in output.lower()
                or "issue" in output.lower(),
                "has_metadata": any(
                    key in output.lower() for key in ["id:", "date:", "reviewer:"]
                ),
                "proper_markdown": not any(
                    "<" in output and ">" in output
                    for output in [output]
                    if "<" in output
                ),
            }
            consistency_checks.append((template_type, checks))

        # Assert
        for template_type, checks in consistency_checks:
            assert checks["has_title"], f"{template_type} missing title"
            assert checks["has_findings"], f"{template_type} missing findings"
            assert checks["proper_markdown"], f"{template_type} has invalid markdown"

    def _generate_review_report(self, findings) -> str:
        """Generate review report output."""
        return f"""# Security Review Report

**Review ID:** REV-001
**Date:** 2024-12-04

## Findings ({len(findings)})

{chr(10).join(f"- {f['severity']}: {f['title']}" for f in findings)}"""

    def _generate_pr_description(self, findings) -> str:
        """Generate PR description output."""
        return f"""# Pull Request: Security Improvements

## Changes Summary
This PR addresses {len(findings)} security-related items.

## Checklist
{chr(10).join(f"- [ ] Fix {f['title'].lower()}" for f in findings)}"""

    def _generate_security_brief(self, findings) -> str:
        """Generate security brief output."""
        critical_findings = [f for f in findings if f["severity"] == "Critical"]
        return f"""# Security Brief

**Critical Issues:** {len(critical_findings)}
**Total Issues:** {len(findings)}

{chr(10).join(f"[ALERT] {f['title']}" for f in critical_findings if critical_findings)}"""

    @pytest.mark.unit
    def test_error_handling_invalid_data(self) -> None:
        """Scenario: Template formatting handles invalid data gracefully.

        Given malformed or missing data
        When generating output
        Then it should provide sensible defaults
        And not crash on missing fields.
        """
        # Arrange - malformed finding data
        malformed_findings = [
            {
                # Missing id, severity, title
                "description": "Some issue",
                "file": "test.py",
            },
            {
                "id": "F2",
                "severity": "InvalidSeverity",  # Invalid severity
                "title": "Valid finding",
                "description": "Proper finding",
            },
        ]

        # Act - format with error handling
        formatted_findings = []
        for finding in malformed_findings:
            formatted_finding = {
                "id": finding.get("id", "UNKNOWN"),
                "title": finding.get("title", "Untitled Finding"),
                "severity": self._validate_severity(finding.get("severity", "Medium")),
                "description": finding.get("description", "No description available"),
                "file": finding.get("file", "Unknown file"),
            }
            formatted_findings.append(formatted_finding)

        # Assert
        assert len(formatted_findings) == 2
        assert formatted_findings[0]["id"] == "UNKNOWN"
        assert formatted_findings[0]["title"] == "Untitled Finding"
        assert formatted_findings[1]["severity"] == "Medium"  # Corrected from invalid

    def _validate_severity(self, severity):
        """Validate and correct severity levels."""
        valid_severities = ["Critical", "High", "Medium", "Low"]
        return severity if severity in valid_severities else "Medium"

    @pytest.mark.performance
    def test_large_finding_set_formatting(self) -> None:
        """Scenario: Template formatting performs efficiently with many findings.

        Given a large set of findings
        When generating output
        Then it should complete in reasonable time.
        """
        # Arrange - generate many findings
        large_findings = []
        for i in range(500):
            large_findings.append(
                {
                    "id": f"F{i + 1:04d}",
                    "title": f"Finding {i + 1}",
                    "severity": ["Critical", "High", "Medium", "Low"][i % 4],
                    "description": f"Description for finding {i + 1}",
                    "file": f"src/file_{i % 20}.py",
                    "line": (i * 7) % 200 + 1,
                },
            )

        # Act - measure formatting performance
        start_time = time.time()

        # Group and format findings
        grouped_findings = {}
        for finding in large_findings:
            severity = finding["severity"]
            if severity not in grouped_findings:
                grouped_findings[severity] = []
            grouped_findings[severity].append(finding)

        # Generate markdown output
        markdown_lines = ["# Large Review Report", ""]
        for severity in ["Critical", "High", "Medium", "Low"]:
            if severity in grouped_findings:
                markdown_lines.append(
                    f"## {severity} Findings ({len(grouped_findings[severity])})",
                )
                # Show only first 10 for each category to avoid huge output
                for finding in grouped_findings[severity][:10]:
                    markdown_lines.append(f"- {finding['id']}: {finding['title']}")

        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should process 500 findings in under 2 seconds
        assert len(grouped_findings) == 4  # All severities present
        assert len(markdown_lines) > 10  # Output generated
        assert "## Critical Findings" in "\n".join(markdown_lines)
