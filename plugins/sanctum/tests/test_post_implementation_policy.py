"""Tests for post_implementation_policy.py hook.

This module tests the governance policy injection hook that enforces
proof-of-work and Iron Law TDD compliance at session start.

The Iron Law: NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


class TestPostImplementationPolicy:
    """Feature: Governance policy enforces proof-of-work and Iron Law.

    As a session participant
    I want governance policy injected at session start
    So that proof-of-work and TDD compliance are reminded
    """

    @pytest.fixture
    def hook_path(self) -> Path:
        """Path to the post_implementation_policy.py hook."""
        return Path(__file__).parent.parent / "hooks" / "post_implementation_policy.py"

    @pytest.fixture
    def hook_content(self, hook_path: Path) -> str:
        """Load the hook content."""
        return hook_path.read_text()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_exists(self, hook_path: Path) -> None:
        """Scenario: Hook file exists.

        Given the sanctum plugin
        When looking for the governance policy hook
        Then it should exist in the hooks directory.
        """
        assert hook_path.exists(), f"Hook not found at {hook_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_is_valid_python(self, hook_path: Path) -> None:
        """Scenario: Hook is valid Python.

        Given the governance policy hook
        When compiling the Python code
        Then it should compile without errors.
        """
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(hook_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Python compilation failed: {result.stderr}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_contains_iron_law_statement(self, hook_content: str) -> None:
        """Scenario: Hook contains Iron Law statement.

        Given the governance policy hook
        When reading the hook content
        Then it should include the Iron Law statement.
        """
        assert "Iron Law" in hook_content
        assert "NO IMPLEMENTATION WITHOUT A FAILING TEST FIRST" in hook_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_contains_proof_of_work_step(self, hook_content: str) -> None:
        """Scenario: Hook includes proof-of-work as first step.

        Given the governance policy hook
        When reading the hook content
        Then proof-of-work should be the first step.
        """
        assert "PROOF-OF-WORK" in hook_content
        assert "MANDATORY FIRST" in hook_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_contains_iron_law_todowrite_items(self, hook_content: str) -> None:
        """Scenario: Hook mentions Iron Law TodoWrite items.

        Given the governance policy hook
        When reading the hook content
        Then it should mention iron-law TodoWrite items.
        """
        assert "iron-law-red" in hook_content
        assert "iron-law-green" in hook_content
        assert "iron-law-refactor" in hook_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_contains_self_check_table(self, hook_content: str) -> None:
        """Scenario: Hook contains Iron Law self-check table.

        Given the governance policy hook
        When reading the hook content
        Then it should include self-check questions.
        """
        assert "Self-Check" in hook_content
        assert "evidence" in hook_content.lower()
        assert "pre-conceived" in hook_content.lower()
        assert "uncertainty" in hook_content.lower()

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_contains_red_flags_table(self, hook_content: str) -> None:
        """Scenario: Hook contains red flags table.

        Given the governance policy hook
        When reading the hook content
        Then it should include red flags for rationalization detection.
        """
        assert "Red Flag" in hook_content or "red flag" in hook_content.lower()
        assert "This looks correct" in hook_content
        assert "RUN IT" in hook_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_defines_lightweight_agents(self, hook_content: str) -> None:
        """Scenario: Hook defines lightweight agents that skip full governance.

        Given the governance policy hook
        When reading the hook content
        Then it should define which agents skip full governance.
        """
        assert "LIGHTWEIGHT_AGENTS" in hook_content
        assert "code-reviewer" in hook_content
        assert "context-optimizer" in hook_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_outputs_valid_json(self, hook_path: Path) -> None:
        """Scenario: Hook outputs valid JSON.

        Given the governance policy hook
        When running it with empty stdin
        Then it should output valid JSON with additionalContext.
        """
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"

        # Parse JSON output
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
        assert "additionalContext" in output["hookSpecificOutput"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_skips_governance_for_review_agents(self, hook_path: Path) -> None:
        """Scenario: Hook skips full governance for review agents.

        Given the governance policy hook
        When running it with a review agent type
        Then it should output abbreviated context.
        """
        input_data = json.dumps({"agent_type": "code-reviewer"})
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_data,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        # Should have abbreviated context, not full governance
        assert "deferred" in context.lower() or "abbreviated" in context.lower()

    @pytest.mark.unit
    def test_hook_applies_full_governance_for_implementation_agents(
        self, hook_path: Path
    ) -> None:
        """Scenario: Hook applies full governance for implementation agents.

        Given the governance policy hook
        When running it with an implementation agent type
        Then it should output full governance policy.
        """
        input_data = json.dumps({"agent_type": "implementation-agent"})
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_data,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        # Should have full governance including Iron Law
        assert "Iron Law" in context
        assert "PROOF-OF-WORK" in context

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_handles_missing_agent_type(self, hook_path: Path) -> None:
        """Scenario: Hook handles missing agent_type gracefully.

        Given the governance policy hook
        When running it with no agent_type in input
        Then it should apply full governance (default behavior).
        """
        input_data = json.dumps({})
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_data,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"

        output = json.loads(result.stdout)
        context = output["hookSpecificOutput"]["additionalContext"]
        # Should have full governance by default
        assert "Iron Law" in context

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_hook_handles_malformed_json_gracefully(self, hook_path: Path) -> None:
        """Scenario: Hook handles malformed JSON input gracefully.

        Given the governance policy hook
        When running it with malformed JSON
        Then it should still output valid governance policy.
        """
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input="not valid json",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Hook failed: {result.stderr}"

        # Should still output valid JSON
        output = json.loads(result.stdout)
        assert "hookSpecificOutput" in output
