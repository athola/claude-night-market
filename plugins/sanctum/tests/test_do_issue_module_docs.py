# ruff: noqa: D101,D102,D103,D205,D212,D400,D415,E501
"""Tests for do-issue module documentation completeness.

Feature: Do-Issue Safety Documentation

    As an operator running do-issue workflows
    I want critical safety warnings in the documentation
    So that I avoid unrecoverable headless/remote-control hangs
"""

from __future__ import annotations

from pathlib import Path

import pytest

DO_ISSUE_MODULES = Path(__file__).parent.parent / "skills" / "do-issue" / "modules"


@pytest.fixture
def parallel_execution_content() -> str:
    """Load the parallel-execution module."""
    return (DO_ISSUE_MODULES / "parallel-execution.md").read_text()


@pytest.fixture
def troubleshooting_content() -> str:
    """Load the troubleshooting module."""
    return (DO_ISSUE_MODULES / "troubleshooting.md").read_text()


class TestRemoteControlWarning:
    """Verify parallel-execution warns about remote control limitations."""

    @pytest.mark.unit
    def test_warns_against_remote_control_dispatch(
        self, parallel_execution_content: str
    ) -> None:
        """
        GIVEN the parallel-execution module
        WHEN checking for remote control guidance
        THEN it warns against running parallel subagents via remote-control.
        """
        assert "remote-control" in parallel_execution_content.lower()
        assert "headless" in parallel_execution_content.lower()

    @pytest.mark.unit
    def test_documents_safe_alternatives(self, parallel_execution_content: str) -> None:
        """
        GIVEN the parallel-execution module
        WHEN checking for safe alternatives
        THEN it lists run_in_background and scope minor as options.
        """
        assert "run_in_background" in parallel_execution_content
        assert "minor" in parallel_execution_content

    @pytest.mark.unit
    def test_links_to_troubleshooting(self, parallel_execution_content: str) -> None:
        """
        GIVEN the parallel-execution module
        WHEN checking cross-references
        THEN it links to troubleshooting.md for recovery steps.
        """
        assert "troubleshooting.md" in parallel_execution_content


class TestSubagentHangTroubleshooting:
    """Verify troubleshooting documents subagent hang recovery."""

    @pytest.mark.unit
    def test_documents_subagent_hang_section(
        self, troubleshooting_content: str
    ) -> None:
        """
        GIVEN the troubleshooting module
        WHEN checking for hang documentation
        THEN it has a dedicated section for subagent hangs.
        """
        assert "Subagent Hangs" in troubleshooting_content

    @pytest.mark.unit
    def test_documents_symptoms(self, troubleshooting_content: str) -> None:
        """
        GIVEN the troubleshooting module
        WHEN checking symptoms documentation
        THEN it describes observable hang indicators.
        """
        content = troubleshooting_content.lower()
        assert "in progress" in content
        assert "no output" in content or "no tool calls" in content

    @pytest.mark.unit
    def test_documents_recovery_steps(self, troubleshooting_content: str) -> None:
        """
        GIVEN the troubleshooting module
        WHEN checking recovery documentation
        THEN it includes Esc interrupt and SIGINT kill as recovery options.
        """
        assert "Esc" in troubleshooting_content
        assert "SIGINT" in troubleshooting_content

    @pytest.mark.unit
    def test_documents_prevention_strategies(
        self, troubleshooting_content: str
    ) -> None:
        """
        GIVEN the troubleshooting module
        WHEN checking prevention documentation
        THEN it recommends running locally and using background mode.
        """
        assert "run_in_background" in troubleshooting_content
        assert "locally" in troubleshooting_content.lower()

    @pytest.mark.unit
    def test_references_upstream_issues(self, troubleshooting_content: str) -> None:
        """
        GIVEN the troubleshooting module
        WHEN checking issue references
        THEN it links to the known upstream bug reports.
        """
        assert "#28482" in troubleshooting_content
        assert "#33232" in troubleshooting_content
        assert "#13240" in troubleshooting_content
