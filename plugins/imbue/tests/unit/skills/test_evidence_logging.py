"""Tests for evidence-logging skill business logic.

This module tests the evidence capture and reproducibility functionality,
following TDD/BDD principles and testing all evidence management scenarios.
"""

import json
from datetime import UTC, datetime

import pytest


class TestEvidenceLoggingSkill:
    """Feature: Evidence logging ensures reproducible review findings.

    As a reviewer
    I want all commands and citations logged systematically
    So that findings can be reproduced and verified
    """

    @pytest.fixture
    def mock_evidence_logging_skill_content(self) -> str:
        """Mock evidence-logging skill content."""
        return """---
name: evidence-logging
description: Workflow for capturing reproducible evidence and audit trails
category: review-patterns
dependencies: []
tools:
  - Read
  - Write
  - Bash
  - TodoWrite
tags:
  - evidence
  - logging
  - reproducibility
  - audit-trail
---

# Evidence Logging

Workflow for capturing reproducible evidence and audit trails during reviews.

## TodoWrite Items

- `evidence-logging:log-initialized`
- `evidence-logging:commands-captured`
- `evidence-logging:citations-recorded`
- `evidence-logging:artifacts-indexed`

## Evidence Log Structure

```json
{
  "session_id": "unique-session-id",
  "timestamp": "ISO-8601 timestamp",
  "context": {
    "repository": "/path/to/repo",
    "branch": "main",
    "baseline": "HEAD~1"
  },
  "evidence": [
    {
      "id": "E1",
      "command": "full command with arguments",
      "output": "command output or snippet",
      "timestamp": "ISO-8601 timestamp",
      "working_directory": "/execution/path"
    }
  ],
  "citations": [
    {
      "id": "C1",
      "url": "https://example.com",
      "title": "Document title",
      "accessed": "ISO-8601 timestamp",
      "relevant_snippet": "Key information"
    }
  ]
}
```

## Command Capture Protocol

1. Log all discovery and analysis commands
2. Capture full command with all arguments
3. Record working directory
4. Store relevant output (full or snippet)
5. Assign sequential evidence IDs [E1], [E2], etc.

## Citation Management

1. Record all external references
2. Include access timestamps
3. Store relevant snippets
4. Maintain URL integrity

## Export Formats

- JSON: Machine-readable evidence
- Markdown: Human-readable report
- CSV: Spreadsheet-compatible evidence
"""

    @pytest.fixture
    def sample_evidence_session(self):
        """Sample evidence logging session data."""
        return {
            "session_id": "evidence-session-123",
            "timestamp": datetime.now(UTC).isoformat(),
            "context": {
                "repository": "/test/review-project",
                "branch": "feature/new-feature",
                "baseline": "main",
            },
            "evidence": [],
            "citations": [],
        }

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_log_initialization(self, sample_evidence_session) -> None:
        """Scenario: Evidence log initializes with session context
        Given starting a review workflow
        When initializing evidence logging
        Then it should create structured evidence log
        With session ID, timestamp, and context.
        """
        # Arrange & Act - evidence session is already initialized
        evidence_log = sample_evidence_session

        # Assert
        assert "session_id" in evidence_log
        assert "timestamp" in evidence_log
        assert "context" in evidence_log
        assert "evidence" in evidence_log
        assert "citations" in evidence_log
        assert evidence_log["session_id"] == "evidence-session-123"
        assert evidence_log["context"]["repository"] == "/test/review-project"
        assert evidence_log["context"]["branch"] == "feature/new-feature"
        assert evidence_log["context"]["baseline"] == "main"
        assert isinstance(evidence_log["evidence"], list)
        assert isinstance(evidence_log["citations"], list)

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_captures_command_output(self, sample_evidence_session) -> None:
        """Scenario: Evidence logging captures command outputs
        Given review commands being executed
        When logging evidence
        Then it should capture command, output, and timestamp
        And provide reference identifiers [E1], [E2], etc.
        """
        # Arrange
        evidence_log = sample_evidence_session
        command = "git diff --stat HEAD~1..HEAD"
        output = " src/main.py | 5 +++++\n tests/test_main.py | 10 ++++++++++"

        # Act - log command evidence
        evidence_item = {
            "id": f"E{len(evidence_log['evidence']) + 1}",
            "command": command,
            "output": output,
            "timestamp": datetime.now(UTC).isoformat(),
            "working_directory": evidence_log["context"]["repository"],
        }
        evidence_log["evidence"].append(evidence_item)

        # Assert
        assert len(evidence_log["evidence"]) == 1
        assert evidence_log["evidence"][0]["id"] == "E1"
        assert evidence_log["evidence"][0]["command"] == command
        assert evidence_log["evidence"][0]["output"] == output
        assert "timestamp" in evidence_log["evidence"][0]
        assert (
            evidence_log["evidence"][0]["working_directory"] == "/test/review-project"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_sequential_identifiers(self, sample_evidence_session) -> None:
        """Scenario: Evidence logging assigns sequential identifiers
        Given multiple commands being logged
        When capturing evidence
        Then it should assign sequential IDs [E1], [E2], [E3]
        And maintain consistent formatting.
        """
        # Arrange
        evidence_log = sample_evidence_session
        commands = [
            ("pwd", "/test/review-project"),
            ("git status", "On branch feature/new-feature"),
            ("git log --oneline -5", "abc123 Fix bug\ndef456 Add feature"),
        ]

        # Act - log multiple commands
        for command, output in commands:
            evidence_item = {
                "id": f"E{len(evidence_log['evidence']) + 1}",
                "command": command,
                "output": output,
                "timestamp": datetime.now(UTC).isoformat(),
                "working_directory": evidence_log["context"]["repository"],
            }
            evidence_log["evidence"].append(evidence_item)

        # Assert
        assert len(evidence_log["evidence"]) == 3
        assert evidence_log["evidence"][0]["id"] == "E1"
        assert evidence_log["evidence"][1]["id"] == "E2"
        assert evidence_log["evidence"][2]["id"] == "E3"
        # Verify sequential numbering
        expected_ids = ["E1", "E2", "E3"]
        actual_ids = [item["id"] for item in evidence_log["evidence"]]
        assert actual_ids == expected_ids

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_supports_citations(self, sample_evidence_session) -> None:
        """Scenario: Evidence log supports web citations
        Given web.run citations in review
        When logging evidence
        Then it should capture URLs and access timestamps
        And format citations consistently.
        """
        # Arrange
        evidence_log = sample_evidence_session
        citation = {
            "id": f"C{len(evidence_log['citations']) + 1}",
            "url": "https://docs.python.org/3/library/json.html",
            "title": "JSON encoder and decoder",
            "accessed": datetime.now(UTC).isoformat(),
            "relevant_snippet": "JSON (JavaScript Object Notation) is a lightweight data interchange format.",
        }

        # Act - add citation
        evidence_log["citations"].append(citation)

        # Assert
        assert len(evidence_log["citations"]) == 1
        assert evidence_log["citations"][0]["id"] == "C1"
        assert (
            evidence_log["citations"][0]["url"]
            == "https://docs.python.org/3/library/json.html"
        )
        assert evidence_log["citations"][0]["title"] == "JSON encoder and decoder"
        assert "accessed" in evidence_log["citations"][0]
        assert "relevant_snippet" in evidence_log["citations"][0]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_exports_json_format(self, sample_evidence_session) -> None:
        """Scenario: Evidence log exports in structured JSON format
        Given a complete evidence log
        When exporting to JSON
        Then it should maintain structure and validity
        And include all evidence and citations.
        """
        # Arrange - populate evidence log
        sample_evidence_session["evidence"].append(
            {
                "id": "E1",
                "command": "git diff",
                "output": "diff content",
                "timestamp": "2024-12-04T10:00:00Z",
                "working_directory": "/test/repo",
            },
        )
        sample_evidence_session["citations"].append(
            {
                "id": "C1",
                "url": "https://example.com",
                "title": "Example",
                "accessed": "2024-12-04T10:00:00Z",
                "relevant_snippet": "snippet",
            },
        )

        # Act - export to JSON
        json_output = json.dumps(sample_evidence_session, indent=2)

        # Assert
        assert isinstance(json_output, str)
        # Verify it's valid JSON by parsing back
        parsed = json.loads(json_output)
        assert parsed["session_id"] == "evidence-session-123"
        assert len(parsed["evidence"]) == 1
        assert len(parsed["citations"]) == 1
        assert parsed["evidence"][0]["id"] == "E1"
        assert parsed["citations"][0]["id"] == "C1"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_exports_markdown_format(self, sample_evidence_session) -> None:
        """Scenario: Evidence log exports in human-readable Markdown
        Given a complete evidence log
        When exporting to Markdown
        Then it should format evidence and citations clearly
        And maintain reference integrity.
        """
        # Arrange - populate evidence log
        sample_evidence_session["evidence"].append(
            {
                "id": "E1",
                "command": "git status",
                "output": "On branch main\nnothing to commit",
                "timestamp": "2024-12-04T10:00:00Z",
                "working_directory": "/test/repo",
            },
        )

        # Act - generate markdown
        markdown_lines = [
            f"# Evidence Log - {sample_evidence_session['session_id']}",
            f"**Timestamp:** {sample_evidence_session['timestamp']}",
            f"**Repository:** {sample_evidence_session['context']['repository']}",
            f"**Branch:** {sample_evidence_session['context']['branch']}",
            "",
            "## Evidence",
            "",
        ]

        for evidence in sample_evidence_session["evidence"]:
            markdown_lines.extend(
                [
                    f"### {evidence['id']}",
                    f"**Command:** `{evidence['command']}`",
                    f"**Working Directory:** {evidence['working_directory']}",
                    f"**Timestamp:** {evidence['timestamp']}",
                    "",
                    "```",
                    evidence["output"],
                    "```",
                    "",
                ],
            )

        markdown_output = "\n".join(markdown_lines)

        # Assert
        assert "# Evidence Log" in markdown_output
        assert "evidence-session-123" in markdown_output
        assert "### E1" in markdown_output
        assert "`git status`" in markdown_output
        assert "On branch main" in markdown_output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_exports_csv_format(self, sample_evidence_session) -> None:
        """Scenario: Evidence log exports in CSV format for analysis
        Given a complete evidence log
        When exporting to CSV
        Then it should create tabular evidence data
        With proper escaping and headers.
        """
        # Arrange - populate evidence log
        sample_evidence_session["evidence"].extend(
            [
                {
                    "id": "E1",
                    "command": "git diff --stat",
                    "output": "2 files changed",
                    "timestamp": "2024-12-04T10:00:00Z",
                    "working_directory": "/test/repo",
                },
                {
                    "id": "E2",
                    "command": "find . -name '*.py'",
                    "output": "./src/main.py\n./test/test_main.py",
                    "timestamp": "2024-12-04T10:01:00Z",
                    "working_directory": "/test/repo",
                },
            ],
        )

        # Act - generate CSV
        csv_lines = ["ID,Timestamp,Command,Working Directory,Output"]

        for evidence in sample_evidence_session["evidence"]:
            # Escape commas and quotes in output
            escaped_output = evidence["output"].replace('"', '""')
            csv_line = f'{evidence["id"]},{evidence["timestamp"]},"{evidence["command"]}","{evidence["working_directory"]}","{escaped_output}"'
            csv_lines.append(csv_line)

        csv_output = "\n".join(csv_lines)

        # Assert
        assert "ID,Timestamp,Command,Working Directory,Output" in csv_output
        assert 'E1,2024-12-04T10:00:00Z,"git diff --stat"' in csv_output
        assert "E2,2024-12-04T10:01:00Z,\"find . -name '*.py'\"" in csv_output

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_handles_large_outputs(self, sample_evidence_session) -> None:
        """Scenario: Evidence logging handles large command outputs
        Given commands with substantial output
        When logging evidence
        Then it should manage output size appropriately
        And provide relevant snippets for large content.
        """
        # Arrange - generate large output
        large_output = "\n".join([f"Line {i} of command output" for i in range(1000)])
        max_snippet_length = 500

        # Act - handle large output by creating snippet
        if len(large_output) > max_snippet_length:
            snippet = (
                large_output[:max_snippet_length]
                + f"\n... ({len(large_output)} total lines, truncated)"
            )
        else:
            snippet = large_output

        evidence_item = {
            "id": "E1",
            "command": "find . -type f",
            "output": snippet,
            "timestamp": datetime.now(UTC).isoformat(),
            "working_directory": "/test/repo",
        }
        sample_evidence_session["evidence"].append(evidence_item)

        # Assert
        assert len(sample_evidence_session["evidence"]) == 1
        assert "truncated" in sample_evidence_session["evidence"][0]["output"]
        assert (
            len(sample_evidence_session["evidence"][0]["output"])
            <= max_snippet_length + 100
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_evidence_references_in_findings(self, sample_evidence_session) -> None:
        """Scenario: Evidence references maintain integrity
        Given review findings referencing evidence
        When creating findings
        Then evidence references should resolve correctly
        And maintain bidirectional links.
        """
        # Arrange - add evidence
        sample_evidence_session["evidence"].extend(
            [
                {
                    "id": "E1",
                    "command": "git diff src/main.py",
                    "output": "function signature changed",
                    "timestamp": "2024-12-04T10:00:00Z",
                    "working_directory": "/test/repo",
                },
                {
                    "id": "E2",
                    "command": "grep -r 'TODO' src/",
                    "output": "src/utils.py:5: TODO: Add error handling",
                    "timestamp": "2024-12-04T10:01:00Z",
                    "working_directory": "/test/repo",
                },
            ],
        )

        # Act - create findings with evidence references
        findings = [
            {
                "id": "F1",
                "title": "Function signature breaking change",
                "description": "Function signature was changed without compatibility",
                "severity": "High",
                "file": "src/main.py",
                "evidence_refs": ["E1"],
            },
            {
                "id": "F2",
                "title": "Outstanding TODO items",
                "description": "TODO items found in production code",
                "severity": "Medium",
                "file": "src/utils.py",
                "evidence_refs": ["E2"],
            },
        ]

        # Assert - verify evidence references resolve
        evidence_ids = {e["id"] for e in sample_evidence_session["evidence"]}
        for finding in findings:
            for ref in finding["evidence_refs"]:
                assert ref in evidence_ids, (
                    f"Evidence reference {ref} not found in evidence log"
                )

        # Verify specific references
        assert "E1" in findings[0]["evidence_refs"]
        assert "E2" in findings[1]["evidence_refs"]

    @pytest.mark.unit
    def test_evidence_error_handling(self, sample_evidence_session) -> None:
        """Scenario: Evidence logging handles errors gracefully
        Given command execution failures
        When logging evidence
        Then it should capture error information
        And continue logging subsequent commands.
        """
        # Arrange
        error_command = "git status --invalid-option"
        error_output = "error: unknown option `invalid-option'"

        # Act - log command error as evidence
        error_evidence = {
            "id": "E1",
            "command": error_command,
            "output": f"ERROR: {error_output}",
            "timestamp": datetime.now(UTC).isoformat(),
            "working_directory": sample_evidence_session["context"]["repository"],
            "status": "failed",
        }
        sample_evidence_session["evidence"].append(error_evidence)

        # Log successful command after error
        success_evidence = {
            "id": "E2",
            "command": "pwd",
            "output": "/test/review-project",
            "timestamp": datetime.now(UTC).isoformat(),
            "working_directory": sample_evidence_session["context"]["repository"],
            "status": "success",
        }
        sample_evidence_session["evidence"].append(success_evidence)

        # Assert
        assert len(sample_evidence_session["evidence"]) == 2
        assert sample_evidence_session["evidence"][0]["status"] == "failed"
        assert "ERROR:" in sample_evidence_session["evidence"][0]["output"]
        assert sample_evidence_session["evidence"][1]["status"] == "success"
        assert (
            sample_evidence_session["evidence"][1]["output"] == "/test/review-project"
        )

    @pytest.mark.unit
    def test_evidence_file_output_persistence(
        self, sample_evidence_session, tmp_path
    ) -> None:
        """Scenario: Evidence log persists to file system
        Given evidence logging session
        When saving evidence log
        Then it should write valid JSON to file
        And be readable for later analysis.
        """
        # Arrange
        evidence_file = tmp_path / "evidence_log.json"
        sample_evidence_session["evidence"].append(
            {
                "id": "E1",
                "command": "git log --oneline -1",
                "output": "abc123 Latest commit message",
                "timestamp": datetime.now(UTC).isoformat(),
                "working_directory": sample_evidence_session["context"]["repository"],
            },
        )

        # Act - write evidence to file
        evidence_file.write_text(json.dumps(sample_evidence_session, indent=2))

        # Assert
        assert evidence_file.exists()
        assert evidence_file.stat().st_size > 0

        # Verify file can be read and parsed
        loaded_evidence = json.loads(evidence_file.read_text())
        assert loaded_evidence["session_id"] == "evidence-session-123"
        assert len(loaded_evidence["evidence"]) == 1
        assert loaded_evidence["evidence"][0]["id"] == "E1"

    @pytest.mark.unit
    def test_evidence_session_uniqueness(self) -> None:
        """Scenario: Evidence logging generates unique session IDs
        Given multiple evidence logging sessions
        When creating new sessions
        Then each should have unique identifiers
        And prevent session conflicts.
        """
        # Arrange & Act - create multiple sessions
        sessions = []
        for i in range(5):
            session = {
                "session_id": f"evidence-session-{i}-{datetime.now(UTC).isoformat()}",
                "timestamp": datetime.now(UTC).isoformat(),
                "evidence": [],
                "citations": [],
            }
            sessions.append(session)

        # Assert - all session IDs are unique
        session_ids = [session["session_id"] for session in sessions]
        assert len(session_ids) == len(set(session_ids))  # All unique
        for session_id in session_ids:
            assert "evidence-session-" in session_id
            assert "T" in session_id  # Contains timestamp

    @pytest.mark.performance
    def test_evidence_logging_performance(self, sample_evidence_session) -> None:
        """Scenario: Evidence logging performs efficiently with large datasets
        Given many evidence items to log
        When processing evidence
        Then it should maintain reasonable performance
        And memory usage.
        """
        import time

        # Arrange - prepare large evidence dataset
        evidence_items = []
        for i in range(1000):
            evidence_items.append(
                {
                    "id": f"E{i + 1}",
                    "command": f"test-command-{i}",
                    "output": f"output-{i}",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "working_directory": "/test/repo",
                },
            )

        # Act - measure performance
        start_time = time.time()
        for evidence in evidence_items:
            sample_evidence_session["evidence"].append(evidence)
        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Should process 1000 items in under 1 second
        assert len(sample_evidence_session["evidence"]) == 1000
        # Verify memory usage is reasonable (basic check)
        json_size = len(json.dumps(sample_evidence_session))
        assert json_size < 10_000_000  # Should be under 10MB
