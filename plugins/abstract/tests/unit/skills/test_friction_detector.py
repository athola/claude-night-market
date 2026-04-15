"""Tests for friction-detector skill content and structure.

Validates that the friction-detector skill defines signal types,
graduation tiers, detection workflow, anti-noise rules, and
integration points for the friction-to-learning pipeline.

Following TDD/BDD principles per the Iron Law.
"""

from pathlib import Path

import pytest

SKILL_PATH = Path(__file__).parents[3] / "skills" / "friction-detector" / "SKILL.md"


@pytest.fixture
def skill_content() -> str:
    """Load the friction-detector skill content."""
    return SKILL_PATH.read_text()


@pytest.fixture
def skill_lines(skill_content: str) -> list[str]:
    """Split skill content into lines for structure checks."""
    return skill_content.splitlines()


class TestFrictionDetectorFrontmatter:
    """Feature: Friction-detector has valid skill frontmatter.

    As a plugin developer
    I want correct frontmatter metadata
    So that the skill is discoverable and loads correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, skill_content: str) -> None:
        """Scenario: Frontmatter contains all required fields.

        Given the friction-detector skill
        When parsing frontmatter
        Then it should have name, description, version, and trigger
        """
        assert "name: friction-detector" in skill_content
        assert "description:" in skill_content
        assert "version:" in skill_content
        assert "trigger:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_not_always_apply(self, skill_content: str) -> None:
        """Scenario: Skill is not always-apply (opt-in only).

        Given the friction-detector skill
        When checking activation mode
        Then alwaysApply should be false
        """
        assert "alwaysApply: false" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_trigger_includes_friction(self, skill_content: str) -> None:
        """Scenario: Trigger keywords include core terms.

        Given the friction-detector skill
        When checking trigger keywords
        Then it should include friction-related terms
        """
        assert "friction" in skill_content.split("trigger:")[1].split("\n")[0]


class TestFrictionSignalTypes:
    """Feature: Friction-detector defines signal types with weights.

    As an agent operator
    I want classified friction signals
    So that I know what to detect and how to prioritize
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_signal_types_table(self, skill_content: str) -> None:
        """Scenario: Skill defines a table of friction signal types.

        Given the friction-detector skill
        When reviewing signal definitions
        Then it should have a table with signal, detection, and weight
        """
        assert "| Signal" in skill_content
        assert "| Detection Method" in skill_content
        assert "| Weight" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_includes_all_six_signal_types(self, skill_content: str) -> None:
        """Scenario: All six friction signal types are defined.

        Given the friction-detector skill
        When reviewing signal types
        Then it should include corrections, failures, denials,
             re-reads, retry loops, and frustration
        """
        lower = skill_content.lower()
        assert "repeated corrections" in lower
        assert "command failures" in lower
        assert "permission denial" in lower
        assert "re-read" in lower
        assert "retry loop" in lower
        assert "user frustration" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weights_are_high_medium_low(self, skill_content: str) -> None:
        """Scenario: Signal weights use High/Medium/Low classification.

        Given the signal types table
        When reviewing weight values
        Then each weight should be High, Medium, or Low
        """
        assert "| High |" in skill_content
        assert "| Medium |" in skill_content
        assert "| Low |" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_weights_have_numeric_scoring(self, skill_content: str) -> None:
        """Scenario: Weights map to numeric scores for calculation.

        Given the signal weight definitions
        When reviewing scoring rules
        Then High, Medium, and Low should have point values
        """
        assert "High = 3" in skill_content
        assert "Medium = 2" in skill_content
        assert "Low = 1" in skill_content


