"""Language-aware pattern loading for slop detection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

# Default language
DEFAULT_LANGUAGE = "en"

# Supported languages
SUPPORTED_LANGUAGES = {"en", "de", "fr", "es", "pt", "it"}

# Language-specific scoring calibration
# Adjusts sensitivity based on cultural norms (1.0 = English baseline)
LANGUAGE_CALIBRATION: dict[str, float] = {
    "en": 1.0,  # Baseline
    "de": 0.85,  # German: formal register more accepted
    "fr": 0.80,  # French: literary flourishes culturally valued
    "es": 0.85,  # Spanish: formal transitions standard in academic writing
    "pt": 0.85,  # Portuguese: similar to Spanish academic norms
    "it": 0.80,  # Italian: literary style culturally valued
}

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "languages"

# Common function words per language for detect_language()
# NOTE: Italian "it" overlaps the English pronoun "it"; short English texts
# can match Italian. detect_language() guards against this by preferring
# English on ties.
_LANGUAGE_MARKERS: dict[str, frozenset[str]] = {
    "en": frozenset(
        {
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
        }
    ),
    "de": frozenset(
        {
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
        }
    ),
    "fr": frozenset(
        {
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
        }
    ),
    "es": frozenset(
        {
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
        }
    ),
    "pt": frozenset(
        {
            "o",
            "a",
            "os",
            "as",
            "é",
            "são",
            "foi",
            "tem",
            "com",
            "para",
            "uma",
            "dos",
            "por",
            "que",
            "como",
            "não",
        }
    ),
    "it": frozenset(
        {
            "il",
            "la",
            "le",
            "gli",
            "è",
            "sono",
            "con",
            "per",
            "una",
            "del",
            "che",
            "non",
            "più",
            "anche",
            "questo",
            "nella",
        }
    ),
}


def load_language_patterns(language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Load slop patterns for a specific language.

    Args:
        language: ISO 639-1 language code (en, de, fr, es, pt, it).

    Returns:
        Dictionary of pattern tiers and categories.

    Raises:
        ValueError: If language is not supported.
        FileNotFoundError: If pattern file is missing.
    """
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
        )

    pattern_file = DATA_DIR / f"{language}.yaml"
    if not pattern_file.exists():
        raise FileNotFoundError(f"Pattern file not found: {pattern_file}")

    if yaml is None:
        raise ImportError(
            "pyyaml is required to load language patterns. Install it with: pip install pyyaml"
        )

    with open(pattern_file, encoding="utf-8") as f:
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


def get_tier5_patterns(
    patterns: dict[str, Any], include_optional: bool = False
) -> list[dict[str, Any]]:
    """Extract Tier 5 structural patterns from loaded patterns.

    Tier 5 covers the 2026 structural tells (spatial copula, negative
    parallelism, contrastive parallelism, three-fragment burst, smart
    quotes, and similar) as regex rather than word lists. Each category
    carries a score, a confidence level, and an ``ignore_case`` flag so
    callers can compile the regex with the correct flags.

    A category may also set ``default_enabled: false`` to stay out of a
    default sweep. That axis is independent of ``confidence``: a low
    confidence category is one whose hits need human judgment before a
    rewrite, which is not the same as one too noisy to report at all.
    ``anthropomorphism_low`` is the first opt-in category (issue #646);
    its verbs (``handles``, ``manages``, ``owns``) are load-bearing in
    systems prose and would swamp a routine run.

    Languages without a ``tier5`` section return an empty list, which
    lets callers degrade gracefully until a language pack is translated.

    Args:
        patterns: Loaded language pattern dictionary.
        include_optional: Include categories marked
            ``default_enabled: false``. Defaults to False.

    Returns:
        List of dicts, one per category, each with ``category``,
        ``patterns`` (list of regex strings), ``score``, ``confidence``,
        ``ignore_case``, and ``default_enabled``.
    """
    tier5 = patterns.get("tier5", {})
    result: list[dict[str, Any]] = []
    for category_name, category_data in tier5.items():
        if not isinstance(category_data, dict):
            continue
        default_enabled = bool(category_data.get("default_enabled", True))
        if not default_enabled and not include_optional:
            continue
        result.append(
            {
                "category": category_name,
                "patterns": list(category_data.get("patterns", [])),
                "score": category_data.get("score", 2),
                "confidence": category_data.get("confidence", "high"),
                "ignore_case": bool(category_data.get("ignore_case", False)),
                "default_enabled": default_enabled,
            }
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
    word_set = set(text.lower().split())

    scores = {
        lang: len(word_set & lang_markers)
        for lang, lang_markers in _LANGUAGE_MARKERS.items()
    }

    if not scores:
        return DEFAULT_LANGUAGE

    best_lang = max(scores, key=lambda k: scores[k])
    # Only return non-English if it has strictly more markers than English
    if best_lang != "en" and scores[best_lang] > scores.get("en", 0):
        return best_lang

    return DEFAULT_LANGUAGE


def get_calibration_factor(language: str) -> float:
    """Return the scoring calibration factor for a language.

    A factor < 1.0 reduces sensitivity for languages where formal or
    literary register is culturally more accepted than in English.

    Args:
        language: ISO 639-1 language code.

    Returns:
        Calibration multiplier (1.0 = English baseline).
    """
    return LANGUAGE_CALIBRATION.get(language, 1.0)


def get_all_language_patterns(languages: list[str] | None = None) -> dict[str, dict]:
    """Load patterns for multiple languages at once.

    Args:
        languages: List of ISO 639-1 language codes to load.
            Defaults to all supported languages when None.

    Returns:
        Mapping of language code to its loaded pattern dictionary.
        Unsupported or missing languages are silently skipped.
    """
    if languages is None:
        languages = sorted(SUPPORTED_LANGUAGES)

    result: dict[str, dict] = {}
    for lang in languages:
        if lang not in SUPPORTED_LANGUAGES:
            continue
        try:
            result[lang] = load_language_patterns(lang)
        except FileNotFoundError:
            continue
    return result


LANGUAGE_NAMES: dict[str, str] = {
    "de": "German",
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "pt": "Portuguese",
}


def list_supported_languages() -> list[dict[str, str]]:
    """List all supported languages with their names."""
    return [
        {"code": code, "name": LANGUAGE_NAMES.get(code, code)}
        for code in sorted(SUPPORTED_LANGUAGES)
    ]
