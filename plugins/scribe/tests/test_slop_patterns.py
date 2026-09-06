"""Tests for AI slop pattern detection.

Issue #36: Plugin: create scribe, a documentation review/update/generation plugin

Tests verify the slop detection patterns work correctly across
vocabulary, structural, and fiction-specific categories.
"""

import re
import sys
from pathlib import Path

import pytest

# Add src to path so the runtime pattern source is importable. Tier 5
# tests source their regex from pattern_loader rather than inline
# fixtures, so they fail if the YAML tier5 section is removed
# (de-tautologized per Discussion #542).
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scribe.pattern_loader import (
    get_ste_patterns,
    get_tier5_patterns,
    load_language_patterns,
)


def _tier5_category(name: str) -> dict:
    """Return one Tier 5 category from the English runtime source."""
    patterns = load_language_patterns("en")
    for entry in get_tier5_patterns(patterns):
        if entry["category"] == name:
            return entry
    raise AssertionError(f"tier5 category not found in runtime source: {name}")


def _compile_category(name: str) -> list[re.Pattern]:
    """Compile every regex in a Tier 5 category with its declared flags."""
    entry = _tier5_category(name)
    flags = re.IGNORECASE if entry.get("ignore_case") else 0
    return [re.compile(p, flags) for p in entry["patterns"]]


def _category_hits(name: str, text: str) -> int:
    """Total matches across all regex in a Tier 5 category."""
    return sum(len(p.findall(text)) for p in _compile_category(name))


def _tier5_category_including_optional(name: str) -> dict:
    """Return one Tier 5 category, including the opt-in ones."""
    patterns = load_language_patterns("en")
    for entry in get_tier5_patterns(patterns, include_optional=True):
        if entry["category"] == name:
            return entry
    raise AssertionError(f"tier5 category not found in runtime source: {name}")


def _category_hits_including_optional(name: str, text: str) -> int:
    """Total matches for a category that may be gated off by default."""
    entry = _tier5_category_including_optional(name)
    flags = re.IGNORECASE if entry.get("ignore_case") else 0
    return sum(len(re.compile(p, flags).findall(text)) for p in entry["patterns"])


class TestTier1VocabularyPatterns:
    """Feature: Detect highest-confidence AI slop words.

    As a documentation maintainer
    I want to detect tier-1 slop words
    So that I can remove obvious AI markers from content
    """

    TIER1_WORDS = [
        "delve",
        "embark",
        "tapestry",
        "realm",
        "beacon",
        "multifaceted",
        "nuanced",
        "pivotal",
        "paramount",
        "meticulous",
        "meticulously",
        "intricate",
        "showcasing",
        "leveraging",
        "streamline",
        "unleash",
        "comprehensive",
    ]

    @pytest.fixture
    def tier1_pattern(self) -> re.Pattern:
        """Compile tier-1 detection pattern."""
        pattern = r"\b(" + "|".join(self.TIER1_WORDS) + r")\b"
        return re.compile(pattern, re.IGNORECASE)

    @pytest.mark.unit
    def test_detects_delve(self, tier1_pattern: re.Pattern) -> None:
        """Scenario: Detect 'delve' as tier-1 slop.

        Given text containing the word 'delve'
        When scanning for tier-1 patterns
        Then it should be flagged.
        """
        text = "Let's delve into the details."
        matches = tier1_pattern.findall(text)
        assert len(matches) == 1
        assert matches[0].lower() == "delve"

    @pytest.mark.unit
    def test_detects_tapestry(self, tier1_pattern: re.Pattern) -> None:
        """Scenario: Detect 'tapestry' as tier-1 slop."""
        text = "This creates a rich tapestry of features."
        matches = tier1_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_multiple_slop_words(self, tier1_pattern: re.Pattern) -> None:
        """Scenario: Detect multiple tier-1 words in one passage."""
        text = """
        This comprehensive solution leverages cutting-edge technology
        to delve into the multifaceted realm of documentation.
        """
        matches = tier1_pattern.findall(text)
        # Should find: comprehensive, leverages (leveraging), delve, multifaceted, realm
        assert len(matches) >= 4

    @pytest.mark.unit
    def test_clean_text_no_matches(self, tier1_pattern: re.Pattern) -> None:
        """Scenario: Clean text has no tier-1 matches."""
        text = "The system processes requests and returns results."
        matches = tier1_pattern.findall(text)
        assert len(matches) == 0


class TestPhrasePatterns:
    """Feature: Detect AI slop phrase patterns.

    As a documentation maintainer
    I want to detect formulaic AI phrases
    So that I can remove them for more direct writing
    """

    VAPID_OPENERS = [
        r"in today's fast-paced",
        r"in an ever-evolving",
        r"in the dynamic world of",
        r"as technology continues to evolve",
    ]

    @pytest.fixture
    def vapid_pattern(self) -> re.Pattern:
        """Compile vapid opener pattern."""
        pattern = "|".join(self.VAPID_OPENERS)
        return re.compile(pattern, re.IGNORECASE)

    @pytest.mark.unit
    def test_detects_fast_paced_opener(self, vapid_pattern: re.Pattern) -> None:
        """Scenario: Detect 'In today's fast-paced world' opener."""
        text = "In today's fast-paced world, documentation is crucial."
        matches = vapid_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_ever_evolving(self, vapid_pattern: re.Pattern) -> None:
        """Scenario: Detect 'ever-evolving landscape' pattern."""
        text = "In an ever-evolving landscape of technology..."
        matches = vapid_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_direct_opener_no_match(self, vapid_pattern: re.Pattern) -> None:
        """Scenario: Direct opener does not match."""
        text = "scribe detects AI patterns in documentation."
        matches = vapid_pattern.findall(text)
        assert len(matches) == 0


class TestStructuralPatterns:
    """Feature: Detect structural AI patterns.

    As a documentation maintainer
    I want to detect structural patterns like excessive em dashes
    So that I can normalize document structure
    """

    @pytest.mark.unit
    def test_em_dash_count(self) -> None:
        """Scenario: Count em dashes in text."""
        text = "The system—which handles requests—returns data—quickly."
        em_dash_count = text.count("—")
        word_count = len(text.split())
        density = em_dash_count / word_count * 1000

        # 3 em dashes in ~7 words = very high density
        assert em_dash_count == 3
        assert density > 100  # Well above threshold

    @pytest.mark.unit
    def test_normal_em_dash_usage(self) -> None:
        """Scenario: Normal em dash usage passes."""
        text = """
        The system processes requests efficiently. Each request
        goes through validation—ensuring data integrity—before
        being stored in the database. Results typically return
        within 50ms for most queries, though complex aggregations
        may take longer depending on data volume.
        """
        em_dash_count = text.count("—")
        word_count = len(text.split())
        density = em_dash_count / word_count * 1000

        # 2 em dashes in ~40 words = ~50/1000, well under 100
        assert density < 100

    @pytest.mark.unit
    def test_bullet_ratio_calculation(self) -> None:
        """Scenario: Calculate bullet point ratio."""
        text = """# Header

- Bullet one
- Bullet two
- Bullet three

Regular paragraph here.

- Another bullet
- And another
"""
        lines = [line for line in text.strip().split("\n") if line.strip()]
        bullet_lines = sum(1 for line in lines if line.strip().startswith("-"))
        total_lines = len(lines)
        ratio = bullet_lines / total_lines

        # 5 bullet lines out of 8 total = 62.5%
        assert ratio > 0.5  # Above 50% threshold


class TestFictionPatterns:
    """Feature: Detect fiction-specific AI patterns.

    As a creative writer
    I want to detect cliche physical/emotional beats
    So that I can write more original prose
    """

    @pytest.fixture
    def breath_pattern(self) -> re.Pattern:
        """Pattern for breath cliches."""
        return re.compile(
            r"breath \w+ didn't know|let out a breath|"
            r"released a breath|exhaled a breath",
            re.IGNORECASE,
        )

    @pytest.fixture
    def wash_pattern(self) -> re.Pattern:
        """Pattern for emotion washing cliches."""
        return re.compile(
            r"(relief|fear|dread|panic|exhaustion) washed over", re.IGNORECASE
        )

    @pytest.mark.unit
    def test_detects_breath_cliche(self, breath_pattern: re.Pattern) -> None:
        """Scenario: Detect 'breath he didn't know' cliche."""
        text = "He let out a breath he didn't know he was holding."
        matches = breath_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_detects_relief_washing(self, wash_pattern: re.Pattern) -> None:
        """Scenario: Detect 'relief washed over' cliche."""
        text = "Relief washed over her as the test passed."
        matches = wash_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_original_emotion_no_match(self, wash_pattern: re.Pattern) -> None:
        """Scenario: Original emotional description doesn't match."""
        text = "Her shoulders dropped three inches as tension released."
        matches = wash_pattern.findall(text)
        assert len(matches) == 0