class TestThreeTierGraduation:
    """Feature: Three-tier storage graduation pipeline.

    As a learning system
    I want tiered promotion of friction patterns
    So that only validated patterns become permanent rules
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_defines_three_tiers(self, skill_content: str) -> None:
        """Scenario: Skill defines Tier 1, Tier 2, and Tier 3.

        Given the friction-detector skill
        When reviewing the graduation model
        Then all three tiers should be defined
        """
        assert "Tier 1:" in skill_content
        assert "Tier 2:" in skill_content
        assert "Tier 3:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tier1_is_ephemeral_per_session(self, skill_content: str) -> None:
        """Scenario: Tier 1 is ephemeral per-session friction log.

        Given the tier 1 definition
        When reviewing storage behavior
        Then it should be ephemeral and per-session
        """
        lower = skill_content.lower()
        assert "ephemeral" in lower
        assert "per-session" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tier2_integrates_with_learnings(self, skill_content: str) -> None:
        """Scenario: Tier 2 feeds into LEARNINGS.md.

        Given the tier 2 definition
        When reviewing storage location
        Then it should reference LEARNINGS.md
        """
        assert "LEARNINGS.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_tier3_requires_user_approval(self, skill_content: str) -> None:
        """Scenario: Tier 3 graduation never auto-modifies CLAUDE.md.

        Given the tier 3 definition
        When reviewing the graduation constraint
        Then it should require explicit user approval
        """
        assert "NEVER auto-modify CLAUDE.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_graduation_formula_exists(self, skill_content: str) -> None:
        """Scenario: A graduation scoring formula is defined.

        Given the graduation model
        When reviewing promotion criteria
        Then a formula with recency decay should exist
        """
        assert "graduation_score" in skill_content
        assert "recency_factor" in skill_content


class TestDetectionWorkflow:
    """Feature: Detection workflow with concrete steps.

    As an agent
    I want a step-by-step detection process
    So that friction is identified consistently
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_has_numbered_steps(self, skill_content: str) -> None:
        """Scenario: Workflow defines sequential steps.

        Given the detection workflow
        When reviewing the process
        Then it should have numbered steps
        """
        assert "### Step 1:" in skill_content
        assert "### Step 2:" in skill_content
        assert "### Step 3:" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_includes_json_schema(self, skill_content: str) -> None:
        """Scenario: Signal recording uses a defined JSON format.

        Given the detection workflow
        When reviewing data capture
        Then a JSON schema for signal records should exist
        """
        assert '"signal_type"' in skill_content
        assert '"weight"' in skill_content
        assert '"session_id"' in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_stores_to_friction_dir(self, skill_content: str) -> None:
        """Scenario: Session logs are stored in a friction directory.

        Given the detection workflow
        When reviewing storage paths
        Then it should use ~/.claude/friction/sessions/
        """
        assert "~/.claude/friction/sessions/" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_workflow_uses_rg_with_grep_fallback(self, skill_content: str) -> None:
        """Scenario: Shell commands prefer rg with grep fallback.

        Given the detection workflow shell snippets
        When reviewing command usage
        Then rg should be preferred with grep as fallback
        """
        assert "command -v rg" in skill_content
        assert "grep" in skill_content


class TestAntiNoiseRules:
    """Feature: Anti-noise filtering prevents false positives.

    As a friction detector
    I want noise filtering rules
    So that one-off errors do not pollute patterns
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_filters_one_off_failures(self, skill_content: str) -> None:
        """Scenario: One-off transient failures are ignored.

        Given the anti-noise rules
        When a single network timeout occurs
        Then it should be filtered out
        """
        lower = skill_content.lower()
        assert "one-off" in lower or "transient" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_filters_user_initiated_exploration(self, skill_content: str) -> None:
        """Scenario: User-initiated exploration is not flagged.

        Given the anti-noise rules
        When friction comes from deliberate experimentation
        Then it should be excluded
        """
        lower = skill_content.lower()
        assert "user-initiated" in lower or "exploration" in lower

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_decay_factor_reduces_stale_signals(self, skill_content: str) -> None:
        """Scenario: Stale friction signals decay over time.

        Given the anti-noise rules
        When a signal is older than 30 days
        Then its weight contribution should be reduced
        """
        assert "30 days" in skill_content
        assert "decay" in skill_content.lower() or "recency" in skill_content.lower()


class TestIntegrationPoints:
    """Feature: Friction-detector integrates with existing systems.

    As a plugin ecosystem
    I want clear integration contracts
    So that friction data flows to the right consumers
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_learnings(self, skill_content: str) -> None:
        """Scenario: Tier 2 patterns feed LEARNINGS.md.

        Given the integration section
        When reviewing data flow
        Then LEARNINGS.md should be a target
        """
        assert "LEARNINGS.md" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_skill_improver(self, skill_content: str) -> None:
        """Scenario: Friction data informs skill-improver priority.

        Given the integration section
        When reviewing downstream consumers
        Then skill-improver should be listed
        """
        assert "skill-improver" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integrates_with_metacognitive(self, skill_content: str) -> None:
        """Scenario: Metacognitive-self-mod can analyze pipeline.

        Given the integration section
        When reviewing feedback loops
        Then metacognitive-self-mod should be referenced
        """
        assert "metacognitive-self-mod" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_references_aggregate_logs(self, skill_content: str) -> None:
        """Scenario: Skill references existing aggregate-logs command.

        Given the integration section
        When reviewing related commands
        Then aggregate-logs should be mentioned
        """
        assert "aggregate-logs" in skill_content


