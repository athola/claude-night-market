"""BDD tests for the tokio task-orchestration vs select! rule (issue #598).

Feature: Rust Review Flags Manual Task Teardown That select! Simplifies
  As a Rust code reviewer
  I want the rust-review skill to flag hand-rolled multi-task
  orchestration (2+ spawned tasks torn down with consecutive abort()
  calls around an mpsc-shared sink)
  So that a safer single select! loop is recommended, with the
  cancel-safety and head-of-line caveats stated.

The rule lives in the concurrency-patterns module (an extension of an
existing module, not a new file), is surfaced in the rust-auditor
agent's Concurrency expertise, and appears in the rust-review command
checklist. These tests assert the content contract of all three.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PENSIVE_ROOT = Path(__file__).resolve().parent.parent.parent
CONCURRENCY_MODULE = (
    PENSIVE_ROOT / "skills" / "rust-review" / "modules" / "concurrency-patterns.md"
)
RUST_AUDITOR_AGENT = PENSIVE_ROOT / "agents" / "rust-auditor.md"
RUST_REVIEW_COMMAND = PENSIVE_ROOT / "commands" / "rust-review.md"


class TestSelectOrchestrationSection:
    """Feature: concurrency-patterns.md documents the select! rule."""

    @pytest.fixture
    def text(self) -> str:
        return CONCURRENCY_MODULE.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_section_exists(self, text: str) -> None:
        """
        Scenario: the module has a Task Orchestration vs select! section
        Given the concurrency-patterns module
        When its headings are scanned
        Then a dedicated select! orchestration section is present
        """
        assert "Task Orchestration vs" in text
        assert "select!" in text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detection_heuristic_covers_spawn_count(self, text: str) -> None:
        """
        Scenario: the heuristic requires two or more spawned tasks
        Given the detection heuristic
        When it is read
        Then it keys on 2+ tokio::spawn handles bound to locals
        """
        lower = text.lower()
        assert "tokio::spawn" in lower
        assert "two or more" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detection_heuristic_covers_abort_teardown(self, text: str) -> None:
        """
        Scenario: the heuristic keys on consecutive abort() teardown
        Given the detection heuristic
        When it is read
        Then it names consecutive abort() calls as the tell
        """
        assert "abort()" in text
        assert "consecutive" in text.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_detection_heuristic_covers_shared_sink(self, text: str) -> None:
        """
        Scenario: the heuristic keys on an mpsc-shared sink
        Given the detection heuristic
        When it is read
        Then it names a SplitSink shared across tasks via an mpsc channel
        """
        lower = text.lower()
        assert "mpsc" in lower
        assert "splitsink" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_states_cancel_safety_caveat(self, text: str) -> None:
        """
        Scenario: the rule states the cancel-safety caveat
        Given the caveats section
        When it is read
        Then it restricts the rewrite to cancel-safe branch futures
        """
        assert "cancel-safe" in text.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_states_head_of_line_caveat(self, text: str) -> None:
        """
        Scenario: the rule states the head-of-line-blocking caveat
        Given the caveats section
        When it is read
        Then it warns that select! head-of-line-blocks sibling branches
        """
        assert "head-of-line" in text.lower()


class TestSelectOrchestrationWiredIntoSurfaces:
    """Feature: the rule is surfaced in the agent and command."""

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_lists_orchestration_expertise(self) -> None:
        """
        Scenario: rust-auditor agent lists the orchestration expertise
        Given the rust-auditor agent definition
        When its Concurrency expertise is read
        Then it references select! task-orchestration simplification
        """
        text = RUST_AUDITOR_AGENT.read_text().lower()
        assert "select!" in text
        assert "abort()" in text

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_command_checklist_lists_orchestration(self) -> None:
        """
        Scenario: rust-review command checklist references the rule
        Given the rust-review command
        When its concurrency checklist is read
        Then it references the select! rewrite for manual teardown
        """
        text = RUST_REVIEW_COMMAND.read_text().lower()
        assert "select!" in text
        assert "abort()" in text
