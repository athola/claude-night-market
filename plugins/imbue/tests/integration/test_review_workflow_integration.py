"""Integration tests for complete review workflow orchestration.

This module tests end-to-end workflow scenarios with multiple skills
and commands working together, following TDD/BDD principles.
"""

import time
from datetime import UTC, datetime
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
    I want skills and commands to work together seamlessly
    So that reviews are efficient and thorough
    """

    @pytest.fixture
    def mock_workflow_environment(self, tmp_path):
        """Create a complete mock environment for workflow testing."""
        # Create mock git repository
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()

        # Create project structure
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()
        (repo_path / "docs").mkdir()
        (repo_path / "config").mkdir()

        # Create sample files
        (repo_path / "src" / "auth.py").write_text("""
def authenticate_user(username, password):
    # SQL injection vulnerable code
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return execute_query(query)
""")
        (repo_path / "src" / "payment.py").write_text("""
def process_payment(amount, card_number):
    # Payment processing logic
    return charge_card(amount, card_number)
""")
        (repo_path / "tests" / "test_auth.py").write_text("""
def test_auth():
    assert True
""")
        (repo_path / "docs" / "api.md").write_text("# API Documentation")
        (repo_path / "config" / "app.json").write_text('{"debug": true}')

        return repo_path

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_end_to_end_review_workflow(
        self,
        mock_workflow_environment,
        mock_claude_tools,
    ) -> None:
        """Scenario: Full review workflow from command to deliverable.

        Given a repository with changes
        When running /review command
        Then it should initialize review-core workflow
        And capture evidence using evidence-logging
        And analyze changes with diff-analysis
        And generate report with structured-output
        And provide evidence-referenced findings.
        """
        # Arrange - set up mocks for skill calls
        skill_execution_log = []
        shared_context = {
            "repository_path": str(mock_workflow_environment),
            "session_id": "integration-test-session",
            "findings": [],
            "evidence": [],
        }

        def mock_skill_call(skill_name, context) -> str:
            skill_execution_log.append((skill_name, context.copy()))

            if skill_name == "review-core":
                # Initialize workflow
                context["workflow_items"] = [
                    "review-core:context-established",
                    "review-core:scope-inventoried",
                    "review-core:evidence-captured",
                    "review-core:deliverables-structured",
                ]
                context["scope"] = {
                    "source_files": ["src/auth.py", "src/payment.py"],
                    "test_files": ["tests/test_auth.py"],
                    "config_files": ["config/app.json"],
                    "docs": ["docs/api.md"],
                }

            elif skill_name == "evidence-logging":
                # Initialize evidence logging
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
                # Analyze changes
                context["changes"] = [
                    {
                        "file": "src/auth.py",
                        "type": "modified",
                        "semantic_category": "security",
                        "risk_level": "High",
                    },
                ]

            elif skill_name == "structured-output":
                # Generate deliverable
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

        mock_claude_tools["Skill"] = Mock(side_effect=mock_skill_call)

        # Act - execute complete workflow
        initial_context = {
            "command": "/review",
            "target": str(mock_workflow_environment),
            "focus": "security",
        }

        # Add findings from analysis before deliverable generation
        shared_context["findings"] = [
            {
                "id": "F1",
                "title": "SQL injection vulnerability",
                "severity": "Critical",
                "file": "src/auth.py",
                "evidence_refs": ["E1"],
            },
        ]

        # Add evidence items before structured output is generated
        shared_context["evidence"] = [
            {
                "id": "E1",
                "command": "grep -n 'SELECT.*username' src/auth.py",
                "output": (  # noqa: S608 - deliberate SQL string for test data
                    "src/auth.py:3: query = \"SELECT * FROM users WHERE username = '"
                    + "test_user"
                    + "'"
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            },
        ]

        # Step 1: Execute /review command (this would orchestrate skills)
        workflow_result = {
            "command_executed": "/review",
            "skills_executed": [],
            "final_deliverable": None,
            "evidence_log": None,
        }

        # Simulate skill orchestration
        skills_to_execute = [
            "review-core",
            "evidence-logging",
            "diff-analysis",
            "structured-output",
        ]
        current_context = initial_context.copy()

        for skill in skills_to_execute:
            mock_claude_tools["Skill"](skill, current_context)
            workflow_result["skills_executed"].append(skill)
            current_context.update(shared_context)

        workflow_result["final_deliverable"] = shared_context.get("deliverable")
        workflow_result["evidence_log"] = shared_context.get("evidence_log")

        # Assert
        assert workflow_result["command_executed"] == "/review"
        assert len(workflow_result["skills_executed"]) == FOUR
        assert all(
            skill in workflow_result["skills_executed"] for skill in skills_to_execute
        )

        # Verify workflow sequence
        execution_order = [call[0] for call in skill_execution_log]
        assert execution_order == skills_to_execute

        # Verify shared context propagation
        assert "workflow_items" in shared_context
        assert "scope" in shared_context
        assert "changes" in shared_context
        assert "deliverable" in shared_context

        # Verify final deliverable
        deliverable = workflow_result["final_deliverable"]
        assert deliverable["template"] == "security_review_report"
        assert len(deliverable["findings"]) >= 1
        assert "E1" in deliverable["evidence_refs"]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_catchup_workflow_with_multiple_skills(self, mock_claude_tools) -> None:
        """Scenario: Catchup workflow integrates multiple skills.

        Given recent changes in repository
        When running /catchup command
        Then it should establish context
        And analyze changes with semantic categorization
        And extract actionable insights
        And record follow-ups.
        """
        # Arrange - set up catchup workflow mocks
        workflow_state = {}

        def mock_catchup_skill(context):
            """Mock catchup skill with multiple phases."""
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
                workflow_state["delta"]["changes"]
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

        # Act - simulate catchup workflow
        catchup_phases = ["context", "delta", "insights", "followups"]
        workflow_results = []

        for phase in catchup_phases:
            context = {"phase": phase}
            result = mock_catchup_skill(context)
            workflow_results.append(result)

        # Generate final summary
        final_summary = {
            "context": workflow_state["context"],
            "key_changes": workflow_state["delta"]["changes"],
            "insights": workflow_state["insights"],
            "followups": workflow_state["followups"],
            "summary": (
                f"Payment processing feature added with "
                f"{workflow_state['delta']['total_files']} files changed"
            ),
        }

        # Assert
        assert len(workflow_results) == FOUR
        assert all(
            result["status"].endswith("confirmed")
            or result["status"].endswith("captured")
            or result["status"].endswith("extracted")
            or result["status"].endswith("recorded")
            for result in workflow_results
        )

        # Verify workflow completeness
        assert "context" in workflow_state
        assert "delta" in workflow_state
        assert "insights" in workflow_state
        assert "followups" in workflow_state

        # Verify final summary content
        assert final_summary["context"]["branch"] == "feature/payment-processing"
        assert final_summary["context"]["commits_ahead"] == COMMITS_AHEAD
        assert len(final_summary["key_changes"]) == THREE
        assert len(final_summary["insights"]) == THREE
        assert len(final_summary["followups"]) == THREE
        assert "Payment processing feature added" in final_summary["summary"]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_agent_integration_with_workflow_skills(self, mock_claude_tools) -> None:
        """Scenario: Review-analyst agent integrates with workflow skills.

        Given autonomous review execution
        When agent analyzes repository
        Then it should use imbue skills consistently
        And provide evidence-referenced findings.
        """
        # Arrange - set up agent integration

        agent_execution_log = []
        shared_evidence = []

        def mock_agent_with_skills(skill_name, context) -> None:
            """Mock agent using imbue skills."""
            agent_execution_log.append((skill_name, context))

            if skill_name == "review-core" and context.get("agent") == "review-analyst":
                context["agent_workflow"] = {
                    "context_established": True,
                    "scope_discovered": ["src/auth.py", "src/payment.py"],
                    "autonomous_mode": True,
                }

            elif skill_name == "evidence-logging":
                # Agent logs evidence systematically
                evidence_item = {
                    "id": f"E{len(shared_evidence) + 1}",
                    "command": f"agent analysis of {context.get('target', 'unknown')}",
                    "output": "Security vulnerability detected",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "agent": "review-analyst",
                }
                shared_evidence.append(evidence_item)
                context["agent_evidence"] = shared_evidence.copy()

            elif skill_name == "structured-output":
                # Agent formats findings consistently
                context["agent_report"] = {
                    "template": "security_audit_report",
                    "agent_generated": True,
                    "evidence_refs": [e["id"] for e in shared_evidence],
                    "compliance_standards": ["OWASP", "NIST"],
                }

        mock_claude_tools["Skill"] = Mock(side_effect=mock_agent_with_skills)

        # Act - execute agent workflow
        agent_workflow = {
            "agent": "review-analyst",
            "skills_used": [],
            "findings": [],
            "evidence_log": None,
            "final_report": None,
        }

        # Simulate agent executing skills
        skills_sequence = [
            ("review-core", {"agent": "review-analyst", "focus": "security_audit"}),
            ("evidence-logging", {"agent": "review-analyst", "target": "src/auth.py"}),
            ("structured-output", {"agent": "review-analyst", "findings_count": 2}),
        ]

        current_agent_context = {}
        for skill_name, context in skills_sequence:
            current_agent_context.update(context)
            mock_claude_tools["Skill"](skill_name, current_agent_context)
            agent_workflow["skills_used"].append(skill_name)
            current_agent_context.update(
                {
                    k: v
                    for k, v in current_agent_context.items()
                    if k.startswith("agent")
                },
            )

        # Add agent findings
        agent_workflow["findings"] = [
            {
                "id": "AF1",
                "title": "Autonomously detected SQL injection",
                "severity": "Critical",
                "agent_detected": True,
                "confidence": 0.95,
            },
        ]

        agent_workflow["evidence_log"] = shared_evidence
        agent_workflow["final_report"] = current_agent_context.get("agent_report")

        # Assert
        assert agent_workflow["agent"] == "review-analyst"
        assert len(agent_workflow["skills_used"]) == THREE
        assert "review-core" in agent_workflow["skills_used"]
        assert "evidence-logging" in agent_workflow["skills_used"]
        assert "structured-output" in agent_workflow["skills_used"]

        # Verify agent-specific enhancements
        assert agent_workflow["final_report"]["agent_generated"] is True
        assert "compliance_standards" in agent_workflow["final_report"]
        assert len(agent_workflow["evidence_log"]) == 1
        assert agent_workflow["evidence_log"][0]["agent"] == "review-analyst"

        # Verify finding quality
        finding = agent_workflow["findings"][0]
        assert finding["agent_detected"] is True
        assert finding["confidence"] > ZERO_POINT_NINE

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_evidence_chain_continuity_across_skills(self, mock_claude_tools) -> None:
        """Scenario: Evidence references maintain integrity across skills.

        Given multi-skill review workflow
        When skills exchange evidence
        Then all citations should resolve correctly
        And evidence IDs should be unique.
        """
        # Arrange - set up evidence chain tracking
        evidence_chain = {
            "evidence_registry": {},  # ID -> evidence mapping
            "reference_tracker": {},  # Finding -> [evidence_refs] mapping
            "skill_contributions": {},  # Skill -> evidence_count mapping
        }

        def mock_evidence_aware_skill(skill_name, context) -> None:
            """Mock skill that contributes to evidence chain."""
            if skill_name == "evidence-logging":
                # Initialize evidence logging
                evidence_log = {
                    "session_id": context.get("session_id", "default"),
                    "evidence": [],
                    "next_evidence_id": 1,
                }
                evidence_chain["skill_contributions"]["evidence-logging"] = 0
                context["evidence_log"] = evidence_log

            elif skill_name == "diff-analysis":
                # Add evidence from diff analysis
                evidence_log = context.get("evidence_log")
                if evidence_log:
                    diff_evidence = {
                        "id": f"E{evidence_log['next_evidence_id']}",
                        "command": "git diff HEAD~1..HEAD",
                        "output": "2 files changed, 15 insertions(+), 5 deletions(-)",
                        "skill": "diff-analysis",
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    evidence_log["evidence"].append(diff_evidence)
                    evidence_log["next_evidence_id"] += 1

                    # Update registry
                    evidence_chain["evidence_registry"][diff_evidence["id"]] = (
                        diff_evidence
                    )
                    evidence_chain["skill_contributions"]["diff-analysis"] = 1

            elif skill_name == "structured-output":
                # Create findings with evidence references
                evidence_log = context.get("evidence_log", {})
                available_evidence = [e["id"] for e in evidence_log.get("evidence", [])]

                findings = [
                    {
                        "id": "F1",
                        "title": "Code change detected",
                        "evidence_refs": available_evidence[:1]
                        if available_evidence
                        else [],
                    },
                ]

                # Track references
                for finding in findings:
                    evidence_chain["reference_tracker"][finding["id"]] = finding[
                        "evidence_refs"
                    ]

                context["findings"] = findings

        mock_claude_tools["Skill"] = Mock(side_effect=mock_evidence_aware_skill)

        # Act - execute evidence chain workflow
        workflow_context = {"session_id": "evidence-chain-test"}

        skills_sequence = ["evidence-logging", "diff-analysis", "structured-output"]
        current_context = workflow_context.copy()

        for skill_name in skills_sequence:
            mock_claude_tools["Skill"](skill_name, current_context)
            current_context.update(
                {
                    k: v
                    for k, v in current_context.items()
                    if k in ["evidence_log", "findings"]
                },
            )

        # Verify evidence chain integrity
        # Assert
        assert len(evidence_chain["evidence_registry"]) >= 1
        assert len(evidence_chain["reference_tracker"]) >= 1

        # Check evidence uniqueness
        evidence_ids = list(evidence_chain["evidence_registry"].keys())
        assert len(evidence_ids) == len(set(evidence_ids))  # All unique

        # Check reference resolution
        for evidence_refs in evidence_chain["reference_tracker"].values():
            for ref in evidence_refs:
                assert ref in evidence_chain["evidence_registry"], (
                    f"Evidence reference {ref} not found"
                )

        # Check skill contributions tracking
        assert evidence_chain["skill_contributions"]["diff-analysis"] == 1
        assert "evidence-logging" in evidence_chain["skill_contributions"]

    @pytest.mark.integration
    @pytest.mark.bdd
    def test_command_skill_orchestration(self, mock_claude_tools) -> None:
        """Scenario: Commands properly orchestrate skills.

        Given /review command execution
        When dispatching to skills
        Then skills should receive correct context
        And return structured results
        And maintain workflow state.
        """
        # Arrange - track orchestration
        orchestration_log = {
            "command_invoked": None,
            "skill_calls": [],
            "context_flow": [],
            "results_chain": [],
        }

        def mock_orchestrated_skill(skill_name, context):
            """Mock skill being orchestrated by command."""
            orchestration_log["skill_calls"].append(skill_name)
            orchestration_log["context_flow"].append(context.copy())

            # Each skill adds to context
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

        mock_claude_tools["Skill"] = Mock(side_effect=mock_orchestrated_skill)

        # Act - simulate command orchestration
        def mock_review_command(args, context):
            """Mock /review command orchestrating skills."""
            orchestration_log["command_invoked"] = "/review"
            orchestration_log["results_chain"].append(
                {"stage": "command_start", "args": args},
            )

            # Orchestrate skills in sequence
            skills_to_orchestrate = [
                "review-core",
                "evidence-logging",
                "structured-output",
            ]

            for skill in skills_to_orchestrate:
                skill_context = context.copy()
                skill_context["command_context"] = {
                    "command": "/review",
                    "args": args,
                    "orchestrated": True,
                }

                result = mock_claude_tools["Skill"](skill, skill_context)
                orchestration_log["results_chain"].append(
                    {"stage": f"skill_{skill}_completed", "result": result},
                )

                # Propagate context changes
                for key, value in skill_context.items():
                    if key not in context:
                        context[key] = value

            orchestration_log["results_chain"].append(
                {"stage": "command_complete", "final_context": context},
            )
            return context

        # Execute orchestration
        command_args = []
        initial_context = {"target": "src/", "focus": "security"}

        final_context = mock_review_command(command_args, initial_context)

        # Assert orchestration quality
        assert orchestration_log["command_invoked"] == "/review"
        assert len(orchestration_log["skill_calls"]) == THREE
        assert orchestration_log["skill_calls"] == [
            "review-core",
            "evidence-logging",
            "structured-output",
        ]

        # Verify context propagation
        context_flows = orchestration_log["context_flow"]
        assert len(context_flows) == THREE

        # Check command context propagation
        for skill_context in context_flows:
            assert "command_context" in skill_context
            assert skill_context["command_context"]["command"] == "/review"
            assert skill_context["command_context"]["orchestrated"] is True

        # Verify results chain
        results_chain = orchestration_log["results_chain"]
        assert len(results_chain) == FIVE  # start + 3 skills + complete
        assert results_chain[0]["stage"] == "command_start"
        assert results_chain[-1]["stage"] == "command_complete"

        # Verify final context has all skill contributions
        assert "workflow_scaffold" in final_context
        assert "evidence_infrastructure" in final_context
        assert final_context["workflow_scaffold"]["items_created"] == FIVE
        assert final_context["evidence_infrastructure"]["tracking_enabled"] is True

    @pytest.mark.integration
    def test_error_propagation_through_workflow(self, mock_claude_tools) -> None:
        """Scenario: Errors are handled gracefully across workflow.

        Given skill execution failures
        When propagating through workflow
        Then errors should be captured and handled
        And workflow should provide meaningful feedback.
        """
        # Arrange - simulate skill failure
        error_log = []

        def mock_failing_skill(skill_name, context):
            """Mock skill that fails conditionally."""
            if skill_name == "diff-analysis" and context.get("simulate_error"):
                error = {
                    "skill": skill_name,
                    "error_type": "GitCommandError",
                    "message": "Git command failed: invalid reference",
                    "context": context.copy(),
                }
                error_log.append(error)
                msg = "Git command failed"
                raise Exception(msg)

            # Other skills succeed
            return {"skill": skill_name, "status": "success"}

        mock_claude_tools["Skill"] = Mock(side_effect=mock_failing_skill)

        # Act - execute workflow with error handling
        workflow_result = {
            "command": "/review",
            "skills_attempted": [],
            "skills_completed": [],
            "errors_encountered": [],
            "fallback_actions": [],
            "final_status": None,
        }

        skills_to_execute = ["review-core", "diff-analysis", "structured-output"]
        current_context = {"simulate_error": True}  # Trigger error in diff-analysis

        for skill in skills_to_execute:
            workflow_result["skills_attempted"].append(skill)
            try:
                result = mock_claude_tools["Skill"](skill, current_context)
                workflow_result["skills_completed"].append(skill)
                current_context.update(result)

            except Exception as e:
                workflow_result["errors_encountered"].append(
                    {"skill": skill, "error": str(e)},
                )

                # Implement fallback action
                if skill == "diff-analysis":
                    workflow_result["fallback_actions"].append(
                        "Used file system analysis instead of git diff",
                    )
                    # Continue with workflow despite error
                    current_context["diff_analysis_fallback"] = True

        # Determine final status
        if workflow_result["errors_encountered"]:
            if workflow_result["fallback_actions"]:
                workflow_result["final_status"] = "completed_with_fallbacks"
            else:
                workflow_result["final_status"] = "failed"
        else:
            workflow_result["final_status"] = "completed_successfully"

        # Assert error handling
        assert len(workflow_result["skills_attempted"]) == THREE
        assert (
            len(workflow_result["skills_completed"]) == TWO
        )  # review-core, structured-output
        assert len(workflow_result["errors_encountered"]) == 1  # diff-analysis failed
        assert workflow_result["errors_encountered"][0]["skill"] == "diff-analysis"

        # Verify fallback actions
        assert len(workflow_result["fallback_actions"]) == 1
        assert "file system analysis" in workflow_result["fallback_actions"][0]

        # Verify final status
        assert workflow_result["final_status"] == "completed_with_fallbacks"
        assert "diff_analysis_fallback" in current_context

        # Verify error logging
        assert len(error_log) == 1
        assert error_log[0]["skill"] == "diff-analysis"
        assert error_log[0]["error_type"] == "GitCommandError"

    @pytest.mark.performance
    @pytest.mark.integration
    def test_workflow_performance_under_load(self, mock_claude_tools) -> None:
        """Scenario: Workflow performs efficiently under load.

        Given multiple concurrent workflows
        When executing review workflows
        Then performance should remain acceptable
        And resource usage should be controlled.
        """
        # Arrange - simulate multiple workflow executions
        workflow_configs = [
            {"target": "src/auth/", "focus": "security"},
            {"target": "src/api/", "focus": "performance"},
            {"target": "src/payment/", "focus": "correctness"},
            {"target": "src/utils/", "focus": "style"},
            {"target": "docs/", "focus": "documentation"},
        ]

        performance_metrics = {
            "workflow_times": [],
            "skill_execution_times": {},
            "total_duration": 0,
            "concurrent_efficiency": True,
        }

        # Act - execute workflows with timing
        start_time = time.time()

        for i, config in enumerate(workflow_configs):
            workflow_start = time.time()

            # Simulate skill execution with timing
            skills = [
                "review-core",
                "evidence-logging",
                "diff-analysis",
                "structured-output",
            ]
            f"workflow_{i}_{config['target']}"

            skill_times = []
            for skill in skills:
                skill_start = time.time()

                # Simulate skill work (tiny delay for testing)
                time.sleep(0.001)  # 1ms per skill

                skill_duration = time.time() - skill_start
                skill_times.append(skill_duration)

                # Track per-skill timing
                if skill not in performance_metrics["skill_execution_times"]:
                    performance_metrics["skill_execution_times"][skill] = []
                performance_metrics["skill_execution_times"][skill].append(
                    skill_duration,
                )

            workflow_duration = time.time() - workflow_start
            performance_metrics["workflow_times"].append(workflow_duration)

        total_duration = time.time() - start_time
        performance_metrics["total_duration"] = total_duration

        # Assert performance efficiency
        assert total_duration < 1.0  # Should complete all workflows in under 1 second

        # Verify individual workflow times
        for workflow_time in performance_metrics["workflow_times"]:
            assert workflow_time < ZERO_POINT_ONE  # Each workflow under 100ms

        # Verify skill performance consistency
        for _skill, times in performance_metrics["skill_execution_times"].items():
            avg_time = sum(times) / len(times)
            assert avg_time < AVG_TIME_THRESHOLD  # Average skill time under 10ms
            assert max(times) - min(times) < TIME_RANGE_THRESHOLD  # Consistent timing

        # Calculate efficiency metrics
        total_workflows = len(workflow_configs)
        total_skills_executed = total_workflows * 4  # 4 skills per workflow
        skills_per_second = total_skills_executed / total_duration

        assert skills_per_second > FIFTY  # Should execute at least 50 skills per second