class TestSlopScoring:
    """Feature: Calculate overall slop score.

    As a documentation maintainer
    I want a single score representing AI content density
    So that I can prioritize remediation efforts
    """

    @pytest.mark.unit
    def test_clean_text_low_score(self) -> None:
        """Scenario: Clean text has low slop score."""
        text = """
        The cache sits between the API and database. When a request
        arrives, we check Redis first. Cache hits return in under 5ms.
        """
        # Simulate scoring: count tier-1 words
        tier1_words = ["delve", "tapestry", "realm", "comprehensive"]
        tier1_count = sum(1 for word in tier1_words if word in text.lower())
        word_count = len(text.split())
        score = (tier1_count * 3) / word_count * 100

        assert score < 1.0  # Clean threshold

    @pytest.mark.unit
    def test_sloppy_text_high_score(self) -> None:
        """Scenario: Sloppy text has high slop score."""
        text = """
        In today's fast-paced world, this comprehensive solution
        delves into the multifaceted realm of documentation,
        leveraging cutting-edge technology to unleash the full
        potential of your content tapestry.
        """
        tier1_words = [
            "delve",
            "delves",
            "tapestry",
            "realm",
            "comprehensive",
            "multifaceted",
            "leveraging",
            "unleash",
        ]
        tier1_count = sum(1 for word in tier1_words if word in text.lower())
        word_count = len(text.split())
        score = (tier1_count * 3) / word_count * 100

        assert score > 5.0  # Heavy slop threshold


class TestTier5SpatialCopula:
    """Feature: Detect spatial-copula / animated-inanimate patterns.

    As a documentation maintainer
    I want to detect "lives in", "sits at", "stands as" and similar
    verbs used with inanimate subjects
    So that I can replace them with plain "is/has/uses"
    """

    @pytest.fixture
    def copula_pattern(self) -> re.Pattern:
        """Pattern for spatial copula verbs."""
        return re.compile(
            r"\b(?:lives?|sits?|stands?|rests?|dwells?)"
            r"\s+(?:in|at|on|between|within|atop)\b",
            re.IGNORECASE,
        )

    @pytest.fixture
    def serves_pattern(self) -> re.Pattern:
        """Pattern for 'serves as' / 'stands as' / 'boasts'."""
        return re.compile(
            r"\b(?:serves?\s+as|stands?\s+as|boasts?|nestled\s+in|rooted\s+in)\b",
            re.IGNORECASE,
        )

    @pytest.mark.unit
    def test_detects_lives_in(self, copula_pattern: re.Pattern) -> None:
        """Scenario: Detect 'lives in' as spatial copula."""
        text = "The skill lives in `plugins/scribe/`."
        matches = copula_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_sits_between(self, copula_pattern: re.Pattern) -> None:
        """Scenario: Detect 'sits between' as spatial copula."""
        text = "The cache sits between the API and the database."
        matches = copula_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_stands_as(self, serves_pattern: re.Pattern) -> None:
        """Scenario: Detect 'stands as' (copula avoidance, not spatial)."""
        text = "The framework stands as a foundation for new work."
        matches = serves_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_detects_boasts(self, serves_pattern: re.Pattern) -> None:
        """Scenario: Detect 'boasts' (animation of inanimate)."""
        text = "The library boasts 50 features and excellent docs."
        matches = serves_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_detects_serves_as(self, serves_pattern: re.Pattern) -> None:
        """Scenario: Detect 'serves as'."""
        text = "This pattern serves as the basis for the workflow."
        matches = serves_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_plain_is_passes(self, copula_pattern: re.Pattern) -> None:
        """Scenario: Plain 'is' does not match."""
        text = "The skill is in plugins/scribe/."
        matches = copula_pattern.findall(text)
        assert len(matches) == 0


