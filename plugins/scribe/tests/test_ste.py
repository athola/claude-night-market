"""Tests for the STE-derived structural checks.

Covers the three checks that are not regex properties and therefore
cannot live in ``en.yaml``: sentence length, paragraph length, and noun
clusters. Each needs word-count normalization or noun detection, so it
is implemented in ``scribe.ste`` and tested here.

The corpus is drawn from this repository's own prose so the measured
false-positive rate reflects the text the checks will actually run on.

Sourcing rule, mirroring ``test_slop_patterns.py``: lexicons come from
the runtime YAML through the loader, never from inline fixtures, so
deleting the data files turns these tests red.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scribe.ste import (
    DESCRIPTIVE_MAX_WORDS,
    NOUN_CLUSTER_MAX_WORDS,
    PARAGRAPH_MAX_SENTENCES,
    PROCEDURAL_MAX_WORDS,
    check_paragraph_length,
    check_sentence_length,
    classify_sentence,
    count_words,
    find_noun_clusters,
    load_ste_lexicons,
    split_sentences,
)

# ---------------------------------------------------------------------------
# Limits: the four numbers corroborated across independent sources.
# ---------------------------------------------------------------------------


def test_limits_match_the_corroborated_values():
    """The four STE limits this module enforces.

    Corroborated across four independent restatements. Pinned here so a
    silent retune of any limit fails rather than changing behavior.
    """
    assert PROCEDURAL_MAX_WORDS == 20
    assert DESCRIPTIVE_MAX_WORDS == 25
    assert PARAGRAPH_MAX_SENTENCES == 6
    assert NOUN_CLUSTER_MAX_WORDS == 3


# ---------------------------------------------------------------------------
# Word counting. STE counts fewer words than ``len(text.split())``.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected", "why"),
    [
        ("Run the install script.", 4, "plain words count normally"),
        ("Set the pre-commit hook.", 4, "hyphenated compound is one word"),
        ("Install a version-independent data root.", 5, "hyphen inside phrase"),
        ("Torque the bolt to 25 Nm.", 5, "number with unit is one word"),
        ("Upgrade to 1.9.18 today.", 4, "dotted version is one word"),
        ("Run trust-attestation.yml now.", 3, "a bare filename is one word"),
        ("Open docs/api-overview.md first.", 3, "a path is one word"),
        (
            "Use the value (the default is 30 seconds) here.",
            5,
            "parenthetical span collapses to one word",
        ),
        (
            'Set the label to "Do Not Remove" first.',
            6,
            "quoted placard collapses to one word",
        ),
        (
            "Do not run `git commit --no-verify` on this branch.",
            7,
            "inline code collapses to one word",
        ),
        (
            "Read https://example.com/a/b/c for details.",
            4,
            "a URL is one word",
        ),
        ("", 0, "empty string counts zero"),
        ("   ", 0, "whitespace counts zero"),
    ],
)
def test_count_words_applies_ste_normalization(text, expected, why):
    assert count_words(text) == expected, why


def test_count_words_is_never_greater_than_naive_split():
    """Normalization only ever merges tokens, never splits them."""
    samples = [
        "Set the pre-commit hook to run 25 Nm (the default) now.",
        'Use "Do Not Remove" and version 1.9.18 together.',
        "Plain words with no normalization at all here.",
    ]
    for text in samples:
        assert count_words(text) <= len(text.split()), text


# ---------------------------------------------------------------------------
# Sentence splitting. Abbreviations and versions must not split.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected_count", "why"),
    [
        ("Run the tests. Then stop.", 2, "plain sentence boundary"),
        ("Use rg, e.g. rg foo. Then stop.", 2, "e.g. is not a boundary"),
        ("See Fig. 3 for details.", 1, "Fig. is not a boundary"),
        ("Upgrade to 1.9.18. Then rerun.", 2, "dotted version is not a boundary"),
        ("The value is 0.5 in production.", 1, "a decimal is not a boundary"),
        ("Stop! Then check. Is it clear?", 3, "bang and question mark split"),
        ("i.e. this stays whole.", 1, "i.e. is not a boundary"),
        ("**Bold lead.** Then the next one.", 2, "bold wrapper ends a sentence"),
        ("*Emphasis.* Next.", 2, "single emphasis marker too"),
        ("`code.` Next.", 2, "trailing backtick too"),
        ("", 0, "empty text yields no sentences"),
    ],
)
def test_split_sentences_guards_abbreviations_and_versions(text, expected_count, why):
    assert len(split_sentences(text)) == expected_count, why


def test_split_sentences_reports_line_numbers():
    text = "First line here.\n\nSecond paragraph sentence."
    sentences = split_sentences(text)
    assert sentences[0].line == 1
    assert sentences[-1].line == 3


# ---------------------------------------------------------------------------
# Procedural vs descriptive. STEMG: a checker that cannot tell these
# apart is not implementing STE, because the limits differ.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Run the test suite.", "procedural"),
        ("Install the pre-commit hook.", "procedural"),
        ("Do not merge code you cannot explain.", "procedural"),
        ("Set the version field in every manifest.", "procedural"),
        ("Confirm you are on a topic branch.", "procedural"),
        ("The system stores captures under a cache root.", "descriptive"),
        ("This means the data is unreachable.", "descriptive"),
        ("It fires on the push.", "descriptive"),
        ("Because the root is version scoped, updates orphan it.", "descriptive"),
        ("A migration recovers the stranded captures.", "descriptive"),
    ],
)
def test_classify_sentence_separates_the_two_registers(text, expected):
    kind, _confidence = classify_sentence(text)
    assert kind == expected, text


def test_classify_sentence_returns_confidence_in_unit_range():
    for text in ["Run the tests.", "The system works.", "Roughly so."]:
        _kind, confidence = classify_sentence(text)
        assert 0.0 <= confidence <= 1.0


def test_ordered_list_context_raises_procedural_confidence():
    """A numbered step is a strong structural signal."""
    bare = classify_sentence("Merge to master.")
    listed = classify_sentence("Merge to master.", in_ordered_list=True)
    assert listed[0] == "procedural"
    assert listed[1] > bare[1]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("**Severity Justified**: Classify issues by impact.", "procedural"),
        ("**Specific Findings**: Each issue includes a step.", "descriptive"),
        ("Note: run the migration first.", "procedural"),
        ("**Scope**: The system stores captures.", "descriptive"),
    ],
)
def test_label_prefixes_do_not_hide_the_register(text, expected):
    """A bolded label is a heading for the item, not its first word.

    This repository's list items overwhelmingly open with
    ``**Label**:``. Classifying on the label made four of five list
    items unclassifiable.
    """
    assert classify_sentence(text)[0] == expected


def test_a_colon_mid_sentence_is_not_a_label():
    """Only a short leading label is stripped, never a real clause."""
    text = "The system stores every capture under one root: the data root."
    assert classify_sentence(text)[0] == "descriptive"


def test_unclassifiable_text_is_unknown_not_guessed():
    kind, confidence = classify_sentence("Possibly, in some cases.")
    assert kind == "unknown"
    assert confidence < 0.5


# ---------------------------------------------------------------------------
# Sentence length. Boundary behavior is the whole contract.
# ---------------------------------------------------------------------------


def _procedural_of(n_words: int) -> str:
    """Build an imperative sentence of exactly ``n_words`` STE words."""
    filler = " ".join(["item"] * (n_words - 2))
    return f"Run the {filler}."


def test_procedural_sentence_at_the_limit_is_clean():
    text = _procedural_of(PROCEDURAL_MAX_WORDS)
    assert count_words(text) == PROCEDURAL_MAX_WORDS
    assert check_sentence_length(text) == []


def test_procedural_sentence_over_the_limit_is_flagged():
    text = _procedural_of(PROCEDURAL_MAX_WORDS + 1)
    findings = check_sentence_length(text)
    assert len(findings) == 1
    assert findings[0].rule == "sentence_length"
    assert findings[0].actual == PROCEDURAL_MAX_WORDS + 1
    assert findings[0].limit == PROCEDURAL_MAX_WORDS


def test_descriptive_sentence_uses_the_looser_limit():
    """A descriptive sentence of 22 words is legal; a procedural one is not."""
    filler = " ".join(["thing"] * 19)
    descriptive = f"The system stores {filler}."
    assert count_words(descriptive) == 22
    assert classify_sentence(descriptive)[0] == "descriptive"
    assert check_sentence_length(descriptive) == []


def test_descriptive_sentence_over_its_own_limit_is_flagged():
    filler = " ".join(["thing"] * 23)
    descriptive = f"The system stores {filler}."
    assert count_words(descriptive) == DESCRIPTIVE_MAX_WORDS + 1
    findings = check_sentence_length(descriptive)
    assert len(findings) == 1
    assert findings[0].limit == DESCRIPTIVE_MAX_WORDS


def test_unknown_register_gets_the_lenient_limit():
    """Ambiguous text must not be flagged at the strict procedural cap.

    False positives are what get a check disabled, so uncertainty
    resolves toward silence.
    """
    findings = check_sentence_length("Possibly, in some cases.")
    assert findings == []


# ---------------------------------------------------------------------------
# Paragraph length.
# ---------------------------------------------------------------------------


def test_paragraph_at_the_limit_is_clean():
    para = " ".join(["The system works."] * PARAGRAPH_MAX_SENTENCES)
    assert check_paragraph_length(para) == []


def test_paragraph_over_the_limit_is_flagged():
    para = " ".join(["The system works."] * (PARAGRAPH_MAX_SENTENCES + 1))
    findings = check_paragraph_length(para)
    assert len(findings) == 1
    assert findings[0].rule == "paragraph_length"
    assert findings[0].actual == PARAGRAPH_MAX_SENTENCES + 1


def test_paragraphs_are_counted_independently():
    block = "The system works. " * 4
    text = block.strip() + "\n\n" + block.strip()
    assert check_paragraph_length(text) == []


def test_ordered_list_steps_are_not_one_paragraph():
    """Seven numbered steps are seven procedures, not a run-on paragraph."""
    text = "\n".join(f"{i}. Run the step." for i in range(1, 8))
    assert check_paragraph_length(text) == []


def test_one_overlong_list_item_is_still_flagged():
    """A bullet is exempt from being merged, not from being counted.

    ``_iter_blocks`` already gives each item its own block, so the
    run-on-paragraph confusion cannot happen. Skipping items outright
    on top of that let a single eight-sentence bullet through.
    """
    body = " ".join(["The system works."] * (PARAGRAPH_MAX_SENTENCES + 2))
    findings = check_paragraph_length(f"- {body}")
    assert len(findings) == 1
    assert findings[0].actual == PARAGRAPH_MAX_SENTENCES + 2


def test_a_list_item_at_the_limit_stays_clean():
    body = " ".join(["The system works."] * PARAGRAPH_MAX_SENTENCES)
    assert check_paragraph_length(f"- {body}") == []


# ---------------------------------------------------------------------------
# Noun clusters. Low confidence by construction: surface, do not autofix.
# ---------------------------------------------------------------------------


def test_noun_cluster_over_three_words_is_flagged():
    findings = find_noun_clusters("Check the runtime capture pipeline root now.")
    assert len(findings) == 1
    assert findings[0].rule == "noun_cluster"
    assert findings[0].actual == 4


def test_noun_cluster_at_three_words_is_clean():
    assert find_noun_clusters("Check the capture pipeline root now.") == []


def test_noun_clusters_are_low_confidence():
    """Function-word subtraction is crude, so findings are advisory."""
    findings = find_noun_clusters("Check the runtime capture pipeline root now.")
    assert findings[0].confidence == "low"


def test_function_words_break_a_cluster():
    text = "Check the capture of the pipeline in the root now."
    assert find_noun_clusters(text) == []


def test_a_comma_breaks_a_cluster():
    """List items are separate things, not one long noun.

    "clawhub export, build bridge" is two names. Ignoring the comma
    merged them into a four-word cluster.
    """
    assert find_noun_clusters("Run clawhub export, build bridge now.") == []


def test_a_colon_breaks_a_cluster():
    text = "Check the unit tests: capture pipeline root."
    assert find_noun_clusters(text) == []


def test_inflected_verbs_break_a_cluster():
    """``stores`` is inflected, so it reads as a verb, not a noun."""
    text = "The capture pipeline stores root data now."
    assert find_noun_clusters(text) == []


def test_bare_filenames_do_not_form_noun_clusters():
    """A filename is one thing, not a stack of nouns.

    "trust-attestation.yml fires on the push" tokenized into trust,
    attestation, and yml, which read as a four-word cluster.
    """
    assert find_noun_clusters("trust-attestation.yml fires on the push.") == []


# ---------------------------------------------------------------------------
# Tokenizer defects found by running the checks over 5984 markdown files.
# Each case below is a real finding, reduced. Together they accounted for
# a large share of the noun-cluster noise.
# ---------------------------------------------------------------------------


def test_html_markup_is_not_prose():
    """``<details><summary>`` was the single loudest false positive.

    It produced 2584 identical noun-cluster findings, 11% of every
    cluster reported across the repository.
    """
    text = "<details><summary>Click to expand full content summary</summary>"
    assert find_noun_clusters(text) == []
    assert check_sentence_length(text) == []


def test_inline_html_tags_do_not_join_words_around_them():
    text = "The <b>release</b> is ready."
    assert find_noun_clusters(text) == []


def test_slash_paths_are_one_token():
    text = "Store it under /home/alext/claude/projects/foo/bar now."
    assert find_noun_clusters(text) == []


def test_bare_domain_urls_are_one_token():
    text = "See news.ycombinator.com/item?id=99 for the thread."
    assert find_noun_clusters(text) == []


def test_acronyms_with_digits_stay_whole():
    """``W3C`` tokenized to ``W`` and ``C``, inflating every run.

    The cluster here is real and stays reported. What changes is its
    shape: four nouns rather than six tokens, with the acronym intact
    and the trailing verb excluded.
    """
    findings = find_noun_clusters("The W3C Verifiable Credentials spec applies.")
    assert len(findings) == 1
    assert findings[0].text == "W3C Verifiable Credentials spec"
    assert findings[0].actual == 4


def test_a_short_acronym_phrase_no_longer_reports():
    """``The W3C spec applies.`` held two nouns, and reported six."""
    assert find_noun_clusters("The W3C spec applies.") == []


def test_ies_verbs_break_a_cluster():
    """``applies`` is ``apply`` inflected, so it is a verb, not a noun."""
    assert find_noun_clusters("The runtime capture pipeline applies.") == []


def test_see_is_an_imperative():
    kind, _ = classify_sentence("See the release runbook for the sequence.")
    assert kind == "procedural"


@pytest.mark.parametrize(
    ("text", "expected", "why"),
    [
        ("Wait 30 ms before the retry.", 5, "a number and its unit are one word"),
        ("Wait 5 kg of load.", 4, "unit stays merged"),
        ("It ran for 3 days.", 5, "days is a word, not a unit"),
        ("Read 4 files now.", 4, "files is a word, not a unit"),
    ],
)
def test_number_unit_merging_uses_a_unit_list(text, expected, why):
    assert count_words(text) == expected, why


def test_noun_clusters_ignore_code_and_urls():
    text = "Run `plugins/scribe/src/scribe/pattern_loader.py` now."
    assert find_noun_clusters(text) == []


# ---------------------------------------------------------------------------
# Masking. Code, URLs, and tables are not prose.
# ---------------------------------------------------------------------------


def test_fenced_code_is_not_checked():
    text = (
        "```python\n"
        "the = quick + brown + fox + jumps + over + lazy + dog + again\n"
        "```\n"
    )
    assert check_sentence_length(text) == []
    assert find_noun_clusters(text) == []


def test_markdown_tables_are_not_checked():
    text = "| runtime capture pipeline root | another long noun cluster here |\n"
    assert find_noun_clusters(text) == []


def test_headings_are_not_sentences():
    assert check_sentence_length("## Runtime capture pipeline root\n") == []


def test_yaml_frontmatter_is_not_prose():
    """Skill frontmatter is metadata and must never be measured.

    Every SKILL.md in this repository opens with a ``name``/
    ``description`` block. Counting it as prose made frontmatter the
    single largest source of unclassifiable sentences.
    """
    text = (
        "---\n"
        "name: runtime capture pipeline root\n"
        "description: a description field that runs well past the "
        "twenty word limit for procedural text and would otherwise "
        "be flagged here today\n"
        "---\n"
        "\n"
        "Run the tests.\n"
    )
    assert check_sentence_length(text) == []
    assert find_noun_clusters(text) == []


def test_frontmatter_delimiter_only_counts_at_the_top():
    """A ``---`` rule mid-document is a horizontal rule, not frontmatter."""
    text = "Run the tests.\n\n---\n\nThe system works.\n"
    assert len(split_sentences(text)) == 2
    assert check_sentence_length(text) == []


# ---------------------------------------------------------------------------
# Lexicons come from the runtime YAML, not from inline fixtures.
# ---------------------------------------------------------------------------


def test_lexicons_load_from_the_runtime_data_files():
    lex = load_ste_lexicons()
    assert lex["imperative_verbs"], "imperative verb lexicon is empty"
    assert lex["function_words"], "function word lexicon is empty"
    assert "run" in lex["imperative_verbs"]
    assert "the" in lex["function_words"]


def test_yaml_boolean_words_survive_loading():
    """``on``, ``off``, ``no``, and ``yes`` are YAML 1.1 booleans.

    Unquoted, PyYAML turns ``- on`` into ``True``, so the word is lost
    and the string "true" is added in its place. That silently removed
    four function words and let "the slop check on docs" read as a
    four-word noun cluster.
    """
    lex = load_ste_lexicons()
    for word in ("on", "off", "no"):
        assert word in lex["function_words"], f"{word} lost to YAML booleans"
    assert "no" in lex["descriptive_starters"]
    for lexicon, words in lex.items():
        for junk in ("true", "false"):
            assert junk not in words, f"{junk} leaked into {lexicon}"


def test_every_lexicon_entry_is_a_string_in_the_source():
    """Guards the whole file, not just the four words known to break."""
    with open(
        Path(__file__).parent.parent / "data" / "ste" / "lexicons.yaml",
        encoding="utf-8",
    ) as handle:
        raw = yaml.safe_load(handle)
    for name, words in raw.items():
        bad = [w for w in words if not isinstance(w, str)]
        assert not bad, f"{name} has non-string entries (quote them): {bad}"


def test_lexicons_are_lowercase_and_deduplicated():
    lex = load_ste_lexicons()
    for name, words in lex.items():
        assert all(w == w.lower() for w in words), name
        assert len(words) == len(set(words)), f"{name} has duplicates"
