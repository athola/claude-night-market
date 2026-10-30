"""Tests for i18n slop pattern detection against the shipped YAML.

Issue #138: Multi-language support for scribe slop-detector

The patterns under test are `data/languages/{de,fr,es,pt,it}.yaml`,
loaded through `scribe.pattern_loader`. Editing a word or phrase out of
a YAML file turns the matching sample test red.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from scribe.pattern_loader import (  # noqa: E402 - src/ must join sys.path first
    detect_language,
    get_phrase_patterns,
    get_tier1_words,
    load_language_patterns,
)

LANGUAGES = ["de", "fr", "es", "pt", "it"]


def _tier1_regex(language: str) -> re.Pattern[str]:
    """Match each shipped tier-1 lemma plus its inflected endings."""
    words = get_tier1_words(load_language_patterns(language))
    return re.compile(
        r"\b(?:" + "|".join(re.escape(word) for word in words) + r")\w*",
        re.IGNORECASE,
    )


def _phrase_regex(language: str) -> re.Pattern[str]:
    entries = get_phrase_patterns(load_language_patterns(language))
    return re.compile(
        "|".join(re.escape(entry["pattern"]) for entry in entries), re.IGNORECASE
    )


def _tier1_hits(language: str, text: str) -> list[str]:
    return [m.group(0).lower() for m in _tier1_regex(language).finditer(text)]


ENGLISH_SAMPLE = (
    "The system processes requests efficiently. Each request goes through "
    "validation before being stored in the database. Results return within "
    "50ms for most queries, though complex aggregations may take longer."
)


@pytest.mark.unit
class TestShippedDataShape:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_language_file_ships_tier1_words(self, language: str) -> None:
        assert len(get_tier1_words(load_language_patterns(language))) >= 15

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_language_file_ships_phrase_patterns(self, language: str) -> None:
        phrases = get_phrase_patterns(load_language_patterns(language))
        assert len(phrases) >= 5
        assert all(entry["pattern"].strip() for entry in phrases)


@pytest.mark.unit
class TestTier1WordsAreDetected:
    @pytest.mark.parametrize(
        ("language", "text", "lemma"),
        [
            ("de", "Diese umfassende Lösung deckt alle Bereiche ab.", "umfassend"),
            ("de", "Diese bahnbrechende Technologie verändert alles.", "bahnbrechend"),
            ("de", "Ein wegweisender Ansatz für die Zukunft.", "wegweisend"),
            (
                "de",
                "Unser ganzheitlicher Prozess integriert alle Teams.",
                "ganzheitlich",
            ),
            ("fr", "Un rapport exhaustif des résultats.", "exhaustif"),
            ("fr", "Cet outil est incontournable pour les équipes.", "incontournable"),
            ("fr", "Un point primordial du projet.", "primordial"),
            ("es", "Una estrategia integral para el equipo.", "integral"),
            ("es", "Este paso es indispensable para el lanzamiento.", "indispensable"),
            ("es", "Hay que aprovechar la nueva herramienta.", "aprovechar"),
            ("pt", "Uma abordagem abrangente do problema.", "abrangente"),
            ("pt", "Um sistema multifacetado e meticuloso.", "multifacetado"),
            ("it", "Un rapporto esaustivo per il team.", "esaustivo"),
            ("it", "Un approccio olistico al problema.", "olistico"),
        ],
    )
    def test_shipped_word_is_flagged_in_a_sentence(
        self, language: str, text: str, lemma: str
    ) -> None:
        shipped = get_tier1_words(load_language_patterns(language))
        assert lemma in shipped
        assert any(hit.startswith(lemma) for hit in _tier1_hits(language, text))

    def test_several_german_markers_in_one_passage_are_all_found(self) -> None:
        text = (
            "Diese umfassende und ganzheitliche Strategie ist maßgeblich "
            "für unseren wegweisenden Erfolg."
        )
        assert len(_tier1_hits("de", text)) >= 3


@pytest.mark.unit
class TestPhrasesAreDetected:
    @pytest.mark.parametrize(
        ("language", "text"),
        [
            ("de", "In der heutigen schnelllebigen Welt brauchen wir Lösungen."),
            ("de", "Kann nicht genug betont werden, wie wichtig das ist."),
            ("fr", "Il convient de noter que le test a échoué."),
            ("fr", "Cela va sans dire, mais le test est lent."),
            ("es", "En el mundo acelerado de hoy necesitamos soluciones."),
            ("es", "Vale la pena señalar que el test falló."),
            ("pt", "No mundo acelerado de hoje precisamos de soluções."),
            ("pt", "É importante notar que o teste falhou."),
            ("it", "Nel mondo frenetico di oggi servono soluzioni."),
            ("it", "È importante notare che il test è fallito."),
        ],
    )
    def test_shipped_phrase_is_flagged_in_a_sentence(
        self, language: str, text: str
    ) -> None:
        assert _phrase_regex(language).search(text)


@pytest.mark.unit
class TestNoFalsePositivesOnEnglishText:
    @pytest.mark.parametrize("language", LANGUAGES)
    def test_english_text_matches_no_tier1_word(self, language: str) -> None:
        assert _tier1_hits(language, ENGLISH_SAMPLE) == []

    @pytest.mark.parametrize("language", LANGUAGES)
    def test_english_text_matches_no_phrase(self, language: str) -> None:
        assert _phrase_regex(language).search(ENGLISH_SAMPLE) is None


@pytest.mark.unit
class TestMixedLanguageDocuments:
    @pytest.mark.parametrize(
        ("language", "text"),
        [
            (
                "de",
                "The API returns JSON. Diese umfassende Lösung ist bahnbrechend "
                "und wegweisend.",
            ),
            (
                "fr",
                "The API returns JSON. Cette solution est incontournable et "
                "primordiale pour les équipes.",
            ),
            (
                "es",
                "The API returns JSON. Esta solución integral es indispensable.",
            ),
        ],
    )
    def test_foreign_markers_in_a_bilingual_document_are_caught(
        self, language: str, text: str
    ) -> None:
        assert len(_tier1_hits(language, text)) >= 2

    def test_english_sentence_in_a_bilingual_document_adds_no_hits(self) -> None:
        assert _tier1_hits("de", "The API returns JSON.") == []

    def test_language_heuristic_detects_german(self) -> None:
        text = (
            "Das System verarbeitet Anfragen. Die Daten werden in der Datenbank "
            "gespeichert. Der Prozess ist nicht komplex und mit wenigen Schritten "
            "von der Eingabe bis zur Ausgabe abgeschlossen."
        )
        assert detect_language(text) == "de"

    def test_language_heuristic_detects_french(self) -> None:
        text = (
            "Le système traite les requêtes. Les données sont stockées dans la "
            "base de données. Le processus n'est pas complexe et avec quelques "
            "étapes simples la solution est mise en place dans les délais."
        )
        assert detect_language(text) == "fr"

    def test_language_heuristic_detects_spanish(self) -> None:
        text = (
            "El sistema procesa las solicitudes. Los datos se almacenan en la "
            "base de datos. El proceso no es complejo y con unos pocos pasos la "
            "solución queda instalada sin problemas para los usuarios."
        )
        assert detect_language(text) == "es"

    def test_language_heuristic_returns_en_for_sparse_text(self) -> None:
        text = "API returns JSON. Call the endpoint with a POST request."
        assert detect_language(text) == "en"