class TestTier5NegativeParallelism:
    """Feature: Detect negative-parallelism rhetorical scaffolds.

    The strongest 2026 prose tell per cross-source consensus.
    """

    @pytest.fixture
    def not_just_pattern(self) -> re.Pattern:
        return re.compile(
            r"\bNot\s+just\s+\w+,?\s+but(?:\s+also)?\s+\w+", re.IGNORECASE
        )

    @pytest.fixture
    def its_not_pattern(self) -> re.Pattern:
        # Non-greedy across optional articles/words up to the
        # comma, then "it's <word>". Real prose uses multi-word
        # objects like "a tool", "just a phase".
        return re.compile(
            r"\bIt's not [\w\s]+?,\s+it's \w+",
            re.IGNORECASE,
        )

    @pytest.fixture
    def no_no_just_pattern(self) -> re.Pattern:
        return re.compile(r"\bNo \w+\.\s+No \w+\.\s+Just \w+", re.IGNORECASE)

    @pytest.fixture
    def thats_okay_pattern(self) -> re.Pattern:
        return re.compile(r"\bAnd that's okay\.", re.IGNORECASE)

    @pytest.fixture
    def comma_no_pattern(self) -> re.Pattern:
        # Comma-joined variant of "No X. No Y.": "No X, no Y, no Z".
        return re.compile(r"\bNo \w+,\s+no \w+(?:,\s+no \w+)*", re.IGNORECASE)

    @pytest.fixture
    def trailing_not_pattern(self) -> re.Pattern:
        # Trailing corrective negation: "Y, not X." Catches the
        # rhetorical tail. Genuine either/or choices ("Python, not
        # Java") are slop too: rewrite as "Y instead of X".
        return re.compile(r"\b\w+,\s+not\s+(?:just\s+)?\w+[.!?]")

    @pytest.mark.unit
    def test_detects_not_just_but(self, not_just_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Not just X, but Y' construction."""
        text = "Not just fast, but elegant."
        matches = not_just_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_not_just_but_also(self, not_just_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Not just X, but also Y' variant."""
        text = "Not just fast, but also elegant."
        matches = not_just_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_its_not_its(self, its_not_pattern: re.Pattern) -> None:
        """Scenario: Detect 'It's not X, it's Y' construction."""
        text = "It's not a tool, it's a transformation."
        matches = its_not_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_no_no_just(self, no_no_just_pattern: re.Pattern) -> None:
        """Scenario: Detect 'No X. No Y. Just Z.' construction."""
        text = "No friction. No setup. Just code."
        matches = no_no_just_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_and_thats_okay(self, thats_okay_pattern: re.Pattern) -> None:
        """Scenario: Detect 'And that's okay.' closing reassurance."""
        text = "Sometimes the tests fail. And that's okay."
        matches = thats_okay_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_comma_joined_no(self, comma_no_pattern: re.Pattern) -> None:
        """Scenario: Detect 'No X, no Y, no Z' comma-joined construction."""
        text = "No friction, no setup, no config."
        assert len(comma_no_pattern.findall(text)) == 1

    @pytest.mark.unit
    def test_detects_trailing_negation(self, trailing_not_pattern: re.Pattern) -> None:
        """Scenario: Detect trailing 'Y, not X' corrective negation."""
        text = "The API is clear, not clever."
        assert len(trailing_not_pattern.findall(text)) == 1

    @pytest.mark.unit
    def test_detects_trailing_negation_proper_noun(
        self, trailing_not_pattern: re.Pattern
    ) -> None:
        """Scenario: Either/or with proper nouns is still slop.

        "Python, not Java" is flagged; the rewrite is "Python
        instead of Java", which keeps the contrast without the tail.
        """
        text = "We use Python, not Java."
        assert len(trailing_not_pattern.findall(text)) == 1

    @pytest.mark.unit
    def test_detects_copula_led_corrective_with_article(self) -> None:
        """Scenario: 'It's X, not Y' with articles (the reported tic).

        The trailing corrective led by a copula ("It's a tool, not a
        toy") is the most common form seen in generated docs. The bare
        trailing regex misses it because Y carries an article. Sourced
        from the runtime YAML, not an inline fixture.
        """
        assert _category_hits("negative_parallelism", "It's a tool, not a toy.") >= 1

    @pytest.mark.unit
    def test_detects_copula_led_corrective_mid_sentence(self) -> None:
        """Scenario: copula-led corrective with no terminal punctuation.

        "It's fast, not clever, and that matters." has the corrective
        tail mid-sentence; the bare trailing regex needs a sentence-
        final period and so misses it.
        """
        assert (
            _category_hits(
                "negative_parallelism", "It's fast, not clever, and that matters."
            )
            >= 1
        )

    @pytest.mark.unit
    def test_detects_trailing_corrective_with_article(self) -> None:
        """Scenario: trailing 'X, not a Y.' with an article before Y."""
        assert (
            _category_hits("negative_parallelism", "The API is clear, not a gimmick.")
            >= 1
        )

    @pytest.mark.unit
    def test_copula_list_comma_is_not_corrective(self) -> None:
        """Guard: an ordinary list comma must not trip the corrective regex."""
        assert (
            _category_hits(
                "negative_parallelism", "It's a fast, reliable, well-tested tool."
            )
            == 0
        )

    @pytest.mark.unit
    def test_comma_no_ignores_single_no(self, comma_no_pattern: re.Pattern) -> None:
        """Scenario: A single 'No X.' is not the comma-joined pattern."""
        text = "No config required."
        assert len(comma_no_pattern.findall(text)) == 0

    @pytest.mark.unit
    def test_positive_statement_passes(
        self,
        not_just_pattern: re.Pattern,
        its_not_pattern: re.Pattern,
    ) -> None:
        """Scenario: Positive statement does not match negative parallelism."""
        text = "The framework is fast and elegant."
        assert len(not_just_pattern.findall(text)) == 0
        assert len(its_not_pattern.findall(text)) == 0


class TestTier5PlusSignConjunction:
    """Feature: Detect plus-sign used as 'and' in prose."""

    @pytest.fixture
    def plus_pattern(self) -> re.Pattern:
        return re.compile(r"\w\s\+\s\w")

    @pytest.mark.unit
    def test_detects_plus_in_prose(self, plus_pattern: re.Pattern) -> None:
        """Scenario: Detect 'hooks + skills' in prose."""
        text = "The plugin uses hooks + skills together."
        matches = plus_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_plus_in_version_string_acceptable(self) -> None:
        """Scenario: '3.11+' in version context is acceptable.

        The detection regex requires word-space-plus-space-word,
        so '3.11+' (no surrounding spaces) does not match.
        """
        pattern = re.compile(r"\w\s\+\s\w")
        text = "Requires Python 3.11+ for typing features."
        matches = pattern.findall(text)
        assert len(matches) == 0

    @pytest.mark.unit
    def test_and_passes(self, plus_pattern: re.Pattern) -> None:
        """Scenario: Plain 'and' does not match."""
        text = "The plugin uses hooks and skills together."
        matches = plus_pattern.findall(text)
        assert len(matches) == 0


class TestTier5ThroatClearing:
    """Feature: Detect throat-clearing discourse openers."""

    @pytest.fixture
    def opener_pattern(self) -> re.Pattern:
        return re.compile(
            r"^(?:Here's the thing,|Look,\s+[A-Z]|The thing is,|"
            r"Let me explain\.|Bear with me\.|"
            r"The uncomfortable truth is)",
            re.MULTILINE,
        )

    @pytest.fixture
    def let_that_sink_pattern(self) -> re.Pattern:
        return re.compile(r"\bLet that sink in\b", re.IGNORECASE)

    @pytest.mark.unit
    def test_detects_heres_the_thing(self, opener_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Here's the thing,' opener."""
        text = "Here's the thing, this approach is fragile."
        matches = opener_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_look_opener(self, opener_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Look,' as sentence opener."""
        text = "Look, This is not the right path forward."
        matches = opener_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_detects_let_that_sink_in(self, let_that_sink_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Let that sink in.'"""
        text = "The system handles 1M req/s. Let that sink in."
        matches = let_that_sink_pattern.findall(text)
        assert len(matches) == 1

    @pytest.mark.unit
    def test_substantive_opener_passes(self, opener_pattern: re.Pattern) -> None:
        """Scenario: Substantive opener does not match."""
        text = "The skill processes input and returns findings."
        matches = opener_pattern.findall(text)
        assert len(matches) == 0


class TestTier5ThreeFragmentBurst:
    """Feature: Detect three-fragment-burst patterns."""

    @pytest.fixture
    def burst_pattern(self) -> re.Pattern:
        return re.compile(r"\b([A-Z][a-z]+)\.\s+([A-Z][a-z]+)\.\s+([A-Z][a-z]+)\.")

    @pytest.mark.unit
    def test_detects_three_word_burst(self, burst_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Focused. Aligned. Measurable.'"""
        text = "Our principles are simple. Focused. Aligned. Measurable."
        matches = burst_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_detects_fast_reliable_cheap(self, burst_pattern: re.Pattern) -> None:
        """Scenario: Detect 'Fast. Reliable. Cheap.'"""
        text = "Pick two. Fast. Reliable. Cheap."
        matches = burst_pattern.findall(text)
        assert len(matches) >= 1

    @pytest.mark.unit
    def test_normal_short_sentences_no_match(self, burst_pattern: re.Pattern) -> None:
        """Scenario: Normal short sentences with content don't match."""
        text = (
            "The cache works well. It returns results quickly. We added it last week."
        )
        matches = burst_pattern.findall(text)
        # These have multi-word sentences; the burst regex needs
        # exactly three single-capitalized-word sentences in a row
        assert len(matches) == 0


class TestTier5EmDashPreventionMode:
    """Feature: Prevention-mode em-dash detection (any em-dash fails).

    Audit mode tolerates legitimate em-dash usage by human writers.
    Prevention mode applies to docs an agent just generated, where
    every em-dash is a finding.
    """

    @pytest.mark.unit
    def test_prevention_mode_any_em_dash_is_finding(self) -> None:
        """Scenario: In prevention mode, even one em dash fails."""
        text = "The system handles requests—and returns results quickly."
        em_dash_count = text.count("—")
        # Prevention mode: nonzero count is a finding
        assert em_dash_count == 1
        prevention_failed = em_dash_count > 0
        assert prevention_failed

    @pytest.mark.unit
    def test_prevention_mode_zero_em_dashes_passes(self) -> None:
        """Scenario: In prevention mode, zero em dashes passes."""
        text = "The system handles requests and returns results quickly."
        em_dash_count = text.count("—")
        assert em_dash_count == 0
        prevention_failed = em_dash_count > 0
        assert not prevention_failed


class TestTier5SmartQuotes:
    """Feature: Detect smart quotes outside code blocks."""

    @pytest.fixture
    def smart_quote_pattern(self) -> re.Pattern:
        return re.compile(r"[“”‘’]")

    @pytest.mark.unit
    def test_detects_curly_double_quotes(self, smart_quote_pattern: re.Pattern) -> None:
        """Scenario: Detect curly double quotes (“”)."""
        text = "The skill returns a “finding” for each match."
        matches = smart_quote_pattern.findall(text)
        assert len(matches) == 2

    @pytest.mark.unit
    def test_detects_curly_single_quotes(self, smart_quote_pattern: re.Pattern) -> None:
        """Scenario: Detect curly single quotes (‘’)."""
        text = "The flag ‘--strict’ enables prevention mode."
        matches = smart_quote_pattern.findall(text)
        assert len(matches) == 2

    @pytest.mark.unit
    def test_straight_quotes_pass(self, smart_quote_pattern: re.Pattern) -> None:
        """Scenario: Straight quotes do not match."""
        text = 'The skill returns a "finding" for each match.'
        matches = smart_quote_pattern.findall(text)
        assert len(matches) == 0


class TestTier5ContrastiveParallelism:
    """Feature: Detect affirmative contrastive parallelism (antithesis).

    Contrastive negation ("not X, but Y") is covered by
    TestTier5NegativeParallelism. This class covers the affirmative
    sibling: two parallel clauses set in opposition with no "not"
    anchor ("Less config, more code"; "Where others X, we Y"). These
    are judgment-level tells: keep them only when the contrast carries
    information that survives removal.

    The regex is sourced from the runtime pattern loader
    (data/languages/en.yaml § tier5.contrastive_parallelism), not from
    an inline fixture, so removing it from the YAML breaks these tests.
    """

    CATEGORY = "contrastive_parallelism"

    @pytest.mark.unit
    def test_category_is_low_confidence(self) -> None:
        """Scenario: Affirmative antithesis never auto-applies."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "low"

    @pytest.mark.unit
    def test_detects_less_more(self) -> None:
        """Scenario: Detect 'Less X, more Y' comparative antithesis."""
        assert _category_hits(self.CATEGORY, "Less config, more code.") == 1

    @pytest.mark.unit
    def test_detects_more_less(self) -> None:
        """Scenario: Detect 'More X, less Y' comparative antithesis."""
        assert _category_hits(self.CATEGORY, "More haste, less speed.") == 1

    @pytest.mark.unit
    def test_less_more_ignores_no_comma(self) -> None:
        """Scenario: 'more X and less Y' (no comma) is not the pattern.

        Plain comparatives joined by "and" are ordinary prose, not the
        antithesis scaffold. Requiring the comma keeps the match tight.
        """
        assert (
            _category_hits(self.CATEGORY, "We added more tests and less mocking.") == 0
        )

    @pytest.mark.unit
    def test_detects_where_contrast(self) -> None:
        """Scenario: Detect 'Where others X, we Y' rhetorical contrast."""
        text = "Where others add complexity, we remove it."
        assert _category_hits(self.CATEGORY, text) == 1

    @pytest.mark.unit
    def test_where_locative_with_noun_passes(self) -> None:
        """Scenario: Locative 'where' with a noun subject does not match.

        The pronoun guard means "Where the config is stored, the
        system reads it" is left alone (subject is "the system").
        """
        text = "Where the config is stored, the system reads it."
        assert _category_hits(self.CATEGORY, text) == 0

    @pytest.mark.unit
    def test_positive_statement_passes(self) -> None:
        """Scenario: A direct positive statement matches no pattern."""
        text = "The config is small and the code is short."
        assert _category_hits(self.CATEGORY, text) == 0


class TestTier5SemicolonSplice:
    """Feature: Detect prose semicolons that read more naturally rephrased.

    Newer models reach for the semicolon as a sophistication marker,
    splicing two independent clauses where a period or a coordinating
    conjunction ("and", "but", "so") reads more naturally. The policy
    is "semicolons in prose only when absolutely necessary", so this
    category surfaces every prose semicolon for human judgment rather
    than auto-rewriting: a list whose items carry internal commas is a
    legitimate keep, a spliced clause is not.

    The regex is sourced from the runtime pattern loader
    (data/languages/en.yaml § tier5.semicolon_splice), not from an
    inline fixture, so removing it from the YAML breaks these tests.
    """

    CATEGORY = "semicolon_splice"

    @pytest.mark.unit
    def test_category_is_low_confidence(self) -> None:
        """Scenario: Semicolon findings surface, never auto-apply."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "low"

    @pytest.mark.unit
    def test_detects_clause_splice(self) -> None:
        """Scenario: Detect a semicolon joining two independent clauses."""
        text = "The system is fast; it handles a million requests."
        assert _category_hits(self.CATEGORY, text) == 1

    @pytest.mark.unit
    def test_detects_imperative_splice(self) -> None:
        """Scenario: Detect a semicolon between two imperatives."""
        text = "Run the tests; they validate the change."
        assert _category_hits(self.CATEGORY, text) == 1

    @pytest.mark.unit
    def test_period_passes(self) -> None:
        """Scenario: Two sentences split by a period do not match."""
        text = "The system is fast. It handles a million requests."
        assert _category_hits(self.CATEGORY, text) == 0

    @pytest.mark.unit
    def test_conjunction_passes(self) -> None:
        """Scenario: A coordinating conjunction does not match."""
        text = "The system is fast and it handles a million requests."
        assert _category_hits(self.CATEGORY, text) == 0


class TestTier5PerformativeHonesty:
    """Feature: Detect performative-candor honesty framings.

    Covers the "Honest X" headline trope and adverbial honesty
    throat-clearing ("to be honest", "Honestly,", "full disclosure").
    These read as manufactured authenticity. High confidence per the
    2025-2026 update: broader matching, with the false-positive risk
    in dialogue and affiliate-SEO accepted. Regexes are scoped to
    framing nouns and discourse-marker forms so ordinary uses such
    as "an honest mistake" still pass.

    Sourced from data/languages/en.yaml section tier5.performative_honesty.
    """

    CATEGORY = "performative_honesty"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Honesty findings are high-confidence (aggressive mode)."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    def test_detects_to_be_honest(self) -> None:
        """Scenario: Detect 'to be honest' adverbial opener."""
        assert _category_hits(self.CATEGORY, "To be honest, I didn't expect it.") >= 1

    @pytest.mark.unit
    def test_detects_honestly_comma(self) -> None:
        """Scenario: Detect sentence-initial 'Honestly,'."""
        assert _category_hits(self.CATEGORY, "Honestly, the results surprised us.") >= 1

    @pytest.mark.unit
    def test_detects_honest_review_headline(self) -> None:
        """Scenario: Detect 'An Honest Review' affiliate-SEO headline."""
        assert _category_hits(self.CATEGORY, "An Honest Review of the new model.") >= 1

    @pytest.mark.unit
    def test_detects_the_honest_truth_about(self) -> None:
        """Scenario: Detect 'The Honest Truth About' framing."""
        assert _category_hits(self.CATEGORY, "The Honest Truth About async Rust.") >= 1

    @pytest.mark.unit
    def test_detects_real_talk(self) -> None:
        """Scenario: Detect 'Real talk:' pseudo-authenticity opener."""
        assert _category_hits(self.CATEGORY, "Real talk: the API is fine.") >= 1

    @pytest.mark.unit
    def test_honest_mistake_passes(self) -> None:
        """Guard: 'an honest mistake' is not a framing noun."""
        assert _category_hits(self.CATEGORY, "That was an honest mistake.") == 0

    @pytest.mark.unit
    def test_honest_answer_passes(self) -> None:
        """Guard: 'an honest answer' is not a framing noun."""
        assert _category_hits(self.CATEGORY, "She gave an honest answer.") == 0

    @pytest.mark.unit
    def test_bare_honest_passes(self) -> None:
        """Guard: 'honest' as a plain adjective is not flagged."""
        assert _category_hits(self.CATEGORY, "He did an honest day's work.") == 0


class TestTier5SophisticationMarker:
    """Feature: Detect 'prior art' and adjacent sophistication markers.

    Flags the collocations AI reaches for to sound rigorous in non-
    academic prose: surveying prior art, standing on the shoulders
    of, a body of work, state of the art. Bare "prior art" is NOT
    matched: legitimate patent and academic uses lack the collocation
    trigger and pass. High confidence per the 2025-2026 update; IP-
    adjacent repos can disable the category via .slop-config.yaml.

    Sourced from data/languages/en.yaml section tier5.sophistication_marker.
    """

    CATEGORY = "sophistication_marker"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Sophistication-marker findings are high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    def test_detects_survey_prior_art(self) -> None:
        """Scenario: Detect 'survey the prior art' collocation."""
        assert _category_hits(self.CATEGORY, "We survey the prior art first.") >= 1

    @pytest.mark.unit
    def test_detects_standing_on_shoulders(self) -> None:
        """Scenario: Detect 'standing on the shoulders of' cliche."""
        text = "We stand on the shoulders of giants."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_state_of_the_art(self) -> None:
        """Scenario: Detect 'state of the art' as a vague authority boost."""
        assert _category_hits(self.CATEGORY, "It is state of the art.") >= 1

    @pytest.mark.unit
    def test_detects_body_of_work(self) -> None:
        """Scenario: Detect 'extensive body of work' padding."""
        text = "An extensive body of work supports this."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_patent_prior_art_passes(self) -> None:
        """Guard: a real patent sentence has no collocation trigger."""
        text = "The examiner cited prior art in rejecting claim 1."
        assert _category_hits(self.CATEGORY, text) == 0

    @pytest.mark.unit
    def test_prior_art_search_passes(self) -> None:
        """Guard: 'prior art search' is a legitimate patent term."""
        text = "Run a prior art search before filing."
        assert _category_hits(self.CATEGORY, text) == 0


class TestTier5ParticipialTail:
    """Feature: Detect comma-led present-participle fake-analysis tails.

    AI appends ', highlighting', ', underscoring', ', paving the way
    for' to sentences to manufacture analysis. Requires a leading
    comma so a sentence that merely uses the word does not trip.

    Sourced from data/languages/en.yaml section tier5.participial_tail.
    """

    CATEGORY = "participial_tail"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Participial-tail findings are high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    def test_detects_highlighting_tail(self) -> None:
        """Scenario: Detect ', highlighting' participial tack-on."""
        text = "The team shipped early, highlighting the new API."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_underscoring_tail(self) -> None:
        """Scenario: Detect ', underscoring' significance tack-on."""
        text = "Latency dropped, underscoring the rewrite's value."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_paving_the_way_tail(self) -> None:
        """Scenario: Detect ', paving the way for' cliche tack-on."""
        text = "The merger closed, paving the way for expansion."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_word_without_comma_passes(self) -> None:
        """Guard: 'highlighting' with no leading comma is not a tail."""
        assert _category_hits(self.CATEGORY, "Highlighting is a display verb.") == 0


class TestTier5EmphasisCrutch:
    """Feature: Detect manufactured-importance emphasis terminators.

    'Full stop.', 'Make no mistake', 'Read that again.' are crutches
    AI uses to stamp authority or drama onto a sentence.

    Sourced from data/languages/en.yaml section tier5.emphasis_crutch.
    """

    CATEGORY = "emphasis_crutch"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Emphasis-crutch findings are high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    def test_detects_full_stop(self) -> None:
        """Scenario: Detect 'Full stop.' authority terminator."""
        assert _category_hits(self.CATEGORY, "This is broken. Full stop.") >= 1

    @pytest.mark.unit
    def test_detects_make_no_mistake(self) -> None:
        """Scenario: Detect 'Make no mistake' dramatic declarative."""
        assert _category_hits(self.CATEGORY, "Make no mistake, this matters.") >= 1

    @pytest.mark.unit
    def test_detects_read_that_again(self) -> None:
        """Scenario: Detect 'Read that again.' emphasis crutch."""
        assert _category_hits(self.CATEGORY, "Revenue doubled. Read that again.") >= 1

    @pytest.mark.unit
    def test_full_stop_without_period_passes(self) -> None:
        """Guard: 'full stop' not terminating a sentence is not the crutch."""
        text = "The bus came to a full stop at the light."
        assert _category_hits(self.CATEGORY, text) == 0


class Test2026VocabularyAndPhraseExtensions:
    """Feature: 2025-2026 vocabulary and phrase additions are loadable.

    Guards the tier1 word additions and the rlhf_hedge phrase
    subcategory. Sources the lists from the runtime pattern loader so
    a dropped entry fails here rather than silently leaving a gap.
    """

    @pytest.mark.unit
    def test_new_tier1_words_present(self) -> None:
        """Scenario: The 2026 vocabulary additions are in the tier1 lists."""
        patterns = load_language_patterns("en")
        words: set[str] = set()
        for category in patterns["tier1"].values():
            if isinstance(category, list):
                words.update(w.lower() for w in category)
        for word in (
            "underpin",
            "unravel",
            "demystify",
            "invaluable",
            "esteemed",
            "unwavering",
            "relentless",
            "enlightening",
            "plethora",
        ):
            assert word in words, f"missing tier1 word: {word}"

    @pytest.mark.unit
    def test_throat_clearing_new_openers_present(self) -> None:
        """Scenario: The new throat-clearing openers are wired in."""
        text = "In this guide, we will explore the basics."
        assert _category_hits("throat_clearing", text) >= 1

    @pytest.mark.unit
    def test_rlhf_hedge_phrases_present(self) -> None:
        """Scenario: The rlhf_hedge phrase subcategory is loadable."""
        patterns = load_language_patterns("en")
        hedge = patterns["phrases"].get("rlhf_hedge", {})
        phrase_list = [p.lower() for p in hedge.get("patterns", [])]
        assert "while it is true that" in phrase_list
        assert "it could be argued that" in phrase_list


class TestTier5SpatialCopulaBareForm:
    """Feature: The spatial copula regex covers plural/bare verb forms.

    Issue #646 predicted that ``live in`` already matches via the
    ``lives?`` alternation, making that phrase a documentation-only
    change. This test pins the prediction so a later regex edit that
    drops the optional ``s`` fails loudly.

    Sourced from data/languages/en.yaml section tier5.spatial_copula.
    """

    CATEGORY = "spatial_copula"

    @pytest.mark.unit
    def test_detects_bare_form_live_in(self) -> None:
        """Scenario: Detect the plural/bare 'live in' form."""
        text = "The configs live in the repo root."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_inflected_form_lives_in(self) -> None:
        """Scenario: Detect the singular 'lives in' form."""
        text = "The config lives in the repo root."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_bare_form_sit_between(self) -> None:
        """Scenario: Detect the bare 'sit between' form."""
        text = "Adapters sit between storage and the domain."
        assert _category_hits(self.CATEGORY, text) >= 1


class TestTier5Anthropomorphism:
    """Feature: Detect human agency attributed to non-human subjects.

    Issue #646: giving code, systems, and documents mental states,
    volition, or bodies. High-confidence tier covers mental-state and
    body verbs, which have no literal reading when the subject is a
    module or a cache.

    Sourced from data/languages/en.yaml section tier5.anthropomorphism.
    """

    CATEGORY = "anthropomorphism"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: The high tier is marked high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The scheduler wants to run these in order.",
            "The parser understands nested blocks.",
            "This module knows about the auth layer.",
            "The cache decides what to evict.",
            "The type system tries to help you here.",
            "The linter believes this is unreachable.",
            "The store remembers the last offset.",
            "The resolver forgets stale entries.",
            "The compiler cares about alignment here.",
            "The router is aware of every mounted path.",
            "The client refuses malformed payloads.",
            "The allocator is smart enough to coalesce.",
            "The handler reaches into the request context.",
            "The migration walks the dependency tree.",
            "The gateway speaks to the billing service.",
        ],
    )
    def test_detects_mental_state_and_body_verbs(self, text: str) -> None:
        """Scenario: Non-human subjects taking human-agency verbs."""
        assert _category_hits(self.CATEGORY, text) >= 1, text

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The observer pattern decouples the two sides.",
            # Corpus audit (1445 files): "agent" names an intentional
            # system in this domain, so it belongs with the terms of
            # art rather than the technical subject nouns.
            "The agent tries to end its turn.",
            "An agent decides whether to escalate.",
            "Iterator::next advances the cursor.",
            "Call handler.handle to dispatch the event.",
            "Future::poll returns Pending until ready.",
            "The supervisor restarts the child process.",
            "A zombie process lingers until reaped.",
            "The heartbeat fires every thirty seconds.",
            "She knows the codebase better than anyone.",
            "The reviewer wants a second opinion.",
            "Users understand the tradeoff.",
        ],
    )
    def test_ignores_terms_of_art_and_human_subjects(self, text: str) -> None:
        """Scenario: Domain terms and real human subjects do not fire."""
        assert _category_hits(self.CATEGORY, text) == 0, text


class TestTier5AnthropomorphismMedium:
    """Feature: Detect metaphorical predicates and agency verbs.

    Issue #646 medium tier: surfaced for human judgment, not
    auto-rewritten, because several have legitimate literal uses.

    Sourced from data/languages/en.yaml tier5.anthropomorphism_medium.
    """

    CATEGORY = "anthropomorphism_medium"

    @pytest.mark.unit
    def test_category_is_medium_confidence(self) -> None:
        """Scenario: The medium tier is marked medium-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "medium"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "That interface is the seam between storage and domain.",
            "This adapter is the boundary for all IO.",
            "The registry is the glue holding the plugins together.",
            "The config drives retry behavior.",
            "The API rides on top of the transport layer.",
            "The scheduler rides on the event loop.",
            "That was a real fix, not a workaround.",
            "This does real work on every request.",
        ],
    )
    def test_detects_metaphorical_predicates(self, text: str) -> None:
        """Scenario: Metaphor and emphasis-crutch predicates fire."""
        assert _category_hits(self.CATEGORY, text) >= 1, text

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "Pass a real number to the constructor.",
            "The pipeline is data-driven end to end.",
            "A data driven approach beats guessing.",
            "He drives to work every morning.",
            "She drives the roadmap for this quarter.",
            "The system runs in real time.",
            "A real user reported this crash.",
            "Test with real data before shipping.",
            # Corpus audit: "real work" after a preposition means a
            # non-synthetic workload, contrasted with a test fixture.
            # That is a literal distinction, not an emphasis crutch.
            "Run the gate on real work before enabling it.",
            "Claude B uses the skill for real work.",
            "It knows this is a test rather than real work.",
            # "boundary" modifying a following noun is not a
            # metaphorical predicate nominative.
            "Its spine is the boundary distinction.",
            "This is the seam alignment problem.",
        ],
    )
    def test_ignores_literal_and_domain_uses(self, text: str) -> None:
        """Scenario: Literal senses and fixed compounds do not fire."""
        assert _category_hits(self.CATEGORY, text) == 0, text


class TestTier5AnthropomorphismLow:
    """Feature: Generalized agency verbs are gated off by default.

    Issue #646 low tier: ``handles``, ``manages``, ``owns``, ``talks
    to``, ``sees`` are load-bearing in systems prose. They must be
    available for an opt-in run but must never fire in a default run.

    Sourced from data/languages/en.yaml tier5.anthropomorphism_low.
    """

    CATEGORY = "anthropomorphism_low"

    @pytest.mark.unit
    def test_absent_from_default_run(self) -> None:
        """Scenario: A default load excludes the opt-in category."""
        patterns = load_language_patterns("en")
        names = {e["category"] for e in get_tier5_patterns(patterns)}
        assert self.CATEGORY not in names

    @pytest.mark.unit
    def test_present_when_optional_requested(self) -> None:
        """Scenario: An opt-in load includes the category."""
        patterns = load_language_patterns("en")
        entries = get_tier5_patterns(patterns, include_optional=True)
        names = {e["category"] for e in entries}
        assert self.CATEGORY in names

    @pytest.mark.unit
    def test_category_is_low_confidence(self) -> None:
        """Scenario: The opt-in tier is marked low-confidence."""
        patterns = load_language_patterns("en")
        entry = next(
            e
            for e in get_tier5_patterns(patterns, include_optional=True)
            if e["category"] == self.CATEGORY
        )
        assert entry["confidence"] == "low"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The service handles retries internally.",
            "The pool manages its own connections.",
            "The module owns the schema definition.",
            "The worker talks to the queue directly.",
            "The validator sees the raw payload.",
        ],
    )
    def test_opt_in_run_detects_agency_verbs(self, text: str) -> None:
        """Scenario: With the flag on, agency verbs are reported."""
        patterns = load_language_patterns("en")
        entry = next(
            e
            for e in get_tier5_patterns(patterns, include_optional=True)
            if e["category"] == self.CATEGORY
        )
        flags = re.IGNORECASE if entry["ignore_case"] else 0
        hits = sum(len(re.compile(p, flags).findall(text)) for p in entry["patterns"])
        assert hits >= 1, text


class TestTier5SignificanceCluster:
    """Feature: Detect manufactured historical significance.

    'stands as a testament to', 'marks a turning point', 'left an
    indelible mark' inflate importance the surrounding facts should
    carry on their own.

    Sourced from data/languages/en.yaml section tier5.significance_cluster.
    """

    CATEGORY = "significance_cluster"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Significance-cluster findings are high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    def test_detects_testament(self) -> None:
        """Scenario: Detect 'stands as a testament to'."""
        text = "The release stands as a testament to the team's rigor."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_turning_point(self) -> None:
        """Scenario: Detect 'marks a turning point'."""
        assert _category_hits(self.CATEGORY, "This marks a turning point.") >= 1

    @pytest.mark.unit
    def test_detects_indelible_mark(self) -> None:
        """Scenario: Detect 'indelible mark'."""
        text = "The project left an indelible mark on the ecosystem."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_setting_the_stage(self) -> None:
        """Scenario: Detect 'setting the stage for'."""
        text = "The refactor, setting the stage for future work, landed."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_shaping_the_future(self) -> None:
        """Scenario: Detect 'shaping the future of'."""
        assert _category_hits(self.CATEGORY, "Shaping the future of search.") >= 1

    @pytest.mark.unit
    def test_detects_underscores_the_importance(self) -> None:
        """Scenario: Detect 'underscores the importance of'."""
        text = "This underscores the importance of testing."
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_pivotal_role(self) -> None:
        """Scenario: Detect 'plays a pivotal role'."""
        assert _category_hits(self.CATEGORY, "Caching plays a pivotal role.") >= 1

    @pytest.mark.unit
    def test_literal_stage_direction_passes(self) -> None:
        """Guard: A literal stage is not the significance cluster."""
        text = "The crew was setting the stage lights before the show."
        assert _category_hits(self.CATEGORY, text) == 0

    @pytest.mark.unit
    def test_literal_will_and_testament_passes(self) -> None:
        """Guard: A legal testament is not the inflation pattern."""
        assert _category_hits(self.CATEGORY, "He signed his last testament.") == 0


class TestTier5LoopVocabulary:
    """Feature: Detect loop/cascade metaphor vocabulary.

    'unpack' for explain, 'surface' as a verb for raise/report, 'a
    quiet shift', 'the signal here is' are metaphors that read as
    insight while deferring the actual claim.

    Sourced from data/languages/en.yaml section tier5.loop_vocabulary.
    """

    CATEGORY = "loop_vocabulary"

    @pytest.mark.unit
    def test_category_is_medium_confidence(self) -> None:
        """Scenario: Loop-vocabulary findings are surfaced, not auto-fixed."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "medium"

    @pytest.mark.unit
    def test_detects_unpack_metaphor(self) -> None:
        """Scenario: Detect 'unpack' used for 'explain'."""
        assert _category_hits(self.CATEGORY, "Let's unpack this design.") >= 1

    @pytest.mark.unit
    def test_detects_quiet_shift(self) -> None:
        """Scenario: Detect 'a quiet shift' standing in for the named shift."""
        assert _category_hits(self.CATEGORY, "There is a quiet shift here.") >= 1

    @pytest.mark.unit
    def test_detects_signal_here_is(self) -> None:
        """Scenario: Detect 'the signal here is' for 'the point is'."""
        assert _category_hits(self.CATEGORY, "The signal here is latency.") >= 1

    @pytest.mark.unit
    def test_literal_unpacking_passes(self) -> None:
        """Guard: Literal unpacking (tuples, archives) is not the metaphor."""
        text = "The function unpacks the tuple into three variables."
        assert _category_hits(self.CATEGORY, text) == 0


def _ste_hits(category: str, text: str) -> int:
    """Count matches for one STE category, sourced from the runtime YAML."""
    patterns = load_language_patterns("en")
    for entry in get_ste_patterns(patterns, include_optional=True):
        if entry["category"] == category:
            flags = re.IGNORECASE if entry.get("ignore_case") else 0
            return sum(
                len(re.findall(pattern, text, flags)) for pattern in entry["patterns"]
            )
    raise AssertionError(f"ste category not found in runtime source: {category}")


class TestSTESemicolons:
    """ASD-STE100 rule 8.1 bans the semicolon outright.

    This is stricter than the house ``semicolon_splice`` rule, which
    only flags a semicolon joining two independent clauses.
    """

    CATEGORY = "semicolons"

    @pytest.mark.unit
    def test_detects_a_splicing_semicolon(self) -> None:
        assert _ste_hits(self.CATEGORY, "The system is fast; it scales.") >= 1

    @pytest.mark.unit
    def test_detects_a_list_semicolon_the_house_rule_permits(self) -> None:
        """The house rule keeps this one. STE does not."""
        text = "Use red, which is hot; blue, which is cold; and green."
        assert _ste_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_prose_without_semicolons_passes(self) -> None:
        assert _ste_hits(self.CATEGORY, "The system is fast. It scales.") == 0


class TestSTEBannedTenses:
    """STE permits simple tenses only: no perfect, no continuous."""

    CATEGORY = "banned_tenses"

    @pytest.mark.unit
    def test_detects_present_perfect(self) -> None:
        assert _ste_hits(self.CATEGORY, "The build has finished already.") >= 1

    @pytest.mark.unit
    def test_detects_past_perfect(self) -> None:
        assert _ste_hits(self.CATEGORY, "The job had failed before we saw it.") >= 1

    @pytest.mark.unit
    def test_detects_continuous(self) -> None:
        assert _ste_hits(self.CATEGORY, "The daemon is running the migration.") >= 1

    @pytest.mark.unit
    def test_simple_present_passes(self) -> None:
        assert _ste_hits(self.CATEGORY, "The daemon runs the migration.") == 0

    @pytest.mark.unit
    def test_simple_past_passes(self) -> None:
        assert _ste_hits(self.CATEGORY, "The build finished at noon.") == 0


class TestSTEContractions:
    """STE spells words out. Contractions are not approved forms."""

    CATEGORY = "contractions"

    @pytest.mark.unit
    def test_detects_negative_contraction(self) -> None:
        assert _ste_hits(self.CATEGORY, "Do not worry, it won't break.") >= 1

    @pytest.mark.unit
    def test_detects_pronoun_contraction(self) -> None:
        assert _ste_hits(self.CATEGORY, "It's ready and we'll ship it.") >= 2

    @pytest.mark.unit
    def test_possessive_apostrophe_passes(self) -> None:
        """A possessive is not a contraction."""
        assert _ste_hits(self.CATEGORY, "The daemon's log file grew.") == 0

    @pytest.mark.unit
    def test_expanded_forms_pass(self) -> None:
        assert _ste_hits(self.CATEGORY, "It is ready and we will ship it.") == 0


class TestSTEPassiveVoice:
    """STE requires the active voice in procedures."""

    CATEGORY = "passive_voice"

    @pytest.mark.unit
    def test_detects_passive_with_agent(self) -> None:
        text = "The migration was executed by the daemon."
        assert _ste_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    def test_detects_agentless_passive(self) -> None:
        assert _ste_hits(self.CATEGORY, "The file is removed automatically.") >= 1

    @pytest.mark.unit
    def test_active_voice_passes(self) -> None:
        assert _ste_hits(self.CATEGORY, "The daemon executes the migration.") == 0


class TestTier5Litotes:
    """Feature: Detect double negation used where a positive form exists.

    "not uncommon", "not unlike", "never fails to" say a positive thing
    through two negations, which costs the reader a step and buys
    nothing. The positive form always exists, so these are safe to
    rewrite rather than merely surface.

    Sourced from data/languages/en.yaml section tier5.litotes.
    """

    CATEGORY = "litotes"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Litotes findings are high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    def test_category_is_enabled_by_default(self) -> None:
        """Scenario: The positive rewrite is unambiguous, so it runs by default."""
        assert _tier5_category(self.CATEGORY)["default_enabled"] is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "This failure mode is not uncommon in production.",
            "The syntax is not unlike Python's.",
            "The change is not unreasonable.",
            "The cost is not insignificant.",
            "It never fails to surface the same bug.",
            "The argument is not without merit.",
        ],
    )
    def test_detects_double_negation(self, text: str) -> None:
        """Scenario: A negated negative is flagged for positive rewrite."""
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The key was not until 2.1.85 recognized by the harness.",
            "The gate does not sit in the matcher group.",
            "The value is not inside the cache file.",
            "This does not include the hook subset.",
            "The estimate is not intended to be exact.",
        ],
    )
    def test_plain_negation_is_not_litotes(self, text: str) -> None:
        """Guard: 'not' before a word starting un-/in- is not double negation.

        A stem list rather than a bare ``not\\s+(?:un|in)\\w+`` is what
        keeps "not until", "not inside" and "not include" out. Those
        three appear throughout this repository's own prose.
        """
        assert _category_hits(self.CATEGORY, text) == 0


