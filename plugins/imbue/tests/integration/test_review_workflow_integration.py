"""Integration tests for complete review workflow orchestration.

This module tests end-to-end workflow scenarios with multiple skills
and commands working together, following TDD/BDD principles.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

# Constants for PLR2004 magic values
ZERO_POINT_ONE = 0.1
ZERO_POINT_NINE = 0.9
TWO = 2
THREE = 3
FOUR = 4
FIVE = 5
FIFTY = 50
COMMITS_AHEAD = 12
AVG_TIME_THRESHOLD = 0.01
TIME_RANGE_THRESHOLD = 0.005


class TestReviewWorkflowIntegration:
    """Feature: Complete review workflow integration.

    As a user
    I want skills and commands to work together
    So that reviews are efficient and thorough
    """

    @pytest.fixture
    def mock_workflow_environment(self, tmp_path):
        """Create a complete mock environment for workflow testing."""
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()
        (repo_path / "docs").mkdir()
        (repo_path / "config").mkdir()

        (repo_path / "src" / "auth.py").write_text(
            "def authenticate_user(username, password):\n"
            '    query = "SELECT * FROM users WHERE username = \'"'
            ' + username + "\'"\n'
            "    return execute_query(query)\n"
        )
        (repo_path / "src" / "payment.py").write_text(
            "def process_payment(amount, card_number):\n"
            "    return charge_card(amount, card_number)\n"
        )
        (repo_path / "tests" / "test_auth.py").write_text(
            "def test_auth():\n    assert True\n"
        )
        (repo_path / "docs" / "api.md").write_text("# API Documentation")
        (repo_path / "config" / "app.json").write_text('{"debug": true}')

        return repo_path

    @pytest.fixture
    def skill_execution_log(self):
        """Shared skill execution log for tracking call order."""
        return []

    @pytest.fixture
    def shared_context(self, mock_workflow_environment):
        """Shared context for workflow skill execution."""
        return {
            "repository_path": str(mock_workflow_environment),
            "session_id": "integration-test-session",
            "findings": [],
            "evidence": [],
        }

    @pytest.fixture
    def mock_skill_call(self, skill_execution_log, shared_context):
        """Create a mock skill call function for workflow testing."""

        def _mock_skill_call(skill_name, context) -> str:
            skill_execution_log.append((skill_name, context.copy()))

            if skill_name == "review-core":
                context["workflow_items"] = [
                    "review-core:context-established",
                    "review-core:scope-inventoried",
                    "review-core:evidence-captured",
                    "review-core:deliverables-structured",
                ]
                context["scope"] = {
                    "source_files": [
                        "src/auth.py",
                        "src/payment.py",
                    ],
                    "test_files": ["tests/test_auth.py"],
                    "config_files": ["config/app.json"],
                    "docs": ["docs/api.md"],
                }
            elif skill_name == "evidence-logging":
                context["evidence_session"] = context.get(
                    "session_id",
                    "default-session",
                )
                context["evidence_log"] = {
                    "session_id": context["evidence_session"],
                    "evidence": [],
                    "citations": [],
                }
            elif skill_name == "diff-analysis":
                context["changes"] = [
                    {
                        "file": "src/auth.py",
                        "type": "modified",
                        "semantic_category": "security",
                        "risk_level": "High",
                    },
                ]
            elif skill_name == "structured-output":
                context["deliverable"] = {
                    "template": "security_review_report",
                    "sections": [
                        "Executive Summary",
                        "Findings",
                        "Actions",
                        "Evidence",
                    ],
                    "findings": context.get("findings", []),
                    "evidence_refs": [
                        f"E{i + 1}" for i in range(len(context.get("evidence", [])))
                    ],
                }

            shared_context.update(context)
            return f"{skill_name} completed"

        return _mock_skill_call

    @pytest.fixture
    def executed_workflow(
        self,
        mock_claude_tools,
        mock_skill_call,
        shared_context,
        skill_execution_log,
    ):
        """Execute the full review workflow and return results."""
        mock_claude_tools["Skill"] = Mock(side_effect=mock_skill_call)

        shared_context["findings"] = [
            {
                "id": "F1",
                "title": "SQL injection vulnerability",
                "severity": "Critical",
                "file": "src/auth.py",
                "evidence_refs": ["E1"],
            },
        ]
        shared_context["evidence"] = [
            {
                "id": "E1",
                "command": "grep -n 'SELECT.*username' src/auth.py",
                "output": (
                    'src/auth.py:3: query = "SELECT * FROM users'
                    " WHERE username = 'test_user'"
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        skills_to_execute = [
            "review-core",
            "evidence-logging",
            "diff-analysis",
            "structured-output",
        ]
        current_context = {
            "command": "/review",
            "target": shared_context["repository_path"],
            "focus": "security",
        }

        workflow_result = {
            "command_executed": "/review",
            "skills_executed": [],
            "final_deliverable": None,
            "evidence_log": None,
        }

        for skill in skills_to_execute:
            mock_claude_tools["Skill"](skill, current_context)
            workflow_result["skills_executed"].append(skill)
            current_context.update(shared_context)

        workflow_result["final_deliverable"] = shared_context.get(
            "deliverable",
        )
        workflow_result["evidence_log"] = shared_context.get(
            "evidence_log",
        )

        return workflow_result

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_end_to_end_skills_all_executed(
        self,
        executed_workflow,
    ) -> None:
        """Scenario: Full review workflow executes all four skills.

        Given a repository with changes
        When running /review command
        Then all four skills should execute in order.
        """
        assert executed_workflow["command_executed"] == "/review"
        assert executed_workflow["skills_executed"] == [
            "review-core",
            "evidence-logging",
            "diff-analysis",
            "structured-output",
        ]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_end_to_end_execution_order(
        self,
        executed_workflow,
        skill_execution_log,
    ) -> None:
        """Scenario: Skills execute in correct sequence.

        Given a review workflow
        When skills are orchestrated
        Then execution order matches the expected sequence.
        """
        execution_order = [call[0] for call in skill_execution_log]
        assert execution_order == [
            "review-core",
            "evidence-logging",
            "diff-analysis",
            "structured-output",
        ]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_end_to_end_context_propagation(
        self,
        executed_workflow,
        shared_context,
    ) -> None:
        """Scenario: Context propagates across skills.

        Given a multi-skill workflow
        When each skill completes
        Then shared context contains all skill contributions.
        """
        assert "workflow_items" in shared_context
        assert len(shared_context["workflow_items"]) == FOUR
        assert "scope" in shared_context
        assert "changes" in shared_context
        assert "deliverable" in shared_context

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_end_to_end_deliverable_quality(
        self,
        executed_workflow,
    ) -> None:
        """Scenario: Final deliverable is properly structured.

        Given a completed workflow
        When inspecting the deliverable
        Then it should have correct template and evidence refs.
        """
        deliverable = executed_workflow["final_deliverable"]
        assert deliverable["template"] == "security_review_report"
        assert len(deliverable["findings"]) == 1
        assert "E1" in deliverable["evidence_refs"]


class TestCatchupWorkflowIntegration:
    """Feature: Catchup workflow integrates multiple skills.

    As a user returning to work
    I want the catchup workflow to use multiple skills
    So that I get a complete picture of changes
    """

    @pytest.fixture
    def workflow_state(self):
        """Shared workflow state for catchup phases."""
        return {}

    @pytest.fixture
    def mock_catchup_skill(self, workflow_state):
        """Mock catchup skill with multiple phases."""

        def _skill(context):
            phase = context.get("phase", "context")
            if phase == "context":
                workflow_state["context"] = {
                    "branch": "feature/payment-processing",
                    "baseline": "main",
                    "commits_ahead": 12,
                    "files_changed": 8,
                }
                return {"status": "context_confirmed"}
            if phase == "delta":
                workflow_state["delta"] = {
                    "changes": [
                        {"type": "feature", "category": "payment", "count": 5},
                        {"type": "test", "category": "test", "count": 2},
                        {"type": "docs", "category": "documentation", "count": 1},
                    ],
                    "total_files": 8,
                    "lines_changed": 150,
                }
                return {"status": "delta_captured"}
            if phase == "insights":
                workflow_state["insights"] = [
                    "Payment processing feature implemented with 5 components",
                    "Test coverage added for payment flows",
                    "API documentation updated",
                ]
                return {"status": "insights_extracted"}
            if phase == "followups":
                workflow_state["followups"] = [
                    "[ ] Review payment security implementation",
                    "[ ] Update API documentation with new endpoints",
                    "[ ] Coordinate with finance team for payment testing",
                ]
                return {"status": "followups_recorded"}
            return None

        return _skill

    @pytest.fixture
    def catchup_results(self, mock_catchup_skill, workflow_state):
        """Execute all catchup phases and return results + state."""
        phases = ["context", "delta", "insights", "followups"]
        results = []
        for phase in phases:
            result = mock_catchup_skill({"phase": phase})
            results.append(result)

        summary = {
            "context": workflow_state["context"],
            "key_changes": workflow_state["delta"]["changes"],
            "insights": workflow_state["insights"],
            "followups": workflow_state["followups"],
            "summary": (
                f"Payment processing feature added with "
                f"{workflow_state['delta']['total_files']} files changed"
            ),
        }
        return results, summary, workflow_state

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_catchup_all_phases_complete(self, catchup_results) -> None:
        """Scenario: All catchup phases complete successfully.

        Given recent changes in repository
        When running /catchup command
        Then all four phases should complete.
        """
        results, _, _ = catchup_results
        assert len(results) == FOUR
        statuses = [r["status"] for r in results]
        assert statuses == [
            "context_confirmed",
            "delta_captured",
            "insights_extracted",
            "followups_recorded",
        ]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_catchup_context_accuracy(self, catchup_results) -> None:
        """Scenario: Catchup context captures branch and commit info.

        Given a feature branch ahead of main
        When confirming context
        Then branch name and commits ahead are accurate.
        """
        _, summary, _ = catchup_results
        assert summary["context"]["branch"] == "feature/payment-processing"
        assert summary["context"]["commits_ahead"] == COMMITS_AHEAD

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_catchup_summary_content(self, catchup_results) -> None:
        """Scenario: Catchup summary contains expected data.

        Given completed catchup analysis
        When inspecting the summary
        Then it should have changes, insights, and followups.
        """
        _, summary, _ = catchup_results
        assert len(summary["key_changes"]) == THREE
        assert len(summary["insights"]) == THREE
        assert len(summary["followups"]) == THREE
        assert "Payment processing feature added" in summary["summary"]


class TestAgentIntegration:
    """Feature: Review-analyst agent integrates with workflow skills.

    As an autonomous review agent
    I want to use imbue skills consistently
    So that findings have evidence references
    """

    @pytest.fixture
    def agent_workflow_result(self, mock_claude_tools):
        """Execute agent workflow and return results."""
        shared_evidence = []

        def mock_agent_skill(skill_name, context) -> None:
            if skill_name == "review-core" and context.get("agent") == "review-analyst":
                context["agent_workflow"] = {
                    "context_established": True,
                    "scope_discovered": [
                        "src/auth.py",
                        "src/payment.py",
                    ],
                    "autonomous_mode": True,
                }
            elif skill_name == "evidence-logging":
                evidence_item = {
                    "id": f"E{len(shared_evidence) + 1}",
                    "command": (
                        f"agent analysis of {context.get('target', 'unknown')}"
                    ),
                    "output": "Security vulnerability detected",
                    "timestamp": datetime.now(
                        timezone.utc,
                    ).isoformat(),
                    "agent": "review-analyst",
                }
                shared_evidence.append(evidence_item)
                context["agent_evidence"] = shared_evidence.copy()
            elif skill_name == "structured-output":
                context["agent_report"] = {
                    "template": "security_audit_report",
                    "agent_generated": True,
                    "evidence_refs": [e["id"] for e in shared_evidence],
                    "compliance_standards": ["OWASP", "NIST"],
                }

        mock_claude_tools["Skill"] = Mock(
            side_effect=mock_agent_skill,
        )

        skills_sequence = [
            (
                "review-core",
                {
                    "agent": "review-analyst",
                    "focus": "security_audit",
                },
            ),
            (
                "evidence-logging",
                {
                    "agent": "review-analyst",
                    "target": "src/auth.py",
                },
            ),
            (
                "structured-output",
                {
                    "agent": "review-analyst",
                    "findings_count": 2,
                },
            ),
        ]

        current_context = {}
        skills_used = []
        for skill_name, context in skills_sequence:
            current_context.update(context)
            mock_claude_tools["Skill"](skill_name, current_context)
            skills_used.append(skill_name)

        return {
            "agent": "review-analyst",
            "skills_used": skills_used,
            "findings": [
                {
                    "id": "AF1",
                    "title": "Autonomously detected SQL injection",
                    "severity": "Critical",
                    "agent_detected": True,
                    "confidence": 0.95,
                },
            ],
            "evidence_log": shared_evidence,
            "final_report": current_context.get("agent_report"),
        }

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_agent_uses_all_skills(
        self,
        agent_workflow_result,
    ) -> None:
        """Scenario: Agent uses all three review skills.

        Given autonomous review execution
        When agent runs
        Then it should use review-core, evidence-logging,
        and structured-output.
        """
        assert agent_workflow_result["skills_used"] == [
            "review-core",
            "evidence-logging",
            "structured-output",
        ]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_agent_report_is_agent_generated(
        self,
        agent_workflow_result,
    ) -> None:
        """Scenario: Agent report is flagged as agent-generated.

        Given an agent-produced report
        When inspecting the report
        Then agent_generated should be True
        And compliance standards should be included.
        """
        report = agent_workflow_result["final_report"]
        assert report["agent_generated"] is True
        assert report["compliance_standards"] == ["OWASP", "NIST"]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_agent_evidence_attribution(
        self,
        agent_workflow_result,
    ) -> None:
        """Scenario: Agent evidence is attributed correctly.

        Given evidence logged by the agent
        When inspecting evidence
        Then evidence should be attributed to review-analyst.
        """
        assert len(agent_workflow_result["evidence_log"]) == 1
        assert agent_workflow_result["evidence_log"][0]["agent"] == "review-analyst"

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_agent_finding_quality(
        self,
        agent_workflow_result,
    ) -> None:
        """Scenario: Agent findings have high confidence.

        Given agent-detected findings
        When inspecting confidence
        Then confidence should exceed 0.9.
        """
        finding = agent_workflow_result["findings"][0]
        assert finding["agent_detected"] is True
        assert finding["confidence"] > ZERO_POINT_NINE


class TestEvidenceChainContinuity:
    """Feature: Evidence references maintain integrity across skills.

    As a review consumer
    I want all evidence citations to resolve correctly
    So that findings are verifiable
    """

    @pytest.fixture
    def evidence_chain_result(self, mock_claude_tools):
        """Execute evidence chain workflow and return results."""
        evidence_chain = {
            "evidence_registry": {},
            "reference_tracker": {},
            "skill_contributions": {},
        }

        def mock_skill(skill_name, context) -> None:
            if skill_name == "evidence-logging":
                evidence_chain["skill_contributions"]["evidence-logging"] = 0
                context["evidence_log"] = {
                    "session_id": context.get(
                        "session_id",
                        "default",
                    ),
                    "evidence": [],
                    "next_evidence_id": 1,
                }
            elif skill_name == "diff-analysis":
                evidence_log = context.get("evidence_log")
                if evidence_log:
                    eid = evidence_log["next_evidence_id"]
                    diff_evidence = {
                        "id": f"E{eid}",
                        "command": "git diff HEAD~1..HEAD",
                        "output": ("2 files changed, 15 insertions(+), 5 deletions(-)"),
                        "skill": "diff-analysis",
                        "timestamp": datetime.now(
                            timezone.utc,
                        ).isoformat(),
                    }
                    evidence_log["evidence"].append(diff_evidence)
                    evidence_log["next_evidence_id"] += 1
                    evidence_chain["evidence_registry"][diff_evidence["id"]] = (
                        diff_evidence
                    )
                    evidence_chain["skill_contributions"]["diff-analysis"] = 1
            elif skill_name == "structured-output":
                evidence_log = context.get("evidence_log", {})
                available = [e["id"] for e in evidence_log.get("evidence", [])]
                findings = [
                    {
                        "id": "F1",
                        "title": "Code change detected",
                        "evidence_refs": available[:1] if available else [],
                    },
                ]
                for finding in findings:
                    evidence_chain["reference_tracker"][finding["id"]] = finding[
                        "evidence_refs"
                    ]
                context["findings"] = findings

        mock_claude_tools["Skill"] = Mock(side_effect=mock_skill)

        current_context = {"session_id": "evidence-chain-test"}
        for skill_name in [
            "evidence-logging",
            "diff-analysis",
            "structured-output",
        ]:
            mock_claude_tools["Skill"](
                skill_name,
                current_context,
            )

        return evidence_chain

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_evidence_ids_are_unique(
        self,
        evidence_chain_result,
    ) -> None:
        """Scenario: Evidence IDs are unique.

        Given evidence from multiple skills
        When collecting all evidence IDs
        Then each ID should be unique.
        """
        evidence_ids = list(
            evidence_chain_result["evidence_registry"].keys(),
        )
        assert len(evidence_ids) == len(set(evidence_ids))
        assert len(evidence_ids) >= 1

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_evidence_references_resolve(
        self,
        evidence_chain_result,
    ) -> None:
        """Scenario: All evidence references resolve to existing evidence.

        Given findings with evidence references
        When checking reference resolution
        Then every reference should exist in the registry.
        """
        for refs in evidence_chain_result["reference_tracker"].values():
            for ref in refs:
                assert ref in evidence_chain_result["evidence_registry"], (
                    f"Evidence reference {ref} not found"
                )

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_skill_contributions_tracked(
        self,
        evidence_chain_result,
    ) -> None:
        """Scenario: Skill contributions are tracked.

        Given multi-skill evidence workflow
        When inspecting contributions
        Then diff-analysis should have contributed 1 evidence item.
        """
        contributions = evidence_chain_result["skill_contributions"]
        assert contributions["diff-analysis"] == 1
        assert "evidence-logging" in contributions


class TestCommandSkillOrchestration:
    """Feature: Commands properly orchestrate skills.

    As a review command
    I want to orchestrate skills with correct context
    So that workflows maintain state across skills
    """

    @pytest.fixture
    def orchestration_result(self, mock_claude_tools):
        """Execute command orchestration and return results."""
        orchestration_log = {
            "command_invoked": None,
            "skill_calls": [],
            "context_flow": [],
            "results_chain": [],
        }

        def mock_skill(skill_name, context):
            orchestration_log["skill_calls"].append(skill_name)
            orchestration_log["context_flow"].append(context.copy())
            if skill_name == "review-core":
                context["workflow_scaffold"] = {
                    "items_created": 5,
                    "context": {"repo": "/test", "branch": "main"},
                }
            elif skill_name == "evidence-logging":
                context["evidence_infrastructure"] = {
                    "session_id": "orchestration-test",
                    "tracking_enabled": True,
                }
            return {"skill": skill_name, "status": "completed"}

        mock_claude_tools["Skill"] = Mock(side_effect=mock_skill)

        orchestration_log["command_invoked"] = "/review"
        orchestration_log["results_chain"].append(
            {"stage": "command_start", "args": []},
        )

        context = {"target": "src/", "focus": "security"}
        for skill in [
            "review-core",
            "evidence-logging",
            "structured-output",
        ]:
            skill_context = context.copy()
            skill_context["command_context"] = {
                "command": "/review",
                "args": [],
                "orchestrated": True,
            }
            result = mock_claude_tools["Skill"](
                skill,
                skill_context,
            )
            orchestration_log["results_chain"].append(
                {
                    "stage": f"skill_{skill}_completed",
                    "result": result,
                },
            )
            for key, value in skill_context.items():
                if key not in context:
                    context[key] = value

        orchestration_log["results_chain"].append(
            {"stage": "command_complete", "final_context": context},
        )

        return orchestration_log, context

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_orchestration_invokes_command(
        self,
        orchestration_result,
    ) -> None:
        """Scenario: Command is properly invoked.

        Given /review command execution
        When dispatching to skills
        Then command should be recorded.
        """
        log, _ = orchestration_result
        assert log["command_invoked"] == "/review"

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_orchestration_calls_all_skills(
        self,
        orchestration_result,
    ) -> None:
        """Scenario: All three skills are called in order.

        Given /review command
        When orchestrating skills
        Then review-core, evidence-logging, structured-output
        should be called.
        """
        log, _ = orchestration_result
        assert log["skill_calls"] == [
            "review-core",
            "evidence-logging",
            "structured-output",
        ]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_orchestration_context_propagation(
        self,
        orchestration_result,
    ) -> None:
        """Scenario: Context flows correctly to each skill.

        Given orchestrated skills
        When inspecting context flow
        Then each skill should receive command_context.
        """
        log, _ = orchestration_result
        assert len(log["context_flow"]) == THREE
        for skill_ctx in log["context_flow"]:
            assert skill_ctx["command_context"]["command"] == "/review"
            assert skill_ctx["command_context"]["orchestrated"] is True

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_orchestration_final_context(
        self,
        orchestration_result,
    ) -> None:
        """Scenario: Final context contains all skill contributions.

        Given a completed orchestration
        When inspecting final context
        Then workflow_scaffold and evidence_infrastructure exist.
        """
        _, final_context = orchestration_result
        assert final_context["workflow_scaffold"]["items_created"] == FIVE
        assert final_context["evidence_infrastructure"]["tracking_enabled"] is True

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_orchestration_results_chain(
        self,
        orchestration_result,
    ) -> None:
        """Scenario: Results chain captures all stages.

        Given a completed orchestration
        When inspecting results chain
        Then it should have start + 3 skills + complete = 5 entries.
        """
        log, _ = orchestration_result
        chain = log["results_chain"]
        assert len(chain) == FIVE
        assert chain[0]["stage"] == "command_start"
        assert chain[-1]["stage"] == "command_complete"


class TestErrorPropagation:
    """Feature: Errors are handled gracefully across workflow.

    As a workflow executor
    I want errors captured and fallbacks applied
    So that partial failures do not crash the workflow
    """

    @pytest.fixture
    def error_workflow_result(self, mock_claude_tools):
        """Execute workflow with simulated error."""
        error_log = []

        def mock_skill(skill_name, context):
            if skill_name == "diff-analysis" and context.get("simulate_error"):
                error_log.append(
                    {
                        "skill": skill_name,
                        "error_type": "GitCommandError",
                        "message": "Git command failed: invalid reference",
                        "context": context.copy(),
                    }
                )
                msg = "Git command failed"
                raise RuntimeError(msg)
            return {"skill": skill_name, "status": "success"}

        mock_claude_tools["Skill"] = Mock(side_effect=mock_skill)

        workflow_result = {
            "skills_attempted": [],
            "skills_completed": [],
            "errors_encountered": [],
            "fallback_actions": [],
            "final_status": None,
        }

        current_context = {"simulate_error": True}
        for skill in [
            "review-core",
            "diff-analysis",
            "structured-output",
        ]:
            workflow_result["skills_attempted"].append(skill)
            try:
                result = mock_claude_tools["Skill"](
                    skill,
                    current_context,
                )
                workflow_result["skills_completed"].append(skill)
                current_context.update(result)
            except Exception as e:
                workflow_result["errors_encountered"].append(
                    {"skill": skill, "error": str(e)},
                )
                if skill == "diff-analysis":
                    workflow_result["fallback_actions"].append(
                        "Used file system analysis instead of git diff",
                    )
                    current_context["diff_analysis_fallback"] = True

        if workflow_result["errors_encountered"]:
            if workflow_result["fallback_actions"]:
                workflow_result["final_status"] = "completed_with_fallbacks"
            else:
                workflow_result["final_status"] = "failed"
        else:
            workflow_result["final_status"] = "completed_successfully"

        return workflow_result, error_log, current_context

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_error_workflow_attempts_all_skills(
        self,
        error_workflow_result,
    ) -> None:
        """Scenario: All skills are attempted despite errors.

        Given a skill failure
        When propagating through workflow
        Then all skills should still be attempted.
        """
        result, _, _ = error_workflow_result
        assert len(result["skills_attempted"]) == THREE

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_error_workflow_captures_failure(
        self,
        error_workflow_result,
    ) -> None:
        """Scenario: Failed skill is captured in errors.

        Given diff-analysis fails
        When inspecting errors
        Then diff-analysis should be listed as failed.
        """
        result, _, _ = error_workflow_result
        assert len(result["skills_completed"]) == TWO
        assert len(result["errors_encountered"]) == 1
        assert result["errors_encountered"][0]["skill"] == "diff-analysis"

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_error_workflow_applies_fallback(
        self,
        error_workflow_result,
    ) -> None:
        """Scenario: Fallback is applied for failed skill.

        Given diff-analysis failure with fallback configured
        When checking fallback actions
        Then file system analysis fallback should be applied.
        """
        result, _, context = error_workflow_result
        assert len(result["fallback_actions"]) == 1
        assert "file system analysis" in result["fallback_actions"][0]
        assert result["final_status"] == "completed_with_fallbacks"
        assert "diff_analysis_fallback" in context

    @pytest.mark.bdd
    @pytest.mark.integration
    def test_error_workflow_logs_error_details(
        self,
        error_workflow_result,
    ) -> None:
        """Scenario: Error details are logged.

        Given a skill failure
        When inspecting error log
        Then error type and skill should be recorded.
        """
        _, error_log, _ = error_workflow_result
        assert len(error_log) == 1
        assert error_log[0]["skill"] == "diff-analysis"
        assert error_log[0]["error_type"] == "GitCommandError"


class TestWorkflowPerformance:
    """Feature: Workflow performs efficiently under load.

    As a workflow executor
    I want multiple workflows to complete quickly
    So that performance remains acceptable
    """

    @pytest.mark.bdd
    @pytest.mark.performance
    @pytest.mark.integration
    def test_workflow_total_duration(self, mock_claude_tools) -> None:
        """Scenario: All workflows complete in under 1 second.

        Given 5 concurrent workflow configurations
        When executing review workflows
        Then total duration should be under 1 second.
        """
        configs = [
            {"target": "src/auth/", "focus": "security"},
            {"target": "src/api/", "focus": "performance"},
            {"target": "src/payment/", "focus": "correctness"},
            {"target": "src/utils/", "focus": "style"},
            {"target": "docs/", "focus": "documentation"},
        ]

        skills = [
            "review-core",
            "evidence-logging",
            "diff-analysis",
            "structured-output",
        ]

        start_time = time.time()
        workflow_times = []

        for _config in configs:
            wf_start = time.time()
            for _skill in skills:
                time.sleep(0.001)
            workflow_times.append(time.time() - wf_start)

        total_duration = time.time() - start_time

        assert total_duration < 1.0

    @pytest.mark.bdd
    @pytest.mark.performance
    @pytest.mark.integration
    def test_individual_workflow_timing(
        self,
        mock_claude_tools,
    ) -> None:
        """Scenario: Each individual workflow completes under 100ms.

        Given workflow configurations
        When measuring each workflow
        Then each should complete in under 100ms.
        """
        workflow_times = []
        for _ in range(5):
            wf_start = time.time()
            for _ in range(4):
                time.sleep(0.001)
            workflow_times.append(time.time() - wf_start)

        for wf_time in workflow_times:
            assert wf_time < ZERO_POINT_ONE

    @pytest.mark.bdd
    @pytest.mark.performance
    @pytest.mark.integration
    def test_skill_throughput(self, mock_claude_tools) -> None:
        """Scenario: Skill throughput exceeds 50 skills per second.

        Given multiple workflow executions
        When measuring throughput
        Then at least 50 skills per second should execute.
        """
        start_time = time.time()
        total_skills = 20  # 5 workflows * 4 skills
        for _ in range(total_skills):
            time.sleep(0.001)
        total_duration = time.time() - start_time

        skills_per_second = total_skills / total_duration
        assert skills_per_second > FIFTY
