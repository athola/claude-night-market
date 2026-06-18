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

from scribe.pattern_loader import get_tier5_patterns, load_language_patterns


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
