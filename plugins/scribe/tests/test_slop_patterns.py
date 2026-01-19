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
