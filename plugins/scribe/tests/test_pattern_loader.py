"""Tests for multi-language pattern loading (Issue #138).

Verifies language pattern YAML files load correctly and that
the detection, extraction, and language identification functions
work across all supported languages.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add src to path so scribe package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scribe.pattern_loader import (
    detect_language,
    get_phrase_patterns,
    get_tier1_words,
    get_tier2_words,
    list_supported_languages,
    load_language_patterns,
)


class TestPatternLoading:
    """Feature: Load language-specific slop patterns from YAML files."""

    @pytest.mark.unit
    def test_load_english_patterns(self) -> None:
        """English patterns load with all tier categories."""
        patterns = load_language_patterns("en")
        assert patterns["language"] == "en"
        assert "tier1" in patterns
        assert "tier2" in patterns
        assert "phrases" in patterns

    @pytest.mark.unit
    def test_load_german_patterns(self) -> None:
        """German patterns load with core categories."""
        patterns = load_language_patterns("de")
        assert patterns["language"] == "de"
        assert "tier1" in patterns
        assert "tier2" in patterns

    @pytest.mark.unit
    def test_load_french_patterns(self) -> None:
        """French patterns load with core categories."""
        patterns = load_language_patterns("fr")
        assert patterns["language"] == "fr"
        assert "tier1" in patterns

    @pytest.mark.unit
    def test_load_spanish_patterns(self) -> None:
        """Spanish patterns load with core categories."""
        patterns = load_language_patterns("es")
        assert patterns["language"] == "es"
        assert "tier1" in patterns

    @pytest.mark.unit
    def test_unsupported_language_raises(self) -> None:
        """Unsupported language code raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported language"):
            load_language_patterns("xx")


class TestWordExtraction:
    """Feature: Extract word lists from loaded patterns."""

    @pytest.mark.unit
    def test_get_tier1_words_english(self) -> None:
        """Tier 1 extraction returns known English slop words."""
        patterns = load_language_patterns("en")
        words = get_tier1_words(patterns)
        assert len(words) > 0
        assert "delve" in words
        assert "tapestry" in words

    @pytest.mark.unit
    def test_get_tier2_words_english(self) -> None:
        """Tier 2 extraction returns transition and hedging words."""
        patterns = load_language_patterns("en")
        words = get_tier2_words(patterns)
        assert len(words) > 0
        assert "moreover" in words
        assert "leverage" in words

    @pytest.mark.unit
    def test_get_tier1_words_german(self) -> None:
        """German tier 1 extraction returns German slop words."""
        patterns = load_language_patterns("de")
        words = get_tier1_words(patterns)
        assert len(words) > 0
        assert "vertiefen" in words

    @pytest.mark.unit
    def test_get_phrase_patterns_with_scores(self) -> None:
        """Phrase patterns include scores and categories."""
        patterns = load_language_patterns("en")
        phrases = get_phrase_patterns(patterns)
        assert len(phrases) > 0
        assert all("score" in p for p in phrases)
        assert all("pattern" in p for p in phrases)
        assert all("category" in p for p in phrases)

    @pytest.mark.unit
    def test_phrase_scores_are_integers(self) -> None:
        """Phrase scores are numeric values."""
        patterns = load_language_patterns("en")
        phrases = get_phrase_patterns(patterns)
        for p in phrases:
            assert isinstance(p["score"], int)


class TestLanguageDetection:
    """Feature: Auto-detect text language from function word frequency."""

    @pytest.mark.unit
    def test_detect_english(self) -> None:
        """Detects English text correctly."""
        text = (
            "The quick brown fox has been jumping over the lazy dog "
            "with great enthusiasm."
        )
        assert detect_language(text) == "en"

    @pytest.mark.unit
    def test_detect_german(self) -> None:
        """Detects German text correctly."""
        text = (
            "Der schnelle braune Fuchs ist über den faulen Hund "
            "mit großer Begeisterung gesprungen und hat dabei "
            "die Landschaft erkundet."
        )
        assert detect_language(text) == "de"

    @pytest.mark.unit
    def test_detect_french(self) -> None:
        """Detects French text correctly."""
        text = (
            "Le renard brun rapide est passé sur le chien paresseux "
            "avec une grande enthousiasme dans les rues de la ville."
        )
        assert detect_language(text) == "fr"

    @pytest.mark.unit
    def test_detect_spanish(self) -> None:
        """Detects Spanish text correctly."""
        text = (
            "El zorro marrón rápido ha saltado sobre el perro perezoso "
            "con gran entusiasmo por las calles de la ciudad."
        )
        assert detect_language(text) == "es"

    @pytest.mark.unit
    def test_defaults_to_english(self) -> None:
        """Short or ambiguous text defaults to English."""
        assert detect_language("hello world") == "en"

    @pytest.mark.unit
    def test_empty_text_defaults_to_english(self) -> None:
        """Empty text defaults to English."""
        assert detect_language("") == "en"


class TestSupportedLanguages:
    """Feature: List available language packs."""

    @pytest.mark.unit
    def test_list_supported_languages(self) -> None:
        """Lists all supported languages with codes and names."""
        langs = list_supported_languages()
        codes = {lang["code"] for lang in langs}
        assert "en" in codes
        assert "de" in codes
        assert "fr" in codes
        assert "es" in codes

    @pytest.mark.unit
    def test_language_entries_have_names(self) -> None:
        """Each language entry includes a human-readable name."""
        langs = list_supported_languages()
        for lang in langs:
            assert "name" in lang
            assert len(lang["name"]) > 0