class TestTier5VacuousNegation:
    """Feature: Detect negation clichés that assert importance and stop.

    "cannot be overstated" and "it goes without saying" are filler in
    negative dress: they claim weight without supplying any, and the
    sentence reads the same with them deleted.

    Sourced from data/languages/en.yaml section tier5.vacuous_negation.
    """

    CATEGORY = "vacuous_negation"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: Vacuous-negation findings are high-confidence."""
        assert _tier5_category(self.CATEGORY)["confidence"] == "high"

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The importance of this cannot be overstated.",
            "Its value cannot be overemphasized.",
            "The risk is not to be underestimated.",
            "It goes without saying that tests matter.",
            "Needless to say, the build broke.",
            "Shipping this was no small feat.",
            "It is not hard to see why this fails.",
        ],
    )
    def test_detects_vacuous_negation(self, text: str) -> None:
        """Scenario: A negation cliché carrying no information is flagged."""
        assert _category_hits(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The estimate cannot be verified from this machine.",
            "The hook cannot reach the registry, so it warns.",
            "This claim is not supported by the measurement.",
        ],
    )
    def test_substantive_negation_passes(self, text: str) -> None:
        """Guard: negation that carries a real fact is not the cliché."""
        assert _category_hits(self.CATEGORY, text) == 0


class TestTier5NegativeDefinition:
    """Feature: Surface behavior described only by what it will not do.

    "the parser doesn't handle nested blocks" leaves the reader to infer
    what it does handle. The positive form is usually shorter and always
    more useful.

    This is the category that must stay opt-in. Precise negation is how
    contracts, invariants and trust boundaries are correctly written,
    and this repository's own rule files are built out of "do not use
    for", "must not", and "never". A default-on version would bury a
    real finding under hundreds of correct sentences, which is the
    failure mode ``anthropomorphism_low`` was gated off for.

    Sourced from data/languages/en.yaml section tier5.negative_definition.
    """

    CATEGORY = "negative_definition"

    @pytest.mark.unit
    def test_category_is_opt_in(self) -> None:
        """Scenario: The category stays out of a default sweep."""
        entry = _tier5_category_including_optional(self.CATEGORY)
        assert entry["default_enabled"] is False

    @pytest.mark.unit
    def test_category_is_low_confidence(self) -> None:
        """Scenario: Hits are surfaced for judgment, never auto-rewritten."""
        entry = _tier5_category_including_optional(self.CATEGORY)
        assert entry["confidence"] == "low"

    @pytest.mark.unit
    def test_default_sweep_excludes_the_category(self) -> None:
        """Scenario: A routine run does not load it."""
        patterns = load_language_patterns("en")
        default_categories = {
            entry["category"] for entry in get_tier5_patterns(patterns)
        }
        assert self.CATEGORY not in default_categories

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The parser doesn't handle nested blocks.",
            "The exporter does not support CSV.",
            "The daemon is unable to recover from a partial write.",
            "The probe fails to detect a stale session.",
            "This helper cannot handle Unicode paths.",
        ],
    )
    def test_detects_negative_definition(self, text: str) -> None:
        """Scenario: Capability stated only in the negative is surfaced."""
        assert _category_hits_including_optional(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The write must not follow a symlink.",
            "Do not use this for ops; use night-market-operations.",
            "The hook never gates anything when the key is misplaced.",
        ],
    )
    def test_imperative_and_invariant_negation_passes(self, text: str) -> None:
        """Guard: prohibitions and invariants are precision, not slop.

        These three shapes carry the repository's trust boundaries. A
        pattern that caught them would make the category unusable even
        as an opt-in.
        """
        assert _category_hits_including_optional(self.CATEGORY, text) == 0


class TestContrastiveNegationTrailing:
    """The trailing corrective that survives proofreading.

    Review on PR #662 flagged `README.md`: "The third sends your code,
    not just a status check." The `negative_parallelism` bare-trailing
    regex needs the sentence to end one word after "not", so a three-word
    tail slips through. Every AI-writing source that names contrastive
    negation names this surface form, so the miss was in the regex rather
    than in the category.

    Forms covered here come from the cross-source sweep run for that
    review: the mid-sentence "X, not just Y" tail, "isn't just X, but Y",
    "more than X, it's Y", and "not about X, it's about Y".
    """

    @pytest.mark.unit
    def test_detects_mid_sentence_not_just_tail(self) -> None:
        """Scenario: the exact README sentence that review flagged."""
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "The third sends your code, not just a status check.",
            )
            >= 1
        )

    @pytest.mark.unit
    def test_detects_not_just_tail_mid_clause(self) -> None:
        """Scenario: the tail continues into another clause, no period."""
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "It runs the tool, not just a description of it, and reports.",
            )
            >= 1
        )

    @pytest.mark.unit
    def test_detects_isnt_just_but_form(self) -> None:
        """Scenario: 'isn't just X, but Y' correction."""
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "This isn't just a linter, but a whole review harness.",
            )
            >= 1
        )

    @pytest.mark.unit
    def test_detects_more_than_copula_form(self) -> None:
        """Scenario: 'more than X, it's Y' elevation."""
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "It is more than a document, it's a co-editing surface.",
            )
            >= 1
        )

    @pytest.mark.unit
    def test_detects_not_about_it_is_about_form(self) -> None:
        """Scenario: 'not about X, it's about Y' reframing."""
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "This is not about looking modern, it's about being usable.",
            )
            >= 1
        )

    @pytest.mark.unit
    def test_plain_exclusion_is_not_flagged(self) -> None:
        """Guard: 'not' carrying a fact is left alone.

        "The probe does not run" states a behavior. Only the corrective
        scaffold, where a negated half exists to set up an affirmed half,
        is the tell.
        """
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "The probe does not run, because gemini authenticates by key.",
            )
            == 0
        )

    @pytest.mark.unit
    def test_comparative_more_than_is_not_flagged(self) -> None:
        """Guard: an ordinary comparison must not trip the elevation regex."""
        assert (
            _category_hits(
                "contrastive_negation_trailing",
                "The sweep found more than fifteen files across seven plugins.",
            )
            == 0
        )