class TestFrictionReportFormat:
    """Feature: Friction report has a defined output format.

    As a user reviewing friction
    I want a clear report structure
    So that I can act on findings efficiently
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_report_has_tier_sections(self, skill_content: str) -> None:
        """Scenario: Report separates signals by tier.

        Given the friction report format
        When reviewing section structure
        Then it should have Tier 1, Tier 2, and Tier 3 sections
        """
        assert "### New Signals (Tier 1)" in skill_content
        assert "### Recurring Patterns (Tier 2" in skill_content
        assert "### Graduation Proposals (Tier 3)" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_graduation_proposals_have_actions(self, skill_content: str) -> None:
        """Scenario: Graduation proposals include approve/reject actions.

        Given a Tier 3 graduation proposal
        When reviewing the proposal format
        Then it should offer Approve / Reject / Defer options
        """
        assert "Approve" in skill_content
        assert "Reject" in skill_content
        assert "Defer" in skill_content

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_report_includes_noise_filtered(self, skill_content: str) -> None:
        """Scenario: Report shows what was filtered as noise.

        Given the friction report format
        When reviewing transparency
        Then it should list noise-filtered items
        """
        assert "Noise Filtered" in skill_content


class TestSkillQuality:
    """Feature: Skill meets project quality standards.

    As a project maintainer
    I want consistent skill quality
    So that skills are maintainable and readable
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_skill_under_200_lines(self, skill_lines: list[str]) -> None:
        """Scenario: Skill stays under 200 lines.

        Given the friction-detector skill
        When counting lines
        Then it should be under 200 lines
        """
        assert len(skill_lines) <= 200, (
            f"Skill has {len(skill_lines)} lines, exceeds 200 limit"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_prose_lines_wrap_at_80_chars(self, skill_lines: list[str]) -> None:
        """Scenario: Prose lines wrap at 80 characters.

        Given the friction-detector skill
        When checking line lengths
        Then prose lines should not exceed 80 characters
        (excluding tables, code blocks, frontmatter, headings, URLs)
        """
        in_code_block = False
        in_frontmatter = False
        violations = []

        for i, line in enumerate(skill_lines, 1):
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            # Skip tables, headings, URLs, link definitions
            stripped = line.strip()
            if stripped.startswith("|"):
                continue
            if stripped.startswith("#"):
                continue
            if "http://" in line or "https://" in line:
                continue
            if stripped.startswith("[") and "]:" in stripped:
                continue
            if len(line) > 80:
                violations.append(f"  Line {i} ({len(line)} chars): {line}")

        assert not violations, "Lines exceed 80 chars:\n" + "\n".join(violations[:5])

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_em_dashes(self, skill_content: str) -> None:
        """Scenario: Skill uses no em dashes.

        Given the friction-detector skill
        When scanning for em dashes
        Then none should be present
        """
        assert "\u2014" not in skill_content, "Em dash found in skill content"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_no_emojis(self, skill_content: str) -> None:
        """Scenario: Skill contains no emojis.

        Given the friction-detector skill
        When scanning for emoji characters
        Then none should be present
        """
        import re

        emoji_pattern = re.compile(
            "[\U0001f600-\U0001f64f"
            "\U0001f300-\U0001f5ff"
            "\U0001f680-\U0001f6ff"
            "\U0001f1e0-\U0001f1ff"
            "\u2702-\u27b0"
            "\u24c2-\U0001f251"
            "\u2600-\u26ff]+",
            flags=re.UNICODE,
        )
        matches = emoji_pattern.findall(skill_content)
        assert not matches, f"Emojis found: {matches}"
