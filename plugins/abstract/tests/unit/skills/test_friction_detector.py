"""Tests for friction-detector skill content and structure.

Validates that the friction-detector skill defines signal types,
graduation tiers, detection workflow, anti-noise rules, and
integration points for the friction-to-learning pipeline.

Coverage of the text-presence critique (issue #442, discussion #433),
stated exactly rather than implied:

============  =========================================================
Frontmatter   Guarded as an invariant. The block is parsed as YAML and
              the required keys are asserted as parsed values, so a
              frontmatter that no longer parses fails here instead of
              passing on a substring.
Thresholds    Guarded as invariants in
              ``TestFrictionDetectorInvariants``: tier ordering,
              recency decay, signal weights, storage schema version.
              These catch value drift, which was the specific defect
              named -- "Tier 2: 6.0" becoming "Tier 2: 8.0" fails.
Integration   Guarded, and moved. The four canaries here asserted the
              document *mentions* skill-improver, LEARNINGS.md and
              friends. That is backwards: the risk is not that the
              document stops naming an integration point, it is that
              the document keeps naming one that no longer exists.
              ``tests/test_cited_paths_resolve.py`` now resolves every
              ``plugin:name`` this file cites against the filesystem,
              so the SKILL.md qualifies those names and the guard
              lives where every other document gets the same check.
Prose content Not guarded, deliberately. The remaining tests assert
              that named concepts appear -- the six signal types, the
              tier descriptions, the report sections. No invariant
              underlies them: "the document must discuss anti-noise
              rules" is an editorial judgment, and a test that spells
              out the expected wording only restates the document. They
              are kept because deletion detection is worth something,
              and they are not dressed up as more than that.
============  =========================================================

The distinction that matters: an invariant fails when the document
becomes *wrong*, a presence check fails when it becomes *different*.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

SKILL_PATH = Path(__file__).parents[3] / "skills" / "friction-detector" / "SKILL.md"


@pytest.fixture
def skill_content() -> str:
    """Load the friction-detector skill content."""
    return SKILL_PATH.read_text()


@pytest.fixture
def skill_lines(skill_content: str) -> list[str]:
    """Split skill content into lines for structure checks."""
    return skill_content.splitlines()


@pytest.fixture
def frontmatter(skill_content: str) -> dict[str, Any]:
    """The frontmatter block, parsed.

    Parsing is the point. `"name: friction-detector" in text` is
    satisfied by that string appearing in a code fence, in prose, or
    inside a block whose indentation stopped being valid YAML three
    edits ago. Loading it asserts the harness can read the file the
    same way this test does.
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", skill_content, re.DOTALL)
    assert match, "SKILL.md must open with a YAML frontmatter block"
    loaded = yaml.safe_load(match.group(1))
    assert isinstance(loaded, dict), "frontmatter must parse to a mapping"
    return loaded


