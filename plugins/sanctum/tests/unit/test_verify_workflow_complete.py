"""Tests for verify_workflow_complete hook - post-implementation reminders."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from hooks.verify_workflow_complete import main


class TestWorkflowReminder:
    """
    Feature: Post-Implementation Workflow Reminder

    As a developer using Claude Code
    I want to be reminded of post-implementation checklists when a session stops
    So that I don't forget critical verification and documentation steps
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_outputs_reminder_as_json(self, capsys):
        """
        Scenario: Hook outputs reminder in JSON format
        Given a session stop event occurs
        When the verify_workflow_complete hook runs
        Then it outputs a JSON object with a 'reason' field
        And the reason contains the post-implementation checklist
        """
        # Arrange - No stdin input needed
        # Act
        with patch("sys.stdin"):
            with pytest.raises(SystemExit) as exc_info:
                main()

        # Assert
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "reason" in output
        assert isinstance(output["reason"], str)
        assert len(output["reason"]) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_contains_proof_of_work_section(self, capsys):
        """
        Scenario: Reminder includes proof-of-work checklist
        Given a session stop event occurs
        When the verify_workflow_complete hook runs
        Then the reminder includes PROOF-OF-WORK section
        And it mentions creating TodoWrite items
        And it mentions capturing evidence with references
        """
        # Arrange & Act
        with patch("sys.stdin"):
            with pytest.raises(SystemExit):
                main()

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        reason = output["reason"]

        assert "PROOF-OF-WORK" in reason
        assert "TodoWrite" in reason
        assert "proof:solution-tested" in reason
        assert "proof:evidence-captured" in reason
        assert "[E1]" in reason or "[E2]" in reason

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_contains_documentation_updates(self, capsys):
        """
        Scenario: Reminder includes documentation update checklist
        Given a session stop event occurs
        When the verify_workflow_complete hook runs
        Then the reminder includes Documentation Updates section
        And it lists all required update commands
        """
        # Arrange & Act
        with patch("sys.stdin"):
            with pytest.raises(SystemExit):
                main()

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        reason = output["reason"]

        assert "Documentation Updates" in reason
        assert "/sanctum:update-docs" in reason
        assert "/abstract:make-dogfood" in reason
        assert "/sanctum:update-readme" in reason
        assert "/sanctum:update-tests" in reason

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_handles_missing_stdin_gracefully(self, capsys):
        """
        Scenario: Hook handles missing or invalid stdin gracefully
        Given a session stop event with no stdin payload
        When the verify_workflow_complete hook runs
        Then it still outputs the reminder
        And does not raise an error
        """
        # Arrange - Simulate no stdin
        # Act
        with patch("sys.stdin"):
            with pytest.raises(SystemExit):
                main()

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "reason" in output
        assert len(output["reason"]) > 0

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_reminder_mentions_applicability_disclaimer(self, capsys):
        """
        Scenario: Reminder includes disclaimer for non-applicable cases
        Given a session stop event occurs
        When the verify_workflow_complete hook runs
        Then the reminder mentions when to disregard it
        And references simple fixes and research tasks
        """
        # Arrange & Act
        with patch("sys.stdin"):
            with pytest.raises(SystemExit):
                main()

        # Assert
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        reason = output["reason"]

        assert "not applicable" in reason.lower()
        assert "simple fix" in reason.lower() or "research" in reason.lower()
