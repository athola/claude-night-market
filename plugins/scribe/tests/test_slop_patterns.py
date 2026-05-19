"""Tests for AI slop pattern detection.

Issue #36: Plugin: create scribe, a documentation review/update/generation plugin

Tests verify the slop detection patterns work correctly across
vocabulary, structural, and fiction-specific categories.
"""

import re

import pytest


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