class TestFrictionDetectorFrontmatter:
    """Feature: Friction-detector has valid skill frontmatter.

    As a plugin developer
    I want correct frontmatter metadata
    So that the skill is discoverable and loads correctly
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_has_required_fields(self, frontmatter: dict[str, Any]) -> None:
        """Scenario: Frontmatter carries the keys the loader needs.

        Given the friction-detector skill
        When the frontmatter block is parsed as YAML
        Then name, description, and trigger are present and non-empty
        Because a key whose value is blank loads as None and the skill
             registers with no description, which the substring form
             could not tell apart from a correct one.
        """
        for key in ("name", "description", "trigger"):
            assert key in frontmatter, f"frontmatter is missing `{key}`"
            assert str(frontmatter[key] or "").strip(), f"`{key}` is empty"
        assert frontmatter["name"] == "friction-detector"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_not_always_apply(self, frontmatter: dict[str, Any]) -> None:
        """Scenario: Skill is opt-in, not always-apply.

        Given the friction-detector skill
        When the parsed activation mode is read
        Then alwaysApply is the boolean False
        Because YAML reads `false`, `False` and `"false"` as three
             different values, and only two of them keep the skill
             opt-in. The substring form accepted all three.
        """
        assert frontmatter.get("alwaysApply") is False

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_frontmatter_trigger_includes_friction(
        self, frontmatter: dict[str, Any]
    ) -> None:
        """Scenario: Trigger keywords include the skill's own subject.

        Given the friction-detector skill
        When the trigger list is parsed into terms
        Then at least one term contains "friction"
        Because a trigger list that never names what it detects cannot
             activate on the topic it exists for.
        """
        terms = [t.strip() for t in str(frontmatter["trigger"]).split(",")]
        assert any("friction" in t for t in terms), f"no friction term in {terms}"


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
    """Feature: Every integration point this skill names exists.

    As a plugin ecosystem
    I want clear integration contracts
    So that friction data flows to the right consumers

    Four canaries used to live here, one per named consumer, each
    asserting the document mentions it. They guarded the wrong
    direction. A test that fails when the document stops saying
    "skill-improver" protects the sentence; nothing protected the
    reader who followed it. Delete the agent and every one of them
    stayed green while the instruction became false.

    The resolution guard is ``tests/test_cited_paths_resolve.py``,
    which walks all ~968 workflow documents and resolves every
    ``plugin:name`` citation against the filesystem. This skill's
    integration names are qualified so that sweep covers them, which
    is why the per-name canaries are gone rather than rewritten: the
    invariant is ecosystem-wide and belongs in one place.

    What is not guarded, and will not be: whether the document *should*
    name a given consumer. That is an editorial call with no invariant
    behind it, and a test asserting it would only restate the document.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_integration_names_are_qualified(self, skill_content: str) -> None:
        """Scenario: Named capabilities carry their plugin prefix.

        Given the integration and related sections
        When each backticked capability reference is read
        Then it is qualified as `plugin:name`
        Because the ecosystem resolution guard keys on that form. A
             bare `skill-improver` resolves to nothing and is silently
             skipped, so dropping the prefix removes the citation from
             the only gate that checks it.
        """
        bare = re.findall(
            r"`(skill-improver|metacognitive-self-mod|aggregate-logs)`",
            skill_content,
        )
        assert not bare, (
            "these capability references lost their plugin prefix and are "
            f"no longer covered by tests/test_cited_paths_resolve.py: {bare}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_learnings_target_is_a_concrete_path(self, skill_content: str) -> None:
        """Scenario: The Tier 2 destination is written as a real path.

        Given the graduation pipeline writes Tier 2 patterns out
        When the LEARNINGS.md destination is read
        Then it is given as a resolvable path, not a bare filename
        Because the file is created on first write in the user's home
             and cannot be checked on disk here. Naming the directory
             is what makes the instruction followable, and a bare
             "LEARNINGS.md" was the whole content of the old canary.
        """
        assert re.search(r"~/\.claude/skills/LEARNINGS\.md", skill_content), (
            "the Tier 2 destination must be written as a full path"
        )


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
    def test_skill_under_220_lines(self, skill_lines: list[str]) -> None:
        """Scenario: Skill stays compact (<=220 lines).

        Given the friction-detector skill
        When counting lines
        Then it should be under 220 lines

        Bumped from 200 to 220 to accommodate the envelope schema
        example added for ADR-0011 (issue #422). The hard cap exists
        to prevent unbounded growth, not to lock the file at a
        single value.
        """
        assert len(skill_lines) <= 220, (
            f"Skill has {len(skill_lines)} lines, exceeds 220 limit"
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


class TestFrictionDetectorInvariants:
    """Feature: Skill structure encodes operational invariants (#442).

    Tests in this class assert *invariants* about structure and
    numeric thresholds rather than literal string presence. They
    serve as the migration target for the older string-presence
    tests above.

    As a maintainer
    I want tests that catch value drift and rewording
    So that a change to "Tier 2 threshold: 6.0" -> "Tier 2: 8.0"
       fails the suite, not silently changes meaning.
    """

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_graduation_thresholds_are_strictly_monotonic(
        self, skill_content: str
    ) -> None:
        """Scenario: Tier 2 < Tier 3 graduation thresholds.

        Given the friction-detector skill defines graduation thresholds
        When the Tier 2 and Tier 3 numeric values are extracted
        Then Tier 2 must be strictly less than Tier 3
        Because graduation is a one-way escalation; equal or inverted
             thresholds collapse the tier system.
        """
        tier2_match = re.search(
            r"Tier\s*2\s*threshold:\s*graduation_score\s*>=\s*([\d.]+)",
            skill_content,
        )
        tier3_match = re.search(
            r"Tier\s*3\s*proposal:\s*graduation_score\s*>=\s*([\d.]+)",
            skill_content,
        )
        assert tier2_match, "Tier 2 threshold must be specified numerically"
        assert tier3_match, "Tier 3 proposal threshold must be specified numerically"
        tier2 = float(tier2_match.group(1))
        tier3 = float(tier3_match.group(1))
        assert tier2 < tier3, (
            f"Tier 2 threshold ({tier2}) must be strictly less than "
            f"Tier 3 proposal threshold ({tier3}); inverted/equal "
            "thresholds collapse the tier system"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_recency_factor_is_strictly_decreasing(self, skill_content: str) -> None:
        """Scenario: Recency factor decays with age.

        Given the friction-detector skill defines a recency_factor table
        When the four numeric coefficients are extracted in time order
        Then they must be strictly decreasing
        Because more recent friction must outweigh older friction;
             equal or non-monotonic values break graduation scoring.
        """
        recent = re.search(r"last 7 days\s*=\s*([\d.]+)", skill_content)
        mid = re.search(r"8-14 days\s*=\s*([\d.]+)", skill_content)
        late = re.search(r"15-30 days\s*=\s*([\d.]+)", skill_content)
        old = re.search(r"31\+\s*days\s*=\s*([\d.]+)", skill_content)
        assert all([recent, mid, late, old]), (
            "All four recency_factor entries must be specified"
        )
        # Pyright cannot infer assert all() narrows None types.
        assert recent is not None
        assert mid is not None
        assert late is not None
        assert old is not None
        values = [
            float(recent.group(1)),
            float(mid.group(1)),
            float(late.group(1)),
            float(old.group(1)),
        ]
        for left, right in zip(values, values[1:]):
            assert left > right, f"recency_factor must strictly decrease: {values}"

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_signal_weights_are_distinct_and_ordered(self, skill_content: str) -> None:
        """Scenario: Signal weight scoring uses distinct integer points.

        Given the skill specifies "High = 3, Medium = 2, Low = 1"
        When the three weights are parsed
        Then High > Medium > Low and all are positive integers
        Because zero or duplicate weights make graduation insensitive
             to severity classification.
        """
        match = re.search(
            r"High\s*=\s*(\d+)[^M]*Medium\s*=\s*(\d+)[^L]*Low\s*=\s*(\d+)",
            skill_content,
        )
        assert match, "Weight scoring must specify High/Medium/Low integer points"
        high, medium, low = (int(g) for g in match.groups())
        assert high > medium > low > 0, (
            f"weights must satisfy High > Medium > Low > 0: "
            f"got High={high}, Medium={medium}, Low={low}"
        )

    @pytest.mark.bdd
    @pytest.mark.unit
    def test_storage_path_uses_envelope_schema_version(
        self, skill_content: str
    ) -> None:
        """Scenario: Friction signals use the shared session-capture envelope.

        Given the friction-detector skill emits per-session JSON
        When inspecting the example payload
        Then it must declare ``schema_version`` and ``source: friction-detector``
        Because envelope adoption (ADR-0011) is what lets downstream
             readers consume friction signals and traces uniformly.
        """
        assert '"schema_version"' in skill_content, (
            "Friction signal example must declare schema_version (ADR-0011)"
        )
        assert '"source": "friction-detector"' in skill_content, (
            "Friction signal envelope must set source=friction-detector"
        )