class TestContrastiveScaffold:
    """ "Rather than" and "instead of" as a definitional frame.

    Review on PR #662 asked that "does X instead of Y" and "does X rather
    than Y" be caught. The research run for it does not support treating
    either as an AI tell on its own: no source in the contrastive-negation
    literature names them, and both are ordinary English connectives. This
    repository writes "rather than" 504 times and "instead of" 299 times
    in its own markdown, almost all correctly, including in the rule files
    that define house style.

    So the category ships the way ``negative_definition`` does: off by
    default, low confidence, surfaced for a human and never scored toward
    the merge gate. It is scoped to the verb-phrase scaffold, where the
    connective joins two actions to define one by the other, rather than
    to the bare connective.

    Sourced from data/languages/en.yaml section tier5.contrastive_scaffold.
    """

    CATEGORY = "contrastive_scaffold"

    @pytest.mark.unit
    def test_category_is_opt_in(self) -> None:
        """Scenario: The category stays out of a default sweep."""
        entry = _tier5_category_including_optional(self.CATEGORY)
        assert entry["default_enabled"] is False

    @pytest.mark.unit
    def test_category_is_low_confidence(self) -> None:
        """Scenario: Hits are surfaced for judgment, never scored."""
        entry = _tier5_category_including_optional(self.CATEGORY)
        assert entry["confidence"] == "low"

    @pytest.mark.unit
    def test_default_sweep_excludes_the_category(self) -> None:
        """Scenario: A routine run does not load it."""
        patterns = load_language_patterns("en")
        default_categories = {
            entry["category"] for entry in get_tier5_patterns(patterns)
        }
        assert self.CATEGORY not in default_categories

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The gate reports the failure rather than swallowing it.",
            "It raises instead of falling back to a guess.",
            "The probe records the version rather than inferring it.",
        ],
    )
    def test_detects_verb_phrase_scaffold(self, text: str) -> None:
        """Scenario: Two actions joined to define one by the other."""
        assert _category_hits_including_optional(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "Use rg rather than grep for file search.",
            "Pass argv instead of a joined string.",
            "Prefer a frozen dataclass rather than a dict.",
        ],
    )
    def test_noun_comparison_is_not_flagged(self, text: str) -> None:
        """Guard: a recommendation between two nouns is ordinary prose.

        Rewriting one loses the alternative the reader needed.
        """
        assert _category_hits_including_optional(self.CATEGORY, text) == 0


