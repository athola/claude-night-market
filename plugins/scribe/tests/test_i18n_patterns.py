"""Tests for i18n slop pattern detection.

Issue #138: Multi-language support for scribe slop-detector

Tests verify that German, French, and Spanish tier-1 and phrase patterns
are detected correctly, that English-only text does not trigger non-English
patterns, and that language selection from config works as expected.
"""

import re

import pytest

# ---------------------------------------------------------------------------
# Pattern definitions (mirrors modules/i18n-patterns.md)
# ---------------------------------------------------------------------------

DE_TIER1_PATTERNS: list[str] = [
    r"\bumfassend\w*\b",
    r"\bnutzen\b",
    r"\bvielf[äa]ltig\w*\b",
    r"\btiefgreifend\w*\b",
    r"\bbahnbrechend\w*\b",
    r"\bganzheitlich\w*\b",
    r"\bmaßgeblich\w*\b",
    r"\bwegweisend\w*\b",
]

DE_PHRASE_PATTERNS: list[str] = [
    r"in der heutigen schnelllebigen welt",
    r"es sei darauf hingewiesen",
]

FR_TIER1_PATTERNS: list[str] = [
    r"\btirer parti de\b",
    r"\bexhaustif(?:ve)?\b|\bexhaustive\b",
    r"\bpolyvalent\w*\b",
    r"\bincontournable[s]?\b",
    r"\bnovateur\b|\bnovatrice\b",
    r"\bprimordial\w*\b",
]

FR_PHRASE_PATTERNS: list[str] = [
    r"dans le monde d'aujourd'hui",
    r"il convient de noter que",
]

ES_TIER1_PATTERNS: list[str] = [
    r"\baprovechar?\b",
    r"\bintegral[e-z]?\b",
    r"\bpolifac[eé]tico[s]?\b",
    r"\binnovador[a-z]?\b",
    r"\bfundamental[e-z]?\b",
    r"\bimprescindible[s]?\b",
]

ES_PHRASE_PATTERNS: list[str] = [
    r"en el mundo acelerado de hoy",
    r"cabe destacar que",
]

PT_TIER1_PATTERNS: list[str] = [
    r"\balavancar?\b",
    r"\babrangente[s]?\b",
    r"\brobusto[s]?\b",
    r"\bholístico[s]?\b",
    r"\bmeticuloso[s]?\b",
    r"\bprimordial[a-z]?\b",
]

PT_PHRASE_PATTERNS: list[str] = [
    r"no mundo acelerado de hoje",
    r"é importante notar que",
]

IT_TIER1_PATTERNS: list[str] = [
    r"\bsfruttare?\b",
    r"\besaustiv\w+\b",
    r"\brobusto[a-z]?\b",
    r"\bolistic\w+\b",
    r"\bmeticoloso[a-z]?\b",
    r"\bfondamentale[a-z]?\b",
]

IT_PHRASE_PATTERNS: list[str] = [
    r"nel mondo frenetico di oggi",
    r"è importante notare che",
]

