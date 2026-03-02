"""Language-aware pattern loading for slop detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Default language
DEFAULT_LANGUAGE = "en"

# Supported languages
SUPPORTED_LANGUAGES = {"en", "de", "fr", "es"}

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "languages"


def load_language_patterns(language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Load slop patterns for a specific language.

    Args:
        language: ISO 639-1 language code (en, de, fr, es).

    Returns:
        Dictionary of pattern tiers and categories.

    Raises:
        ValueError: If language is not supported.
        FileNotFoundError: If pattern file is missing.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )

    pattern_file = DATA_DIR / f"{language}.yaml"
    if not pattern_file.exists():
        raise FileNotFoundError(f"Pattern file not found: {pattern_file}")

    with open(pattern_file) as f:
        return yaml.safe_load(f)


def get_tier1_words(patterns: dict[str, Any]) -> list[str]:
    """Extract all tier 1 words from loaded patterns."""
    tier1 = patterns.get("tier1", {})
    words: list[str] = []
    for category in tier1.values():
        if isinstance(category, list):
            words.extend(category)
    return words


def get_tier2_words(patterns: dict[str, Any]) -> list[str]:
    """Extract all tier 2 words from loaded patterns."""
    tier2 = patterns.get("tier2", {})
    words: list[str] = []
    for category in tier2.values():
        if isinstance(category, list):
            words.extend(category)
    return words


def get_phrase_patterns(patterns: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract phrase patterns with scores from loaded patterns."""
    phrases = patterns.get("phrases", {})
    result: list[dict[str, Any]] = []
    for category_name, category_data in phrases.items():
        if isinstance(category_data, dict):
            score = category_data.get("score", 2)
            for pattern in category_data.get("patterns", []):
                result.append(
                    {"pattern": pattern, "score": score, "category": category_name}
                )
    return result


def detect_language(text: str) -> str:
    """Simple language detection based on common function words.

    Uses frequency of common function words to determine language.
    Falls back to English if detection confidence is low.

    Args:
        text: Text to analyze.

    Returns:
        ISO 639-1 language code.
    """
    text_lower = text.lower()
    words = text_lower.split()
    word_set = set(words)

    # Common function words per language
    markers: dict[str, set] = {
        "en": {
            "the",
            "is",
            "are",
            "was",
            "were",
            "have",
            "has",
            "been",
            "will",
            "would",
            "could",
            "should",
            "this",
            "that",
            "with",
            "from",
        },
        "de": {
            "der",
            "die",
            "das",
            "ist",
            "sind",
            "war",
            "haben",
            "hat",
            "wird",
            "werden",
            "ein",
            "eine",
            "mit",
            "und",
            "für",
            "auf",
        },
        "fr": {
            "le",
            "la",
            "les",
            "est",
            "sont",
            "avec",
            "dans",
            "pour",
            "une",
            "des",
            "sur",
            "qui",
            "que",
            "pas",
        },
        "es": {
            "el",
            "la",
            "los",
            "las",
            "es",
            "son",
            "con",
            "para",
            "una",
            "del",
            "por",
            "que",
            "como",
        },
    }

    scores: dict[str, int] = {}
    for lang, lang_markers in markers.items():
        overlap = word_set & lang_markers
        scores[lang] = len(overlap)

    if not scores:
        return DEFAULT_LANGUAGE

    best_lang = max(scores, key=lambda k: scores[k])
    # Only return non-English if it has significantly more markers
    if best_lang != "en" and scores[best_lang] > scores.get("en", 0):
        return best_lang

    return DEFAULT_LANGUAGE


def list_supported_languages() -> list[dict[str, str]]:
    """List all supported languages with their names."""
    result: list[dict[str, str]] = []
    for lang_code in sorted(SUPPORTED_LANGUAGES):
        pattern_file = DATA_DIR / f"{lang_code}.yaml"
        if pattern_file.exists():
            with open(pattern_file) as f:
                data = yaml.safe_load(f)
                result.append(
                    {
                        "code": lang_code,
                        "name": data.get("name", lang_code),
                    }
                )
        else:
            result.append({"code": lang_code, "name": lang_code})
    return result