class TestTier5OverExplanation:
    """Feature: narration wrapped around a fix, in place of the fix.

    A changelog entry, a commit body or a PR description that explains
    its own reasoning at length costs the reader more than the change
    it describes. The tells are connectives that promise a consequence
    and then restate the sentence before them: "in order to", "this
    ensures that", "the reason for this is".

    Low confidence and opt-in on purpose. "In order to" is correct in a
    sentence that genuinely states a purpose, and the boundary between
    useful rationale and narration is a judgment a person makes. This
    category surfaces candidates; it never rewrites and never gates.

    Sourced from data/languages/en.yaml section tier5.over_explanation.
    """

    CATEGORY = "over_explanation"

    @pytest.mark.unit
    def test_category_is_opt_in(self) -> None:
        """Scenario: a routine sweep does not carry it."""
        entry = _tier5_category_including_optional(self.CATEGORY)
        assert entry["default_enabled"] is False

    @pytest.mark.unit
    def test_category_is_low_confidence(self) -> None:
        """Scenario: hits are surfaced for judgment, never auto-rewritten."""
        entry = _tier5_category_including_optional(self.CATEGORY)
        assert entry["confidence"] == "low"

    @pytest.mark.unit
    def test_default_sweep_excludes_the_category(self) -> None:
        """Guard: the merge bar does not move."""
        patterns = load_language_patterns("en")
        default_categories = {
            entry["category"] for entry in get_tier5_patterns(patterns)
        }
        assert self.CATEGORY not in default_categories

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "In order to fix the race, the lock now wraps the write.",
            "This ensures that the cache stays consistent across restarts.",
            "This means that the exporter now emits one row per session.",
            "The reason for this is that the probe ran before the daemon.",
            "The hook was rewritten, which allows us to drop the retry loop.",
            "It is important to note that the flag defaults to off.",
        ],
    )
    def test_detects_narration(self, text: str) -> None:
        """Scenario: the connective promises a consequence and restates."""
        assert _category_hits_including_optional(self.CATEGORY, text) >= 1

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text",
        [
            "The lock now wraps the write, closing the race.",
            "Run the migration in order.",
            "The cache stays consistent across restarts.",
            "Order matters here: the probe must run after the daemon.",
        ],
    )
    def test_a_stated_fix_passes(self, text: str) -> None:
        """Guard: stating what changed is the target shape, not the tell."""
        assert _category_hits_including_optional(self.CATEGORY, text) == 0


