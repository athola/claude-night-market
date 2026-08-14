"""STE-derived structural checks: sentence length, paragraphs, noun clusters.

These three checks are the ones that cannot be expressed as regexes and
therefore cannot live in ``data/languages/en.yaml`` alongside the slop
patterns. Each needs either word-count normalization or noun detection:

- :func:`check_sentence_length` enforces the two limits ASD-STE100 sets
  for procedural text (20 words) and descriptive text (25 words). The
  two limits differ, so the text must be classified before it is
  measured. A checker that applies one global limit is measuring
  something other than STE.
- :func:`check_paragraph_length` enforces the six-sentence paragraph
  limit against every prose block. A run of numbered steps is a
  procedure rather than a run-on paragraph, and the block splitter
  already encodes that by giving each step its own block.
- :func:`find_noun_clusters` reports noun strings longer than three
  words.

Supporting the above:

- :func:`count_words` implements STE-style counting, which yields a
  smaller number than ``len(text.split())``.
- :func:`split_sentences` splits on sentence-ending punctuation while
  guarding abbreviations and dotted version numbers.
- :func:`classify_sentence` separates the procedural and descriptive
  registers.

WHAT IS OURS AND WHAT IS THE STANDARD'S
---------------------------------------

The four limits (20, 25, 6, 3) are corroborated across four independent
public restatements of ASD-STE100 and are pinned in ``test_ste.py``.

The word-counting conventions in :func:`count_words` are **our own
approximation**. ASD-STE100 counts words by its own conventions rather
than by whitespace, but those conventions are not published outside the
specification, which is copyright ASD and not redistributable. What we
implement here (a hyphenated compound, a parenthetical span, a quoted
placard, a number with its unit, and an inline code span each count as
one word) is a reasonable reading, not a transcription. No rule numbers
are cited for it because none could be verified. Rule 8.1, the ban on
semicolons, is the only rule number this project cites, and that check
lives in ``en.yaml`` because it is a regex property.

This module is an STE-derived authoring aid. It does not implement
ASD-STE100 and nothing here should be described as STE compliance. ASD
and the STE Maintenance Group state that they do not endorse or certify
sellers of tools claimed to be fully compliant with ASD-STE100, and that
such providers have no authorization to use the ASD logo, copyright, or
trademark. This project claims none of those things. Vocabulary checking
against the controlled dictionary is out of scope entirely.

PRECISION
---------

Noun-cluster detection works by subtracting function words and
recognizable verb forms from the token stream and treating the
remainder as nouns. That is crude next to a part-of-speech tagger, and
it is why every noun-cluster finding is reported at ``low`` confidence:
surface it for a human, never rewrite on it.

Paragraph findings are always ``high``, because a sentence count needs
no part of speech. Sentence findings are ``high`` or ``medium``,
depending on whether the register mattered. Past 25 words a sentence is
over both limits and the count alone settles it. Below that the finding
exists only because the sentence was read as procedural, and when that
reading came through a stripped label the finding is reported
``medium``.

A label is stripped because this repository's list items open with
``**Label**:``, and classifying on the label left most of them
unreadable. The cost is that the sentence's real opening is discarded.
``Triggers: push to master`` then reads as an instruction to push,
rather than a description of when a workflow fires, and no test on the
tokens can separate it from ``Merge to master``, which is a real
instruction. Measured across the corpus the reading is right about five
times in six. Dropping the whole class would delete five right answers
for each wrong one it removed, so the class is kept and the doubt is
published with it.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised via ImportError branch
    yaml = None

# Shipped, read-only asset, so deriving it from ``__file__`` is correct.
# Issue #661 warns against this pattern for *runtime user data*, which a
# plugin update would orphan under a version-scoped cache root. Lexicons
# ship with the code and are read-only, which is the case that issue
# explicitly exempts.
DATA_FILE = Path(__file__).parent.parent.parent / "data" / "ste" / "lexicons.yaml"

# The four limits. Corroborated across independent public restatements
# of ASD-STE100 and pinned by test_limits_match_the_corroborated_values.
PROCEDURAL_MAX_WORDS = 20
DESCRIPTIVE_MAX_WORDS = 25
PARAGRAPH_MAX_SENTENCES = 6
NOUN_CLUSTER_MAX_WORDS = 3

# A single opaque token standing in for a span that counts as one word.
# U+00A4 is outside normal prose and survives whitespace splitting.
_MASK = "¤"

# Sentinel replacing a period that must not end a sentence. Same width
# as the period it replaces, so character offsets stay valid and line
# numbers computed against the protected text remain correct.
_DOT = "\x01"

_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_URL = re.compile(r"\b(?:https?://|www\.)\S+")
# A bare domain carries no scheme, so the rule above misses it and the
# host tokenizes into "news ycombinator com". The TLD list is short on
# purpose: a general domain shape would swallow "config.yaml" and any
# sentence whose period lands next to a word.
_BARE_DOMAIN = re.compile(
    r"\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|io|dev|ai|edu|gov|co)\b(?:/\S*)?"
)
# A path is one thing, and its slashes are not word breaks. Without
# this, "/home/alext/claude/projects" reads as a four-word noun cluster.
# The rule also merges "and/or", which counts as one word either way.
_PATH = re.compile(r"(?<!\S)/?[\w.-]+(?:/[\w.-]+)+")
# Inline markup, not prose. Replaced with a space rather than the mask
# because a tag is not a word: "The <b>release</b> is ready" holds four.
_HTML_TAG = re.compile(r"</?[a-zA-Z][^>]*>")
# A bare filename or path is one thing. Without this, "config.yml"
# tokenizes into "config" and "yml" and reads as a noun cluster.
_FILENAME = re.compile(
    r"\b[\w./-]+\.(?:ya?ml|json|md|py|toml|sh|bash|js|ts|txt|cfg|ini|lock|rs|"
    r"tape|jsonl|csv|html|css|sql)\b"
)
_PARENTHETICAL = re.compile(r"\([^()]*\)")
_QUOTED = re.compile(r"\"[^\"]*\"")
# A number followed by its unit: "25 Nm", "30 ms", "5 kg". An earlier
# version accepted any token of four letters or fewer, which merged
# "3 days" and "2 runs" into one word. The unit has to be named.
_UNITS = (
    "ns|us|ms|s|sec|secs|min|mins|h|hr|hrs|"
    "b|kb|mb|gb|tb|kib|mib|gib|"
    "mg|g|kg|lb|lbs|nm|mm|cm|m|km|"
    "px|pt|em|rem|hz|khz|mhz|ghz|v|w|kw|k"
)
_NUMBER_UNIT = re.compile(rf"\b\d[\d,.]*\s+(?:{_UNITS})\b", re.IGNORECASE)

# Abbreviations whose trailing period does not end a sentence.
_ABBREVIATIONS = (
    "e.g.",
    "i.e.",
    "etc.",
    "cf.",
    "vs.",
    "approx.",
    "est.",
    "Fig.",
    "No.",
    "Dr.",
    "Mr.",
    "Mrs.",
    "Ms.",
    "Inc.",
    "Ltd.",
    "Co.",
    "St.",
    "a.m.",
    "p.m.",
)

# A sentence may end inside markdown emphasis: "**Bump the version.**".
# The closing markers are allowed to sit between the punctuation and
# the whitespace, or the two sentences merge into one.
_SENTENCE_END = re.compile(r"[.!?]+[*_`]*(?=\s|$)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
# A line opening with an HTML tag is an HTML block, which markdown
# treats as markup rather than prose. Measuring it produced the single
# loudest false positive in the corpus: "<details><summary>Click to
# expand full content summary</summary>" alone reported 2584 noun
# clusters, 11% of every cluster found.
_HTML_BLOCK = re.compile(r"^\s*</?[a-zA-Z][^>]*>")
_TABLE_ROW = re.compile(r"^\s*\|")
_HORIZONTAL_RULE = re.compile(r"^\s*([-*_])\s*(\1\s*){2,}$")
_FENCE_DELIMITER = re.compile(r"^\s*(```|~~~)")
_ORDERED_ITEM = re.compile(r"^\s*\d+[.)]\s+")
_UNORDERED_ITEM = re.compile(r"^\s*[-*+]\s+")
# A word may carry digits after its first letter. Without them "W3C"
# splits into "W" and "C", and every acronym in the corpus turned into
# single-letter shrapnel that padded noun clusters.
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")

# Punctuation that separates items. A noun cluster is one name, so a
# run of nouns never spans a comma, colon, or dash.
_PUNCTUATION_BREAK = re.compile(r"[,;:()\[\]{}]|\s[-\u2013\u2014]\s")

# A short label introducing a list item: "**Scope**:", "Note:". The
# label names the item; the instruction or statement follows it. Capped
# at four words and 40 characters so a real clause ending in a colon is
# never mistaken for a label.
_LABEL_PREFIX = re.compile(r"^\s*(?:\*\*|__)?\s*([^:*_`]{1,40}?)\s*(?:\*\*|__)?:\s+")
_LABEL_MAX_WORDS = 4

# Verb forms that can only be finite: a copula, an auxiliary, or a
# modal. A word in front of one of these is its subject, and a sentence
# with a subject is a statement rather than an instruction.
_FINITE_FORMS = frozenset(
    {
        "is",
        "are",
        "was",
        "were",
        "has",
        "have",
        "had",
        "does",
        "did",
        "can",
        "cannot",
        "could",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "will",
        "would",
    }
)

_LEXICON_CACHE: dict | None = None


@dataclass(frozen=True)
class Sentence:
    """One sentence, with the 1-based line it starts on."""

    text: str
    line: int
    kind: str
    confidence: float


@dataclass(frozen=True)
class Finding:
    """One STE violation, reported rather than corrected."""

    rule: str
    line: int
    text: str
    detail: str
    confidence: str
    limit: int | None = None
    actual: int | None = None


@dataclass(frozen=True)
class _Block:
    """A run of prose lines: one paragraph or one list item."""

    text: str
    line: int
    is_list_item: bool
    is_ordered: bool


def load_ste_lexicons() -> dict:
    """Load the word lists backing classification and noun detection.

    Returns a mapping of lexicon name to a lowercase, deduplicated,
    sorted list of words. Memoized, matching ``scribe.spelling``.
    """
    global _LEXICON_CACHE
    if _LEXICON_CACHE is not None:
        return _LEXICON_CACHE
    if yaml is None:  # pragma: no cover - depends on the environment
        raise ImportError(
            "pyyaml is required to load the STE lexicons; "
            "install it with `uv sync` in plugins/scribe"
        )
    with DATA_FILE.open(encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle) or {}
    lexicons = {
        name: sorted({str(word).lower() for word in words or []})
        for name, words in raw.items()
    }
    _LEXICON_CACHE = lexicons
    return lexicons


def _sets() -> dict:
    """Lexicons as sets, for membership tests in the hot paths."""
    return {name: set(words) for name, words in load_ste_lexicons().items()}


def _mask_spans(text: str) -> str:
    """Collapse every span that STE counts as a single word.

    Order matters: code and URLs go first so a parenthesis or quote
    inside them cannot open a span that swallows real prose.
    """
    masked = _FENCED_CODE.sub(_MASK, text)
    masked = _INLINE_CODE.sub(_MASK, masked)
    masked = _HTML_TAG.sub(" ", masked)
    masked = _URL.sub(_MASK, masked)
    masked = _BARE_DOMAIN.sub(_MASK, masked)
    masked = _PATH.sub(_MASK, masked)
    masked = _FILENAME.sub(_MASK, masked)
    masked = _PARENTHETICAL.sub(_MASK, masked)
    masked = _QUOTED.sub(_MASK, masked)
    return _NUMBER_UNIT.sub(_MASK, masked)


def count_words(sentence: str) -> int:
    """Count words the way STE counts them, not the way ``split`` does.

    A hyphenated compound, a parenthetical, a quoted placard, a number
    with its unit, and a code span each count as one word. See the
    module docstring on what this shares with the standard and what it
    only approximates.
    """
    masked = _mask_spans(sentence)
    tokens = [token for token in masked.split() if _is_countable(token)]
    return len(tokens)


def _is_countable(token: str) -> bool:
    """True unless the token is bare punctuation."""
    if _MASK in token:
        return True
    return any(char.isalnum() for char in token)


def _protect_periods(text: str) -> str:
    """Replace periods that do not end sentences, preserving length."""
    protected = re.sub(r"\.(?=\d)", _DOT, text)
    for abbreviation in _ABBREVIATIONS:
        protected = re.sub(
            re.escape(abbreviation),
            abbreviation.replace(".", _DOT),
            protected,
            flags=re.IGNORECASE,
        )
    return protected


def split_sentences(text: str, *, in_ordered_list: bool = False) -> list:
    """Split text into sentences, guarding abbreviations and versions.

    ``in_ordered_list`` reaches the register decision, which is where
    it belongs. Deciding afterwards, in the caller, left the classifier
    unable to see the one structural signal it trusts most.
    """
    if not text.strip():
        return []
    protected = _protect_periods(text)
    spans = []
    start = 0
    for match in _SENTENCE_END.finditer(protected):
        spans.append((start, match.end()))
        start = match.end()
    if protected[start:].strip():
        spans.append((start, len(protected)))

    sentences = []
    for span_start, span_end in spans:
        segment = protected[span_start:span_end]
        if not segment.strip():
            continue
        lead = len(segment) - len(segment.lstrip())
        absolute = span_start + lead
        restored = segment.strip().replace(_DOT, ".")
        kind, confidence = classify_sentence(restored, in_ordered_list=in_ordered_list)
        sentences.append(
            Sentence(
                text=restored,
                line=text[:absolute].count("\n") + 1,
                kind=kind,
                confidence=confidence,
            )
        )
    return sentences


def _strip_label(text: str) -> str:
    """Drop a leading ``Label:`` so the register is read from the body.

    Returns the text unchanged when the prefix is too long or too wordy
    to be a label, which keeps a genuine clause ending in a colon
    intact.
    """
    match = _LABEL_PREFIX.match(text)
    if match is None:
        return text
    label = match.group(1).strip()
    if not label or len(label.split()) > _LABEL_MAX_WORDS:
        return text
    remainder = text[match.end() :]
    return remainder if remainder.strip() else text


def _is_finite_verb(word: str, verbs: set) -> bool:
    """True when the word can only be a finite verb, never a bare one.

    A copula or modal qualifies outright. So does an inflected form of
    a listed verb, because ``-s`` marks a third-person present verb.
    The bare form is deliberately excluded: in ``Use return
    dictionaries`` the second word is an object, not a predicate.
    """
    if word in _FINITE_FORMS:
        return True
    if word.endswith("ies") and word[:-3] + "y" in verbs:
        return True
    if word.endswith("es") and word[:-2] in verbs:
        return True
    return word.endswith("s") and word[:-1] in verbs


def classify_sentence(text: str, *, in_ordered_list: bool = False) -> tuple:
    """Classify a sentence as procedural, descriptive, or unknown.

    The two registers carry different word limits, so this decision has
    to be made before any measurement. Returns the register and a
    confidence in ``[0.0, 1.0]``.

    Uncertainty resolves to ``unknown``, and callers give unknown text
    the looser limit. Silence on ambiguous input is what keeps the
    check enabled.
    """
    lex = _sets()
    body = _strip_label(text)
    # A label hides the sentence's real opening, so a register read
    # through one rests on less than a register read from the sentence
    # itself. Measured over the corpus, the reading is right about five
    # times in six, which is worth reporting and not worth asserting.
    through_label = body != text
    words = _WORD.findall(_mask_spans(body))
    if not words:
        return ("unknown", 0.0)
    first = words[0].lower()

    if first in lex["imperative_verbs"]:
        if in_ordered_list:
            return ("procedural", 0.75 if through_label else 0.9)
        return ("procedural", 0.6 if through_label else 0.75)
    # "Never raise the baseline" is an instruction with an adverb in
    # front of its verb. The adverb alone proves nothing, so the verb
    # after it has to be present, and the reading is weaker evidence
    # than a bare imperative. This is tested before the descriptive
    # starters because several openers ("then", "once", "only") sit in
    # both lists, and an adverb followed by a verb is the stronger
    # signal of the two.
    if (
        first in lex["adverbial_openers"]
        and len(words) > 1
        and words[1].lower() in lex["imperative_verbs"]
    ):
        return ("procedural", 0.7 if in_ordered_list else 0.6)
    if first in lex["descriptive_starters"]:
        return ("descriptive", 0.75)
    # "Categories are resolved", "GRADE reports certainty". The opening
    # word is a noun the verb lexicon does not know, and the word after
    # it can only be a predicate, so the opening word is its subject.
    # Placed ahead of the numbered-list fallback on purpose: a step
    # that turns out to be a statement is a statement.
    if len(words) > 1 and _is_finite_verb(words[1].lower(), lex["imperative_verbs"]):
        return ("descriptive", 0.7)
    if in_ordered_list:
        return ("procedural", 0.6)
    return ("unknown", 0.3)


def _iter_blocks(text: str) -> list:
    """Split markdown into prose blocks, dropping everything non-prose.

    Fenced code, headings, table rows, and horizontal rules are not
    prose and are never measured. Each list item becomes its own block
    so a procedure is not read as one giant paragraph.
    """
    blocks = []
    buffer: list = []
    buffer_line = 0
    in_fence = False
    is_list_item = False
    is_ordered = False
    lines = text.splitlines()

    # YAML frontmatter is metadata, not prose. Every SKILL.md in this
    # repository opens with one, and counting `name:`/`description:` as
    # prose made frontmatter the largest single source of sentences the
    # classifier could not place. Only a `---` on the very first line
    # opens frontmatter; anywhere else it is a horizontal rule.
    start_index = 0
    if lines and lines[0].strip() == "---":
        for offset, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start_index = offset + 1
                break

    def flush() -> None:
        nonlocal buffer, buffer_line, is_list_item, is_ordered
        if buffer:
            blocks.append(
                _Block(
                    text=" ".join(buffer),
                    line=buffer_line,
                    is_list_item=is_list_item,
                    is_ordered=is_ordered,
                )
            )
        buffer = []
        is_list_item = False
        is_ordered = False

    for index, line in enumerate(lines[start_index:], start=start_index + 1):
        if _FENCE_DELIMITER.match(line):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            flush()
            continue
        if (
            _HEADING.match(line)
            or _TABLE_ROW.match(line)
            or _HORIZONTAL_RULE.match(line)
            or _HTML_BLOCK.match(line)
        ):
            flush()
            continue

        ordered = _ORDERED_ITEM.match(line)
        marker = ordered or _UNORDERED_ITEM.match(line)
        if marker is not None:
            flush()
            is_list_item = True
            is_ordered = ordered is not None
            buffer = [line[marker.end() :].strip()]
            buffer_line = index
            continue

        if not buffer:
            buffer_line = index
        buffer.append(line.strip())

    flush()
    return blocks


def _finding_confidence(actual: int, register_confidence: float) -> str:
    """How far a sentence_length finding rests on the register.

    Past the descriptive limit the sentence is over both limits, so the
    count settles it and the register is irrelevant. Below that the
    finding stands or falls on a register the checker inferred, and a
    weak inference has to be reported as one. The alternative, dropping
    the finding, deletes about five right answers for each wrong one it
    removes.
    """
    if actual > DESCRIPTIVE_MAX_WORDS or register_confidence >= 0.75:
        return "high"
    return "medium"


def check_sentence_length(text: str) -> list:
    """Report sentences over the limit for their register.

    Procedural sentences are held to 20 words and descriptive ones to
    25. Text whose register cannot be determined gets the looser limit.
    """
    findings = []
    for block in _iter_blocks(text):
        for sentence in split_sentences(block.text, in_ordered_list=block.is_ordered):
            kind = sentence.kind
            limit = (
                PROCEDURAL_MAX_WORDS if kind == "procedural" else DESCRIPTIVE_MAX_WORDS
            )
            actual = count_words(sentence.text)
            if actual > limit:
                findings.append(
                    Finding(
                        rule="sentence_length",
                        line=block.line + sentence.line - 1,
                        text=sentence.text,
                        detail=(
                            f"{kind} sentence runs {actual} words against a "
                            f"{limit}-word limit"
                        ),
                        confidence=_finding_confidence(actual, sentence.confidence),
                        limit=limit,
                        actual=actual,
                    )
                )
    return findings


def check_paragraph_length(text: str) -> list:
    """Report prose blocks longer than six sentences.

    Seven numbered steps are seven procedures, not a run-on paragraph.
    ``_iter_blocks`` already enforces that by giving each list item its
    own block, so no second exemption is needed here. Skipping items
    outright would let one eight-sentence bullet through, which is the
    defect the limit exists to catch.
    """
    findings = []
    for block in _iter_blocks(text):
        count = len(split_sentences(block.text, in_ordered_list=block.is_ordered))
        if count > PARAGRAPH_MAX_SENTENCES:
            findings.append(
                Finding(
                    rule="paragraph_length",
                    line=block.line,
                    text=block.text[:80],
                    detail=(
                        f"paragraph runs {count} sentences against a "
                        f"{PARAGRAPH_MAX_SENTENCES}-sentence limit"
                    ),
                    confidence="high",
                    limit=PARAGRAPH_MAX_SENTENCES,
                    actual=count,
                )
            )
    return findings


def _looks_like_verb(word: str, position: int, verbs: set) -> bool:
    """True when the token reads as a verb rather than a noun.

    A base-form verb opening a sentence is an imperative. Elsewhere a
    bare base form is more often a noun ("the capture pipeline"), so
    only inflected forms count. Inflection is tested by stripping the
    ending and asking whether the stem is a verb we listed, never by
    treating the suffix itself as proof.
    """
    if position == 0 and word in verbs:
        return True
    if word.endswith("s") and word[:-1] in verbs:
        return True
    if word.endswith("es") and word[:-2] in verbs:
        return True
    if word.endswith("ed") and (word[:-2] in verbs or word[:-1] in verbs):
        return True
    if word.endswith("ies") and word[:-3] + "y" in verbs:
        return True
    if word.endswith("ing"):
        stem = word[:-3]
        # "running" -> "runn" -> "run"; "storing" -> "stor" -> "store".
        candidates = {stem, stem + "e"}
        if len(stem) > 1 and stem[-1] == stem[-2]:
            candidates.add(stem[:-1])
        if candidates & verbs:
            return True
    return False


def _is_noun_like(word: str, position: int, lex: dict) -> bool:
    """True when a token can be part of a noun cluster."""
    lowered = word.lower()
    if not lowered.replace("-", "").replace("'", "").isalnum():
        return False
    if lowered in lex["function_words"] or lowered in lex["descriptive_starters"]:
        return False
    if lowered.endswith("ly"):
        return False
    return not _looks_like_verb(lowered, position, lex["imperative_verbs"])


def find_noun_clusters(text: str) -> list:
    """Report noun strings longer than three words.

    Every finding is ``low`` confidence. Detection subtracts function
    words and verb forms and calls the remainder nouns, which a real
    part-of-speech tagger would do far better. Treat a finding as a
    prompt to reread the phrase, never as grounds to rewrite it.
    """
    findings = []
    lex = _sets()
    for block in _iter_blocks(text):
        for sentence in split_sentences(block.text, in_ordered_list=block.is_ordered):
            masked = _mask_spans(sentence.text)
            position = 0
            for segment in _PUNCTUATION_BREAK.split(masked):
                run: list = []
                for word in _WORD.findall(segment):
                    if _is_noun_like(word, position, lex):
                        run.append(word)
                    else:
                        findings.extend(_cluster_finding(run, block, sentence))
                        run = []
                    position += 1
                findings.extend(_cluster_finding(run, block, sentence))
    return findings


def _cluster_finding(run: list, block: _Block, sentence: Sentence) -> list:
    """Build a finding for a completed run, when it is too long."""
    if len(run) <= NOUN_CLUSTER_MAX_WORDS:
        return []
    return [
        Finding(
            rule="noun_cluster",
            line=block.line + sentence.line - 1,
            text=" ".join(run),
            detail=(
                f"noun cluster of {len(run)} words against a "
                f"{NOUN_CLUSTER_MAX_WORDS}-word limit"
            ),
            confidence="low",
            limit=NOUN_CLUSTER_MAX_WORDS,
            actual=len(run),
        )
    ]


def check(text: str, *, noun_clusters: bool = True) -> list:
    """Run the structural checks and return every finding.

    ``noun_clusters`` is a switch because that rule alone reports on
    76% of the markdown in this repository at ``low`` confidence. A
    reader who wants the two counting rules should not have to wade
    through it to reach them.
    """
    findings = check_sentence_length(text) + check_paragraph_length(text)
    if noun_clusters:
        findings += find_noun_clusters(text)
    return findings


def main(argv: list | None = None) -> int:
    """Report findings for each named markdown file.

    Always exits 0 when the files could be read. These checks are
    advisory and ship off by default, and the noun-cluster rule must
    never gate a merge, so an exit code that a pipeline could fail on
    would misrepresent what the output means. A file that cannot be
    read is a different matter and exits 1.
    """
    parser = argparse.ArgumentParser(
        prog="python -m scribe.ste",
        description=(
            "STE-derived structural checks. An authoring aid, not an "
            "implementation of ASD-STE100, and no output of it is STE "
            "compliant."
        ),
    )
    parser.add_argument("paths", nargs="+", help="markdown files to read")
    parser.add_argument(
        "--no-noun-clusters",
        action="store_true",
        help="skip the low-confidence noun-cluster rule",
    )
    args = parser.parse_args(argv)

    unreadable = 0
    for name in args.paths:
        path = Path(name)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            print(f"{path}: {error.strerror or error}", file=sys.stderr)
            unreadable += 1
            continue
        for finding in check(text, noun_clusters=not args.no_noun_clusters):
            print(
                f"{path}:{finding.line}: "
                f"[{finding.rule}/{finding.confidence}] {finding.detail}"
            )
    return 1 if unreadable else 0


if __name__ == "__main__":  # pragma: no cover - exercised through main()
    raise SystemExit(main())
