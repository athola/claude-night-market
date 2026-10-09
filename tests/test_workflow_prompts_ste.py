"""Workflow prose stays inside the adopted STE limits.

A workflow script carries two kinds of text the STE rule puts in scope:
the instructions each `agent()` call sends to a subagent, and the
operator-facing strings (`meta.description`, `meta.whenToUse`, `log()`
lines, `reason` and `next` fields). See
`.claude/rules/ste-for-operator-and-procedures.md`.

`scribe.ste` reads markdown, and these strings are JS literals. The
literals are pulled out first. Comments are rationale and are not
scanned. Only three checks gate here: sentence length, semicolons and
contractions. Noun clusters never gate a merge, per the scribe skill.

The limits are enforced on the text, and no "write in ASD-STE100"
line is added to the prompts themselves. The measured evidence for
that directive is rule obedience in output, not task accuracy, and one
practitioner test found formal ASD-STE100 dropped code facts. Sources:
`Skill(scribe:simplified-technical-english)` module `evidence.md`.
"""

from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plugins" / "scribe" / "src"))
check_sentence_length = importlib.import_module("scribe.ste").check_sentence_length

#: Literals shorter than this are labels, keys and enum values.
MIN_PROSE_WORDS = 6

CONTRACTION = re.compile(
    r"\b\w+(?:n't|'re|'ll|'ve|'m)\b|\b(?:it|that|there|what|here)'s\b",
    re.IGNORECASE,
)

SPLICE = re.compile(r";\s+[A-Za-z]")

ESCAPES = {"n": "\n", "t": "\t"}


def _skip_interpolation(src: str, start: int) -> int:
    """Return the index after the `}` closing the `${` at `start`."""
    depth, index = 1, start + 2
    while depth:
        depth += {"{": 1, "}": -1}.get(src[index], 0)
        index += 1
    return index


def string_literals(src: str) -> list[tuple[int, str]]:
    """Every string literal outside comments, as (line, text).

    A `${...}` interpolation becomes the single word `X`, because the
    reader of the rendered prompt sees one value there.
    """
    literals = []
    index, end = 0, len(src)
    while index < end:
        if src.startswith("//", index):
            newline = src.find("\n", index)
            index = end if newline < 0 else newline
            continue
        if src.startswith("/*", index):
            index = src.index("*/", index) + 2
            continue
        quote = src[index]
        if quote not in "'\"`":
            index += 1
            continue
        line = src.count("\n", 0, index) + 1
        chars = []
        cursor = index + 1
        while src[cursor] != quote:
            if src[cursor] == "\\":
                chars.append(ESCAPES.get(src[cursor + 1], src[cursor + 1]))
                cursor += 2
            elif quote == "`" and src.startswith("${", cursor):
                chars.append("X")
                cursor = _skip_interpolation(src, cursor)
            else:
                chars.append(src[cursor])
                cursor += 1
        literals.append((line, "".join(chars)))
        index = cursor + 1
    return literals


def ste_findings(src: str) -> list[str]:
    findings = []
    for line, text in string_literals(src):
        # A splice is caught at any length. A bare `;` inside a short
        # literal is a key or a separator, not a sentence.
        short = len(text.split()) < MIN_PROSE_WORDS
        if SPLICE.search(text) if short else ";" in text:
            findings.append(f"{line}: semicolon in {text.strip()[:70]!r}")
        if short:
            continue
        for finding in check_sentence_length(text):
            findings.append(f"{line}: {finding.detail}")
        contraction = CONTRACTION.search(text)
        if contraction:
            findings.append(f"{line}: contraction {contraction.group(0)!r}")
    return findings


def _workflow_scripts() -> list[Path]:
    return sorted((REPO_ROOT / "plugins").glob("*/workflows/*.js"))


@pytest.mark.parametrize(
    "script", _workflow_scripts(), ids=lambda p: f"{p.parents[1].name}/{p.name}"
)
def test_workflow_prose_stays_inside_ste_limits(script: Path) -> None:
    findings = ste_findings(script.read_text())

    assert not findings, f"{script.relative_to(REPO_ROOT)}:\n" + "\n".join(findings)


def test_semicolon_in_a_prompt_is_reported() -> None:
    src = "agent(`Read the diff for each file; report the risky ones first.`)"

    assert any("semicolon" in f for f in ste_findings(src))


def test_contraction_in_a_log_line_is_reported() -> None:
    src = 'log("the oracle daemon isn\'t provisioned on this machine yet")'

    assert any("contraction" in f for f in ste_findings(src))


def test_possessive_is_not_a_contraction() -> None:
    src = 'log("the plugin\'s manifest names every skill on disk")'

    assert ste_findings(src) == []


def test_long_instruction_is_reported() -> None:
    words = " ".join(["Check"] + ["the"] * 28 + ["file."])
    src = f"agent('{words}')"

    assert any("word limit" in f for f in ste_findings(src))


def test_clean_prompt_passes() -> None:
    src = "agent(`Read each file in the diff. Report one finding per line.`)"

    assert ste_findings(src) == []


def test_interpolation_counts_as_one_word() -> None:
    src = "agent(`Check ${items.map((i) => `${i.name}; ${i.path}`).join(', ')} now.`)"

    assert string_literals(src) == [(1, "Check X now.")]


def test_comments_are_not_scanned() -> None:
    src = (
        "// A comment; with a semicolon that isn't checked at all here.\n"
        "/* Block comment; also skipped because it's rationale text. */\n"
        "const n = 1\n"
    )

    assert ste_findings(src) == []


def test_semicolon_splice_in_a_short_log_line_is_reported() -> None:
    # Each interpolation counts as one word, so an operator line built
    # mostly from values falls under MIN_PROSE_WORDS and still splices.
    src = "log(`${count} findings; nothing to merge`)"

    assert any("semicolon" in f for f in ste_findings(src))


def test_short_literals_are_not_prose() -> None:
    src = "const schema = { type: 'object', required: ['a;b', 'c;d'] }"

    assert ste_findings(src) == []
