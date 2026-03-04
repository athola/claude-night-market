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
    get_all_language_patterns,
    get_calibration_factor,
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
    def test_load_portuguese_patterns(self) -> None:
        """Portuguese patterns load with core categories."""
        patterns = load_language_patterns("pt")
        assert patterns["language"] == "pt"
        assert "tier1" in patterns
        assert "tier2" in patterns

    @pytest.mark.unit
    def test_load_italian_patterns(self) -> None:
        """Italian patterns load with core categories."""
        patterns = load_language_patterns("it")
        assert patterns["language"] == "it"
        assert "tier1" in patterns
        assert "tier2" in patterns

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
    def test_detect_portuguese(self) -> None:
        """Detects Portuguese text correctly."""
        text = (
            "O sistema processa os pedidos com eficiência. Os dados são "
            "armazenados na base de dados e não são partilhados com terceiros."
        )
        assert detect_language(text) == "pt"

    @pytest.mark.unit
    def test_detect_italian(self) -> None:
        """Detects Italian text correctly."""
        text = (
            "Il sistema elabora le richieste in modo efficiente. I dati non "
            "vengono condivisi con terzi e questo è fondamentale per la privacy."
        )
        assert detect_language(text) == "it"

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
        assert "pt" in codes
        assert "it" in codes

    @pytest.mark.unit
    def test_language_entries_have_names(self) -> None:
        """Each language entry includes a human-readable name."""
        langs = list_supported_languages()
        for lang in langs:
            assert "name" in lang
            assert len(lang["name"]) > 0


class TestCalibrationFactor:
    """Feature: Language-specific scoring calibration."""

    @pytest.mark.unit
    def test_english_calibration_is_baseline(self) -> None:
        """English calibration factor is 1.0 (baseline)."""
        assert get_calibration_factor("en") == 1.0

    @pytest.mark.unit
    def test_german_calibration_below_baseline(self) -> None:
        """German calibration factor is less than 1.0."""
        assert get_calibration_factor("de") < 1.0

    @pytest.mark.unit
    def test_french_calibration_below_baseline(self) -> None:
        """French calibration factor is less than 1.0."""
        assert get_calibration_factor("fr") < 1.0

    @pytest.mark.unit
    def test_portuguese_calibration_below_baseline(self) -> None:
        """Portuguese calibration factor is less than 1.0."""
        assert get_calibration_factor("pt") < 1.0

    @pytest.mark.unit
    def test_italian_calibration_below_baseline(self) -> None:
        """Italian calibration factor is less than 1.0."""
        assert get_calibration_factor("it") < 1.0

    @pytest.mark.unit
    def test_unknown_language_defaults_to_one(self) -> None:
        """Unknown language code returns 1.0 (no adjustment)."""
        assert get_calibration_factor("xx") == 1.0


class TestGetAllLanguagePatterns:
    """Feature: Batch-load patterns for multiple languages."""

    @pytest.mark.unit
    def test_loads_all_languages_by_default(self) -> None:
        """Calling with no args loads all supported languages."""
        all_patterns = get_all_language_patterns()
        assert "en" in all_patterns
        assert "de" in all_patterns
        assert "fr" in all_patterns
        assert "es" in all_patterns
        assert "pt" in all_patterns
        assert "it" in all_patterns

    @pytest.mark.unit
    def test_loads_subset_of_languages(self) -> None:
        """Providing a list loads only the requested languages."""
        result = get_all_language_patterns(["en", "de"])
        assert "en" in result
        assert "de" in result
        assert "fr" not in result

    @pytest.mark.unit
    def test_unsupported_language_skipped(self) -> None:
        """Unsupported language codes are silently skipped."""
        result = get_all_language_patterns(["en", "xx"])
        assert "en" in result
        assert "xx" not in result

    @pytest.mark.unit
    def test_each_entry_contains_tier1(self) -> None:
        """Every loaded language entry includes tier1 data."""
        result = get_all_language_patterns(["en", "pt", "it"])
        for lang, patterns in result.items():
            assert "tier1" in patterns, f"Missing tier1 for {lang}"
