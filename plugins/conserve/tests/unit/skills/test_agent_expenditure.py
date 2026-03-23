"""Tests for agent-expenditure skill token waste monitoring.

This module tests waste signal detection and Brooks's Law thresholds
for agent dispatch sizing. Following TDD/BDD principles.

Note: agent-expenditure is a markdown-only methodology skill with no Python
source modules. The tests below validate:
  1. Skill file structure (SKILL.md exists, has frontmatter, modules present)
  2. Methodology concepts (ghost agent detection, Brooks's Law thresholds,
     post-dispatch review) using inline logic that mirrors the rules documented
     in the skill markdown files.
Structural and conceptual tests are the appropriate test type for skills that
contain no executable Python code. See GitHub issue #320.
"""

from __future__ import annotations

from pathlib import Path

import pytest


class TestAgentExpenditureStructure:
    """Feature: Skill file structure is valid and discoverable.

    As a plugin developer
    I want the skill to have proper structure
    So that it can be discovered and loaded correctly
    """

    @pytest.fixture
    def skill_dir(self) -> Path:
        """Return the skill directory path."""
        return Path(__file__).parents[3] / "skills" / "agent-expenditure"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_file_exists(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md file exists.

        Given the agent-expenditure skill directory
        When checking for SKILL.md
        Then the file should exist
        """
        skill_file = skill_dir / "SKILL.md"
        assert skill_file.exists(), f"SKILL.md not found at {skill_file}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md has valid YAML frontmatter.

        Given the SKILL.md file
        When parsing the file
        Then it should have YAML frontmatter with required fields
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        assert content.startswith("---"), "SKILL.md should start with frontmatter"
        assert content.count("---") >= 2, "SKILL.md should have closing frontmatter"

        # Verify required frontmatter fields
        frontmatter_end = content.index("---", 3)
        frontmatter = content[3:frontmatter_end]
        assert "name:" in frontmatter, "Frontmatter missing 'name' field"
        assert "description:" in frontmatter, "Frontmatter missing 'description' field"
        assert "category:" in frontmatter, "Frontmatter missing 'category' field"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_waste_signals_module_exists(self, skill_dir: Path) -> None:
        """Scenario: The waste-signals module is present on disk.

        Given the SKILL.md frontmatter declares modules/waste-signals.md
        When checking the modules directory
        Then the file should exist
        """
        module_path = skill_dir / "modules" / "waste-signals.md"
        assert module_path.exists(), f"Module not found: {module_path}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_waste_signals_module_has_frontmatter(self, skill_dir: Path) -> None:
        """Scenario: The waste-signals module has valid frontmatter.

        Given the waste-signals.md module file
        When parsing the file
        Then it should have YAML frontmatter with parent_skill
        """
        module_path = skill_dir / "modules" / "waste-signals.md"
        content = module_path.read_text()

        assert content.startswith("---"), (
            "waste-signals.md should start with frontmatter"
        )
        frontmatter_end = content.index("---", 3)
        frontmatter = content[3:frontmatter_end]
        assert "parent_skill:" in frontmatter, (
            "waste-signals.md missing 'parent_skill' field"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_all_five_waste_signals(self, skill_dir: Path) -> None:
        """Scenario: The waste-signals module documents all 5 signal types.

        Given the waste-signals.md module
        When scanning for waste signal headings
        Then all 5 categories should be present
        """
        module_path = skill_dir / "modules" / "waste-signals.md"
        content = module_path.read_text()

        expected_signals = [
            "Ghost Agent",
            "Redundant Reader",
            "Duplicate Worker",
            "Token Hog",
            "Coordination Overhead",
        ]
        for signal in expected_signals:
            assert signal in content, (
                f"Waste signal '{signal}' not documented in waste-signals.md"
            )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_documents_brooks_law_table(self, skill_dir: Path) -> None:
        """Scenario: SKILL.md includes a Brooks's Law threshold table.

        Given the SKILL.md file
        When scanning for the agent count guidance table
        Then all four agent count tiers should be present
        """
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text()

        expected_tiers = ["1-3", "4-5", "6-8", "9+"]
        for tier in expected_tiers:
            assert tier in content, f"Brooks's Law tier '{tier}' not found in SKILL.md"


class TestWasteSignalDetection:
    """Feature: Five waste signals detect token spending inefficiency.

    As a resource optimizer
    I want to detect wasted agent compute
    So that I can improve dispatch efficiency
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_ghost_agent_detection(self) -> None:
        """Scenario: Ghost agents consume tokens without findings.

        Given an agent in parallel dispatch
        When post-execution analysis occurs
        Then it should be flagged as ghost if:
        - Token expenditure > 1.5x median for task type
        - Findings count < 30% of median
        - Findings lack evidence citations
        """
        # Arrange
        median_tokens_for_task = 1000
        median_findings_for_task = 10

        agents = {
            "normal_agent": {
                "tokens_spent": 900,
                "findings_count": 8,
                "has_evidence": True,
            },
            "ghost_agent": {
                "tokens_spent": 1600,  # 1.6x median
                "findings_count": 2,  # 20% of median
                "has_evidence": False,
            },
            "high_effort_normal": {
                "tokens_spent": 1400,  # 1.4x median (just under threshold)
                "findings_count": 12,  # > 30% of median
                "has_evidence": True,
            },
        }

        # Act - detect ghost agents
        ghost_threshold_tokens = median_tokens_for_task * 1.5
        ghost_threshold_findings = median_findings_for_task * 0.3

        ghosts = {
            name: agent
            for name, agent in agents.items()
            if (
                agent["tokens_spent"] > ghost_threshold_tokens
                and agent["findings_count"] < ghost_threshold_findings
                and not agent["has_evidence"]
            )
        }

        # Assert
        assert len(ghosts) == 1
        assert "ghost_agent" in ghosts
        assert "normal_agent" not in ghosts
        assert "high_effort_normal" not in ghosts

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_redundant_reader_detection(self) -> None:
        """Scenario: Redundant readers re-read already-loaded files.

        Given multiple agents in parallel dispatch
        When analyzing file access logs
        Then agents reading same files as others are flagged
        """
        # Arrange
        agent_file_reads = {
            "agent_a": [
                "src/main.py",
                "src/utils.py",
                "config/settings.json",
            ],
            "agent_b": [
                "src/main.py",  # Duplicate read
                "src/handlers.py",
                "config/settings.json",  # Duplicate read
            ],
            "agent_c": [
                "tests/test_main.py",
                "docs/api.md",
            ],
        }

        # Act - find redundant reads
        all_reads = {agent: set(reads) for agent, reads in agent_file_reads.items()}

        redundant_pairs = []
        agents_list = list(all_reads.keys())
        for i, agent_a in enumerate(agents_list):
            for agent_b in agents_list[i + 1 :]:
                overlap = all_reads[agent_a] & all_reads[agent_b]
                if overlap:
                    redundant_pairs.append(
                        {
                            "agents": (agent_a, agent_b),
                            "overlapping_files": overlap,
                        }
                    )

        # Assert
        assert len(redundant_pairs) == 1
        assert redundant_pairs[0]["agents"] == ("agent_a", "agent_b")
        assert "src/main.py" in redundant_pairs[0]["overlapping_files"]
        assert "config/settings.json" in redundant_pairs[0]["overlapping_files"]

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_duplicate_worker_detection(self) -> None:
        """Scenario: Duplicate workers produce overlapping findings.

        Given findings from multiple agents
        When analyzing for semantic overlap
        Then findings >50% overlap indicate duplication
        """
        # Arrange
        agent_findings = {
            "agent_security": [
                {"issue": "Missing input validation on login form"},
                {"issue": "SQL injection vulnerability in query builder"},
                {"issue": "Weak password hashing algorithm"},
            ],
            "agent_quality": [
                {"issue": "Input not validated in login endpoint"},
                {"issue": "Database query vulnerable to SQL injection"},
                {"issue": "Code style violations in auth module"},
            ],
        }

        # Act - detect semantic overlap
        security_set = {
            "input validation",
            "sql injection",
            "password hashing",
        }
        quality_set = {
            "input validation",
            "sql injection",
            "code style",
        }

        overlap_count = len(security_set & quality_set)
        total_unique = len(security_set | quality_set)
        overlap_percentage = overlap_count / total_unique

        # Assert
        assert overlap_percentage >= 0.5  # >=50% overlap
        assert overlap_count == 2
        assert overlap_percentage == 2 / 4  # 50%

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_token_hog_detection(self) -> None:
        """Scenario: Token hogs exceed 3x median without proportional output.

        Given agent token expenditure
        When comparing to task-type median
        Then hogs > 3x median with insufficient output are flagged
        """
        # Arrange
        median_tokens_for_review = 500
        task_type_results = {
            "agent_1": {
                "tokens": 450,
                "findings": 5,
                "quality": "good",
            },
            "agent_2": {
                "tokens": 1200,  # 2.4x median
                "findings": 6,
                "quality": "good",
            },
            "agent_3": {
                "tokens": 1700,  # 3.4x median
                "findings": 4,  # Lower quality despite more tokens
                "quality": "poor",
            },
            "agent_4": {
                "tokens": 1800,  # 3.6x median
                "findings": 12,  # Justified by output
                "quality": "excellent",
            },
        }

        # Act - detect token hogs
        hog_threshold = median_tokens_for_review * 3
        hogs = {
            name: result
            for name, result in task_type_results.items()
            if (
                result["tokens"] > hog_threshold
                and result["quality"] in ["poor", "mediocre"]
            )
        }

        # Assert
        assert len(hogs) == 1
        assert "agent_3" in hogs
        assert "agent_4" not in hogs  # High tokens justified by quality
        assert "agent_2" not in hogs  # Below threshold

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_coordination_overhead_detection(self) -> None:
        """Scenario: Coordination overhead increases with agent count.

        Given N agents and their file operations
        When counting concurrent Read/Write conflicts
        Then overhead > 20% for N > 5 is a waste signal
        """
        # Arrange
        dispatch_scenarios = {
            "small_team": {
                "agent_count": 3,
                "conflict_percentage": 5,
                "is_overhead": False,
            },
            "medium_team": {
                "agent_count": 5,
                "conflict_percentage": 15,
                "is_overhead": False,
            },
            "large_team": {
                "agent_count": 7,
                "conflict_percentage": 25,  # > 20% with N > 5
                "is_overhead": True,
            },
            "huge_team": {
                "agent_count": 10,
                "conflict_percentage": 35,
                "is_overhead": True,
            },
        }

        # Act - flag coordination overhead
        overhead_detected = {}
        for scenario, data in dispatch_scenarios.items():
            has_overhead = data["agent_count"] > 5 and data["conflict_percentage"] > 20
            overhead_detected[scenario] = has_overhead

        # Assert
        assert overhead_detected["small_team"] is False
        assert overhead_detected["medium_team"] is False
        assert overhead_detected["large_team"] is True
        assert overhead_detected["huge_team"] is True


class TestBrooksLawThresholds:
    """Feature: Brooks's Law predicts coordination overhead growth.

    As a dispatch planner
    I want to know when adding agents becomes counterproductive
    So that I can right-size parallel dispatch
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_agent_count_thresholds(self) -> None:
        """Scenario: Agent count maps to expected overhead.

        Given agent count in dispatch
        When determining expected overhead
        Then it should follow Brooks's Law scaling
        """
        # Arrange
        thresholds = {
            "negligible": {"min": 1, "max": 3, "overhead": "0-5%"},
            "acceptable": {"min": 4, "max": 5, "overhead": "10-15%"},
            "close_watch": {"min": 6, "max": 8, "overhead": "20-30%"},
            "counterproductive": {"min": 9, "max": None, "overhead": "30%+"},
        }

        agent_counts = [1, 3, 4, 5, 6, 8, 9, 12]

        # Act - classify each count
        classifications = {}
        for count in agent_counts:
            for level, bounds in thresholds.items():
                max_val = bounds["max"] if bounds["max"] else float("inf")
                if bounds["min"] <= count <= max_val:
                    classifications[count] = level
                    break

        # Assert
        assert classifications[1] == "negligible"
        assert classifications[3] == "negligible"
        assert classifications[4] == "acceptable"
        assert classifications[5] == "acceptable"
        assert classifications[6] == "close_watch"
        assert classifications[8] == "close_watch"
        assert classifications[9] == "counterproductive"
        assert classifications[12] == "counterproductive"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_dispatch_decision_by_overhead(self) -> None:
        """Scenario: Dispatch decisions based on expected overhead.

        Given a planning stage
        When deciding agent count
        Then decisions should follow Brooks's Law guidance
        """
        # Arrange
        decisions = {
            1: {"dispatch_freely": True, "plan_required": False},
            2: {"dispatch_freely": True, "plan_required": False},
            3: {"dispatch_freely": True, "plan_required": False},
            4: {"dispatch_freely": False, "plan_required": True},
            5: {"dispatch_freely": False, "plan_required": True},
            6: {"dispatch_freely": False, "plan_required": True},
            8: {"dispatch_freely": False, "plan_required": True},
            9: {"dispatch_freely": False, "plan_required": True},
        }

        # Act - verify decision logic
        threshold_free = 3  # Up to 3 can dispatch freely
        threshold_plan = 4  # 4+ require a plan
        threshold_careful = 6  # 6+ require close monitoring

        verified = {}
        for count, expected in decisions.items():
            should_dispatch_freely = count <= threshold_free
            should_plan = count >= threshold_plan
            is_correct = (
                expected["dispatch_freely"] == should_dispatch_freely
                and expected["plan_required"] == should_plan
            )
            verified[count] = is_correct

        # Assert
        assert all(verified.values())

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_zero_finding_exception(self) -> None:
        """Scenario: Zero findings from low-risk scans are valid.

        Given a security audit of already-linted code
        When analyzing results
        Then zero findings should not trigger waste signals
        """
        # Arrange
        low_risk_scan = {
            "agent": "security-audit",
            "target": "already-linted-code",
            "tokens_spent": 800,
            "findings": 0,
            "reason": "Code already meets all standards",
        }

        median_tokens = 500
        median_findings = 5

        # Act - check waste criteria
        looks_like_ghost = (
            low_risk_scan["tokens_spent"] > median_tokens * 1.5
            and low_risk_scan["findings"] < median_findings * 0.3
        )

        # Context matters: is this a legitimate zero-finding result?
        is_legitimate_zero = (
            low_risk_scan["reason"] != ""
            and "already" in low_risk_scan["reason"].lower()
        )

        is_waste = looks_like_ghost and not is_legitimate_zero

        # Assert
        assert looks_like_ghost is True
        assert is_legitimate_zero is True
        assert is_waste is False


class TestPostDispatchReview:
    """Feature: Post-dispatch review evaluates expenditure efficiency.

    As a workflow evaluator
    I want to assess whether agent dispatch was efficient
    So that I can improve future dispatch strategies
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_review_checklist_completeness(self) -> None:
        """Scenario: Review checklist validates all 4 key questions.

        Given a completed parallel dispatch
        When conducting post-dispatch review
        Then all 4 questions must be answered
        """
        # Arrange
        review_checklist = [
            "Did each agent produce unique findings?",
            "Was total token expenditure proportional to value?",
            "Did any agent duplicate another's work?",
            "Would fewer agents have produced the same result?",
        ]

        review_responses = {
            "unique_findings": True,
            "token_proportional": False,
            "duplication_detected": True,
            "fewer_agents_sufficient": True,
        }

        # Act - map responses to questions
        answered = {
            i: (question, response)
            for i, (question, response) in enumerate(
                zip(review_checklist, review_responses.values())
            )
        }

        # Assert
        assert len(answered) == 4
        assert all(q for q, _ in answered.values())

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_efficiency_verdict_logic(self) -> None:
        """Scenario: Efficiency verdict based on checklist answers.

        Given review checklist responses
        When determining verdict
        Then 2+ "no" answers indicate reduce agent count
        """
        # Arrange
        review_scenarios = {
            "efficient": {
                "unique_findings": True,
                "token_proportional": True,
                "no_duplication": True,
                "few_agents_insufficient": True,
                "expected_verdict": "continue",
            },
            "inefficient": {
                "unique_findings": False,
                "token_proportional": False,
                "no_duplication": False,
                "few_agents_insufficient": False,
                "expected_verdict": "reduce",
            },
            "marginal": {
                "unique_findings": True,
                "token_proportional": False,
                "no_duplication": True,
                "few_agents_insufficient": True,
                "expected_verdict": "monitor",
            },
        }

        # Act - calculate verdicts
        verdicts = {}
        for scenario, responses in review_scenarios.items():
            no_count = sum(
                1 for k, v in responses.items() if k != "expected_verdict" and not v
            )
            if no_count > 1:
                verdict = "reduce"
            elif no_count == 0:
                verdict = "continue"
            else:
                verdict = "monitor"
            verdicts[scenario] = verdict

        # Assert
        assert verdicts["efficient"] == "continue"
        assert verdicts["inefficient"] == "reduce"
        assert verdicts["marginal"] == "monitor"