# Heuristic function-word counts used for language detection
LANG_FUNCTION_WORDS: dict[str, list[str]] = {
    "de": ["der", "die", "das", "und", "ist", "nicht", "mit", "von"],
    "fr": ["le", "la", "les", "et", "est", "pas", "avec", "une", "dans"],
    "es": ["el", "la", "los", "las", "es", "con", "una", "por", "que"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compile(patterns: list[str]) -> re.Pattern:
    combined = "|".join(f"(?:{p})" for p in patterns)
    return re.compile(combined, re.IGNORECASE)


def count_matches(text: str, patterns: list[str]) -> int:
    pattern = _compile(patterns)
    return len(pattern.findall(text))


def detect_language(text: str) -> str:
    """Return the most likely language code or 'en' if no language scores >= 5."""
    sample = " ".join(text.lower().split()[:200])
    scores: dict[str, int] = {}
    for lang, words in LANG_FUNCTION_WORDS.items():
        scores[lang] = sum(
            len(re.findall(r"\b" + re.escape(w) + r"\b", sample)) for w in words
        )
    best_lang = max(scores, key=lambda k: scores[k])
    return best_lang if scores[best_lang] >= 5 else "en"


def select_patterns(languages: list[str]) -> dict[str, list[str]]:
    """Return combined tier-1 + phrase patterns for the requested languages."""
    mapping = {
        "de": DE_TIER1_PATTERNS + DE_PHRASE_PATTERNS,
        "fr": FR_TIER1_PATTERNS + FR_PHRASE_PATTERNS,
        "es": ES_TIER1_PATTERNS + ES_PHRASE_PATTERNS,
        "pt": PT_TIER1_PATTERNS + PT_PHRASE_PATTERNS,
        "it": IT_TIER1_PATTERNS + IT_PHRASE_PATTERNS,
    }
    result: dict[str, list[str]] = {}
    for lang in languages:
        if lang in mapping:
            result[lang] = mapping[lang]
    return result


# ---------------------------------------------------------------------------
# German tests
# ---------------------------------------------------------------------------


class TestGermanTier1Patterns:
    """Feature: Detect German tier-1 slop words."""

    @pytest.mark.unit
    def test_detects_umfassend(self) -> None:
        """Scenario: 'umfassend' is flagged as a German tier-1 marker."""
        text = "Diese umfassende Lösung deckt alle Bereiche ab."
        assert count_matches(text, DE_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_bahnbrechend(self) -> None:
        """Scenario: 'bahnbrechend' is flagged."""
        text = "Diese bahnbrechende Technologie verändert alles."
        assert count_matches(text, DE_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_wegweisend(self) -> None:
        """Scenario: 'wegweisend' is flagged."""
        text = "Ein wegweisender Ansatz für die Zukunft."
        assert count_matches(text, DE_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_ganzheitlich(self) -> None:
        """Scenario: 'ganzheitlich' is flagged."""
        text = "Unser ganzheitlicher Prozess integriert alle Teams."
        assert count_matches(text, DE_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_german_vapid_opener(self) -> None:
        """Scenario: German vapid opener phrase is flagged."""
        text = "In der heutigen schnelllebigen Welt brauchen wir Lösungen."
        assert count_matches(text, DE_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_german_filler_phrase(self) -> None:
        """Scenario: 'Es sei darauf hingewiesen' is flagged."""
        text = "Es sei darauf hingewiesen, dass dieser Ansatz neu ist."
        assert count_matches(text, DE_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_multiple_german_markers(self) -> None:
        """Scenario: Several German tier-1 words in one passage are all detected."""
        text = (
            "Diese umfassende und ganzheitliche Strategie ist maßgeblich "
            "für unseren wegweisenden Erfolg."
        )
        assert count_matches(text, DE_TIER1_PATTERNS) >= 3


# ---------------------------------------------------------------------------
# French tests
# ---------------------------------------------------------------------------


class TestFrenchTier1Patterns:
    """Feature: Detect French tier-1 slop words."""

    @pytest.mark.unit
    def test_detects_exhaustif(self) -> None:
        """Scenario: 'exhaustif' is flagged as a French tier-1 marker."""
        text = "Ce guide exhaustif couvre tous les cas d'usage."
        assert count_matches(text, FR_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_incontournable(self) -> None:
        """Scenario: 'incontournable' is flagged."""
        text = "Cet outil est devenu incontournable pour les développeurs."
        assert count_matches(text, FR_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_primordial(self) -> None:
        """Scenario: 'primordial' is flagged."""
        text = "Il est primordial de tester votre code avant déploiement."
        assert count_matches(text, FR_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_french_vapid_opener(self) -> None:
        """Scenario: French vapid opener is flagged."""
        text = "Dans le monde d'aujourd'hui, la vitesse est essentielle."
        assert count_matches(text, FR_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_french_filler_phrase(self) -> None:
        """Scenario: 'Il convient de noter que' is flagged."""
        text = "Il convient de noter que cette approche a des limites."
        assert count_matches(text, FR_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_multiple_french_markers(self) -> None:
        """Scenario: Several French tier-1 words in one passage are all detected."""
        text = (
            "Cette solution exhaustive et polyvalente est incontournable "
            "pour tout projet novateur."
        )
        assert count_matches(text, FR_TIER1_PATTERNS) >= 3


# ---------------------------------------------------------------------------
# Spanish tests
# ---------------------------------------------------------------------------


class TestSpanishTier1Patterns:
    """Feature: Detect Spanish tier-1 slop words."""

    @pytest.mark.unit
    def test_detects_aprovechar(self) -> None:
        """Scenario: 'aprovechar' is flagged as a Spanish tier-1 marker."""
        text = "Debemos aprovechar esta oportunidad única."
        assert count_matches(text, ES_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_imprescindible(self) -> None:
        """Scenario: 'imprescindible' is flagged."""
        text = "Esta herramienta es imprescindible para el equipo."
        assert count_matches(text, ES_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_innovador(self) -> None:
        """Scenario: 'innovador' is flagged."""
        text = "Un enfoque innovador para resolver el problema."
        assert count_matches(text, ES_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_spanish_vapid_opener(self) -> None:
        """Scenario: Spanish vapid opener is flagged."""
        text = "En el mundo acelerado de hoy, necesitamos adaptarnos."
        assert count_matches(text, ES_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_spanish_filler_phrase(self) -> None:
        """Scenario: 'Cabe destacar que' is flagged."""
        text = "Cabe destacar que este método reduce el tiempo de entrega."
        assert count_matches(text, ES_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_multiple_spanish_markers(self) -> None:
        """Scenario: Several Spanish tier-1 words in one passage are all detected."""
        text = (
            "Esta solución integral e innovadora es fundamental "
            "e imprescindible para aprovechar el potencial del equipo."
        )
        assert count_matches(text, ES_TIER1_PATTERNS) >= 4


# ---------------------------------------------------------------------------
# Language selection from config
# ---------------------------------------------------------------------------


class TestLanguageSelectionFromConfig:
    """Feature: Language pattern sets are selected based on config."""

    @pytest.mark.unit
    def test_config_selects_german_patterns(self) -> None:
        """Scenario: Config specifying 'de' returns German pattern set."""
        result = select_patterns(["de"])
        assert "de" in result
        assert len(result["de"]) > 0

    @pytest.mark.unit
    def test_config_selects_multiple_languages(self) -> None:
        """Scenario: Config with ['en', 'de', 'fr'] returns de and fr sets."""
        result = select_patterns(["de", "fr"])
        assert "de" in result
        assert "fr" in result
        assert "es" not in result

    @pytest.mark.unit
    def test_unknown_language_code_ignored(self) -> None:
        """Scenario: An unknown language code produces no patterns."""
        result = select_patterns(["xx"])
        assert "xx" not in result
        assert len(result) == 0

    @pytest.mark.unit
    def test_empty_languages_list_returns_empty(self) -> None:
        """Scenario: An empty languages list returns no pattern sets."""
        result = select_patterns([])
        assert result == {}


# ---------------------------------------------------------------------------
# Portuguese tests
# ---------------------------------------------------------------------------


class TestPortugueseTier1Patterns:
    """Feature: Detect Portuguese tier-1 slop words."""

    @pytest.mark.unit
    def test_detects_alavancar(self) -> None:
        """Scenario: 'alavancar' is flagged as a Portuguese tier-1 marker."""
        text = "Precisamos alavancar esta oportunidade única."
        assert count_matches(text, PT_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_abrangente(self) -> None:
        """Scenario: 'abrangente' is flagged."""
        text = "Este guia abrangente cobre todos os casos de uso."
        assert count_matches(text, PT_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_primordial(self) -> None:
        """Scenario: 'primordial' is flagged."""
        text = "É primordial testar o código antes de publicar."
        assert count_matches(text, PT_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_portuguese_vapid_opener(self) -> None:
        """Scenario: Portuguese vapid opener is flagged."""
        text = "No mundo acelerado de hoje, precisamos de soluções rápidas."
        assert count_matches(text, PT_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_portuguese_filler_phrase(self) -> None:
        """Scenario: 'É importante notar que' is flagged."""
        text = "É importante notar que esta abordagem tem limitações."
        assert count_matches(text, PT_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_multiple_portuguese_markers(self) -> None:
        """Scenario: Several Portuguese tier-1 words in one passage are all detected."""
        text = (
            "Esta solução abrangente e robusta é holística "
            "e primordial para alavancar o potencial da equipa."
        )
        assert count_matches(text, PT_TIER1_PATTERNS) >= 3


# ---------------------------------------------------------------------------
# Italian tests
# ---------------------------------------------------------------------------


class TestItalianTier1Patterns:
    """Feature: Detect Italian tier-1 slop words."""

    @pytest.mark.unit
    def test_detects_sfruttare(self) -> None:
        """Scenario: 'sfruttare' is flagged as an Italian tier-1 marker."""
        text = "Dobbiamo sfruttare questa opportunità unica."
        assert count_matches(text, IT_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_esaustivo(self) -> None:
        """Scenario: 'esaustivo' is flagged."""
        text = "Questa guida esaustiva copre tutti i casi d'uso."
        assert count_matches(text, IT_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_fondamentale(self) -> None:
        """Scenario: 'fondamentale' is flagged."""
        text = "È fondamentale testare il codice prima del rilascio."
        assert count_matches(text, IT_TIER1_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_italian_vapid_opener(self) -> None:
        """Scenario: Italian vapid opener is flagged."""
        text = "Nel mondo frenetico di oggi abbiamo bisogno di soluzioni rapide."
        assert count_matches(text, IT_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_detects_italian_filler_phrase(self) -> None:
        """Scenario: 'È importante notare che' is flagged."""
        text = "È importante notare che questo approccio ha dei limiti."
        assert count_matches(text, IT_PHRASE_PATTERNS) >= 1

    @pytest.mark.unit
    def test_multiple_italian_markers(self) -> None:
        """Scenario: Several Italian tier-1 words in one passage are all detected."""
        text = (
            "Questa soluzione esaustiva e robusta è olistica "
            "e fondamentale per sfruttare il potenziale del team."
        )
        assert count_matches(text, IT_TIER1_PATTERNS) >= 3


# ---------------------------------------------------------------------------
# No false positives on English-only text
# ---------------------------------------------------------------------------


class TestNoFalsePositivesOnEnglishText:
    """Feature: English-only text does not match non-English patterns."""

    ENGLISH_SAMPLE = (
        "The system processes requests efficiently. Each request goes through "
        "validation before being stored in the database. Results return within "
        "50ms for most queries, though complex aggregations may take longer."
    )

    @pytest.mark.unit
    def test_english_text_no_german_tier1_match(self) -> None:
        """Scenario: Plain English text does not match German tier-1 patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, DE_TIER1_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_french_tier1_match(self) -> None:
        """Scenario: Plain English text does not match French tier-1 patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, FR_TIER1_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_spanish_tier1_match(self) -> None:
        """Scenario: Plain English text does not match Spanish tier-1 patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, ES_TIER1_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_german_phrase_match(self) -> None:
        """Scenario: Plain English text does not match German phrase patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, DE_PHRASE_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_french_phrase_match(self) -> None:
        """Scenario: Plain English text does not match French phrase patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, FR_PHRASE_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_spanish_phrase_match(self) -> None:
        """Scenario: Plain English text does not match Spanish phrase patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, ES_PHRASE_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_portuguese_tier1_match(self) -> None:
        """Scenario: Plain English text does not match Portuguese tier-1 patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, PT_TIER1_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_portuguese_phrase_match(self) -> None:
        """Scenario: Plain English text does not match Portuguese phrase patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, PT_PHRASE_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_italian_tier1_match(self) -> None:
        """Scenario: Plain English text does not match Italian tier-1 patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, IT_TIER1_PATTERNS) == 0

    @pytest.mark.unit
    def test_english_text_no_italian_phrase_match(self) -> None:
        """Scenario: Plain English text does not match Italian phrase patterns."""
        assert count_matches(self.ENGLISH_SAMPLE, IT_PHRASE_PATTERNS) == 0


# ---------------------------------------------------------------------------
# Mixed-language document handling
# ---------------------------------------------------------------------------


class TestMixedLanguageDocuments:
    """Feature: Mixed-language documents trigger the correct pattern sets."""

    @pytest.mark.unit
    def test_german_section_detected_in_mixed_doc(self) -> None:
        """Scenario: German markers in a bilingual doc are caught."""
        text = (
            "The API returns JSON. "
            "Diese umfassende Lösung ist bahnbrechend und wegweisend."
        )
        assert count_matches(text, DE_TIER1_PATTERNS) >= 2

    @pytest.mark.unit
    def test_french_section_detected_in_mixed_doc(self) -> None:
        """Scenario: French markers in a bilingual doc are caught."""
        text = (
            "The API returns JSON. "
            "Cette solution polyvalente est incontournable pour les équipes."
        )
        assert count_matches(text, FR_TIER1_PATTERNS) >= 2

    @pytest.mark.unit
    def test_spanish_section_detected_in_mixed_doc(self) -> None:
        """Scenario: Spanish markers in a bilingual doc are caught."""
        text = (
            "The API returns JSON. "
            "Esta solución integral e innovadora es imprescindible."
        )
        assert count_matches(text, ES_TIER1_PATTERNS) >= 2

    @pytest.mark.unit
    def test_language_heuristic_detects_german(self) -> None:
        """Scenario: Heuristic correctly identifies a German-heavy document."""
        text = (
            "Das System verarbeitet Anfragen. Die Daten werden in der Datenbank "
            "gespeichert. Der Prozess ist nicht komplex und mit wenigen Schritten "
            "von der Eingabe bis zur Ausgabe abgeschlossen."
        )
        assert detect_language(text) == "de"

    @pytest.mark.unit
    def test_language_heuristic_detects_french(self) -> None:
        """Scenario: Heuristic correctly identifies a French-heavy document."""
        text = (
            "Le système traite les requêtes. Les données sont stockées dans la "
            "base de données. Le processus n'est pas complexe et avec quelques "
            "étapes simples la solution est mise en place dans les délais."
        )
        assert detect_language(text) == "fr"

    @pytest.mark.unit
    def test_language_heuristic_detects_spanish(self) -> None:
        """Scenario: Heuristic correctly identifies a Spanish-heavy document."""
        text = (
            "El sistema procesa las solicitudes. Los datos se almacenan en la "
            "base de datos. El proceso no es complejo y con unos pocos pasos la "
            "solución queda instalada sin problemas para los usuarios."
        )
        assert detect_language(text) == "es"

    @pytest.mark.unit
    def test_language_heuristic_returns_en_for_low_score(self) -> None:
        """Scenario: Sparse non-English text scores below 5 and returns 'en'."""
        text = "API returns JSON. Call the endpoint with a POST request."
        assert detect_language(text) == "en"