class TestInvisibleUnicode:
    """Characters that occupy a document without appearing in it.

    Three distinct hazards share one shape. A bidi override reorders
    what a reader sees without changing what a compiler reads, which is
    the Trojan Source attack. A tag character is a deprecated codepoint
    with no rendering, which makes it a carrier for instructions aimed
    at a model rather than a person. A zero-width space silently breaks
    an exact-match assertion, a YAML key, or a grep pattern.

    None of them announce themselves in a diff, a terminal, or a code
    review, which is why a detector is the only thing that finds them.

    Scoped to codepoints with no legitimate use in this content. The
    emoji joiners are deliberately absent: U+200D and U+FE0F build
    ordinary emoji sequences, U+200C is required in Persian and several
    Indic scripts, and a category that fires on a warning sign in a
    README is one nobody keeps running.

    Every fixture below is an escape rather than a literal character,
    and has to stay one. bandit's B613 fails any Python source file
    carrying a bidirectional control, which is correct: a test file
    full of literal overrides is the hazard it describes. The escape
    produces the same codepoint at runtime and leaves the file ASCII.

    Sourced from data/languages/en.yaml section tier5.invisible_unicode.
    """

    CATEGORY = "invisible_unicode"

    @pytest.mark.unit
    def test_category_is_high_confidence(self) -> None:
        """Scenario: a hit is a defect, not a judgment call."""
        entry = _tier5_category(self.CATEGORY)
        assert entry["confidence"] == "high"

    @pytest.mark.unit
    def test_default_sweep_carries_the_category(self) -> None:
        """Guard: an opt-in security check is one nobody opts into."""
        patterns = load_language_patterns("en")
        assert self.CATEGORY in {
            entry["category"] for entry in get_tier5_patterns(patterns)
        }

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("codepoint", "why"),
        [
            ("\u200b", "zero width space breaks an exact-match assertion"),
            ("\u00ad", "soft hyphen splits a word only when it wraps"),
            ("\u200e", "left-to-right mark"),
            ("\u200f", "right-to-left mark"),
            ("\u202e", "right-to-left override is Trojan Source"),
            ("\u202d", "left-to-right override"),
            ("\u2066", "left-to-right isolate"),
            ("\u2069", "pop directional isolate"),
            ("\u2060", "word joiner"),
            ("\u2062", "invisible times"),
            ("\ufff9", "interlinear annotation anchor"),
            ("\U000e0041", "tag character, a model-directed carrier"),
            ("\U000e007f", "cancel tag"),
            ("\ufdd0", "noncharacter, never valid in interchange"),
            ("\ufffe", "noncharacter"),
        ],
    )
    def test_detects_the_codepoint(self, codepoint: str, why: str) -> None:
        """Scenario: the character sits in prose and renders as nothing."""
        assert _category_hits(self.CATEGORY, f"The gate{codepoint} holds.") >= 1, why

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("text", "why"),
        [
            ("A warning sign: ⚠\ufe0f see below.", "VS16 renders an emoji"),
            ("Family: \U0001f468\u200d\U0001f469\u200d\U0001f467", "ZWJ sequence"),
            ("Persian needs \u200c between letters.", "ZWNJ is a real letter join"),
            ("Plain ASCII prose with no tricks.", "the ordinary case"),
            ("An em dash lives here: — and that is a different rule.", "em dash"),
        ],
    )
    def test_legitimate_text_is_not_flagged(self, text: str, why: str) -> None:
        """Guard: a check that fires on a README emoji gets turned off."""
        assert _category_hits(self.CATEGORY, text) == 0, why

    @pytest.mark.unit
    def test_a_leading_byte_order_mark_is_not_a_finding(self) -> None:
        """Guard: U+FEFF opens a file legitimately; mid-file it does not."""
        assert _category_hits(self.CATEGORY, "\ufeffThe file starts here.") == 0
        assert _category_hits(self.CATEGORY, "Mid\ufefffile is a defect.") >= 1
