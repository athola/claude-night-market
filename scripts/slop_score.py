#!/usr/bin/env python3
"""Score prose for AI slop, sourcing every pattern from the YAML.

`slop-check.yml` used to carry its own `TIER1=`/`TIER2=` grep
alternations. `plugins/scribe/data/languages/en.yaml` is documented as
the single pattern source that `Skill(scribe:slop-detector)` loads at
runtime, so the gate was enforcing a snapshot: every Tier 5 category
added since was invisible to CI, and a grep alternation of bare words
cannot express a regex category anyway.

Reading the YAML means a category added there reaches CI with no
workflow edit, which is the property `tests/unit/test_slop_score.py`
pins.

Scoring keeps the shape the workflow already reported so its threshold
and PR comment stay meaningful: weighted hits per 100 words, tier 1
words worth 3 and tier 2 worth 2, with each Tier 5 category worth the
score it declares for itself. Opt-in categories stay out, matching a
default sweep.

Only high-confidence categories count toward the score. The house rule
is that a `confidence: low` finding is surfaced for a human to judge
and never auto-applied, so failing a merge on one would contradict it:
semicolon splices and the softer anthropomorphism verbs are judgment
calls, and six files in this repository sit above the threshold on
those alone. They are still listed, under a heading that says they did
not count.
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import subprocess
import sys
import tokenize
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "plugins" / "scribe" / "src"))

from scribe.negation import (  # noqa: E402 - path must be set before import
    check_negation_density,
)
from scribe.pattern_loader import (  # noqa: E402 - path must be set before import
    get_tier1_words,
    get_tier2_words,
    get_tier5_patterns,
    load_language_patterns,
)

# Below this many words of prose, a Python file's score measures its
# denominator rather than its writing. The score is hits per 100 words
# and a tier 1 hit is worth 3, so under ~100 words one hit alone can
# put a file over a 3.0 threshold. Measured over six plugins: a module
# with 14 words of docstring and a single finding scored 21.43, against
# 1.55 for a 1029-word ADR carrying twelve.
#
# 150 is where that stops. Sweeping 50, 100 and 150 against the same
# six plugins, it is the lowest value at which every surviving file
# carries at least three findings: 50 leaves fourteen files gating on
# one or two, 100 leaves six, 150 leaves none.
#
# Python only, and deliberately. A one-line module docstring is
# ordinary; a 14-word README is a finding in itself. The markdown gate
# keeps the behavior it had.
#
# The same reasoning already governs `scribe.negation`, whose density
# check floors at 8 sentences because a ratio over a handful of them
# describes the sample rather than the writing.
PYTHON_WORD_FLOOR = 150

TIER1_WEIGHT = 3
TIER2_WEIGHT = 2
EM_DASH_WEIGHT = 1

CONFIG_NAME = ".slop-config.yaml"

_FENCED_CODE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
# Double-backtick spans come first, because the single-backtick
# alternative would consume the opening pair as an empty span and leave
# the code between them bare. RST and Sphinx docstrings mark code that
# way by convention, so before this the formula in ``(n_i - n_j) / (n_i
# + n_j)`` reached the scorer as prose and scored a plus sign as a
# conjunction.
# Shared by the gate and the audit, so the two cannot drift.
#
# The pipe guards keep markdown table separators out. `slop-scan-for-docs.md`
# rule 2a exempts `| -- |` explicitly, and the bare form matched every
# table in the repository, which is why promoting this to the gate
# needed the exemption implemented rather than only documented.
_DOUBLE_DASH = re.compile(r"(?<!\|\s)(?<=\s)--(?=\s)(?!\s*\|)")

_INLINE_CODE = re.compile(r"``[^`]*``|`[^`\n]*`")


@dataclass(frozen=True)
class Finding:
    """One matched pattern, with the rule that matched it."""

    category: str
    match: str
    weight: int


@dataclass(frozen=True)
class Score:
    """A file's weighted hits per 100 words."""

    score: float
    words: int
    findings: list = field(default_factory=list)


def _read_config(config_path: Path | None = None) -> dict:
    """Parse .slop-config.yaml, or return an empty mapping if it is absent."""
    path = config_path or (_REPO_ROOT / CONFIG_NAME)
    if not path.is_file():
        return {}
    try:
        import yaml  # noqa: PLC0415 - deferred so a missing pyyaml degrades to an empty config rather than breaking the gate

        return yaml.safe_load(path.read_text()) or {}
    except (OSError, ValueError):
        return {}


def load_allowlist(config_path: Path | None = None) -> frozenset:
    """Read the `allowlist` field from a .slop-config.yaml.

    `allowlist` and `exclude_patterns` are the two documented fields this
    scorer reads. `config-file.md` documents more, and a config that sets
    the rest gets no error and no effect here, which is worth knowing
    before relying on it.
    """
    loaded = _read_config(config_path)
    return frozenset(str(word).lower() for word in loaded.get("allowlist", []) or [])


def load_exclude_patterns(config_path: Path | None = None) -> tuple:
    """Read the `exclude_patterns` globs from a .slop-config.yaml.

    The gate and the ratchet skip a file matching one. Audit mode does
    not: it exits 0 whatever it finds, so it has nothing to protect and
    answers "where is it" for every file it was asked about. The globs
    are matched with fnmatch against the path relative to the repository
    root, so `*` crosses directory separators.
    """
    loaded = _read_config(config_path)
    return tuple(str(glob) for glob in loaded.get("exclude_patterns", []) or [])


def _relative(path: Path) -> str:
    """The path as the config's globs see it: repo-relative, posix."""
    try:
        return path.resolve().relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _apply_excludes(paths: list, patterns: tuple) -> tuple:
    """Split *paths* into (kept, excluded) by the config's globs."""
    kept, excluded = [], []
    for path in paths:
        target = (
            excluded
            if any(fnmatch(_relative(path), glob) for glob in patterns)
            else kept
        )
        target.append(path)
    return kept, excluded


def _prose_only(text: str) -> str:
    """Drop code spans, where a slop word is a symbol rather than prose."""
    return _INLINE_CODE.sub(" ", _FENCED_CODE.sub(" ", text))


def _blank(match: re.Match) -> str:
    """Replace a code span with spaces, keeping its newlines in place."""
    return "".join("\n" if char == "\n" else " " for char in match.group(0))


def _prose_keeping_offsets(text: str) -> str:
    """Blank code spans without moving any character that follows.

    `_prose_only` collapses a fence to one space, so an offset computed
    on its output points at the wrong line. Audit mode reports lines, so
    it needs the substitution to be length-preserving instead.
    """
    return _INLINE_CODE.sub(_blank, _FENCED_CODE.sub(_blank, text))


def _rules(language: str = "en") -> list:
    """Build the (category, compiled regex, weight) list from the YAML."""
    patterns = load_language_patterns(language)
    rules = []
    for word in get_tier1_words(patterns):
        rules.append(
            ("tier1", re.compile(rf"\b{re.escape(word)}\b", re.I), TIER1_WEIGHT)
        )
    for word in get_tier2_words(patterns):
        rules.append(
            ("tier2", re.compile(rf"\b{re.escape(word)}\b", re.I), TIER2_WEIGHT)
        )
    for entry in get_tier5_patterns(patterns):
        flags = re.IGNORECASE if entry["ignore_case"] else 0
        # A low-confidence hit is surfaced, never scored: gating a merge
        # on one contradicts the rule that says a human decides.
        weight = entry["score"] if entry["confidence"] == "high" else 0
        for pattern in entry["patterns"]:
            rules.append((entry["category"], re.compile(pattern, flags), weight))
    rules.append(("em_dash", re.compile("—"), EM_DASH_WEIGHT))
    # `slop-scan-for-docs.md` rule 2a calls the spaced double dash a
    # high-confidence tell and always-fix. It reached `_audit_rules`
    # only, and CI runs gate and ratchet mode, never `--audit`, so the
    # category had no enforcement path anywhere in the pipeline.
    rules.append(("double_dash", _DOUBLE_DASH, EM_DASH_WEIGHT))
    return rules


_RULES_CACHE: list = []
_AUDIT_RULES_CACHE: list = []


def _audit_rules(language: str = "en") -> list:
    """Every category, opt-in ones included, tagged with its confidence.

    The gate loads a default sweep and scores only high confidence.
    An audit answers "where is it", so it declines neither.
    """
    patterns = load_language_patterns(language)
    rules = [
        ("tier1", re.compile(rf"\b{re.escape(word)}\b", re.I), "high")
        for word in get_tier1_words(patterns)
    ]
    rules += [
        ("tier2", re.compile(rf"\b{re.escape(word)}\b", re.I), "high")
        for word in get_tier2_words(patterns)
    ]
    for entry in get_tier5_patterns(patterns, include_optional=True):
        flags = re.IGNORECASE if entry["ignore_case"] else 0
        for pattern in entry["patterns"]:
            rules.append(
                (entry["category"], re.compile(pattern, flags), entry["confidence"])
            )
    rules.append(("em_dash", re.compile("—"), "high"))
    rules.append(("double_dash", _DOUBLE_DASH, "high"))
    return rules


#: Categories scanned against the raw document rather than the prose
#: copy. Blanking a fence is right for a vocabulary rule, where a slop
#: word in code is a symbol. It is wrong for a character with no glyph:
#: a bidi override in a fenced block is Trojan Source, and the fence is
#: the place it hides.
_RAW_TEXT_CATEGORIES = frozenset({"invisible_unicode"})


#: Structure, not a defect. A newline inside a match is how the source
#: was wrapped, and `_collapse` folds it away; naming it would print
#: `<U+000A>` in place of the space the reader expects.
_ASCII_WHITESPACE = frozenset(" \t\n\r\f\v")


def _collapse(text: str) -> str:
    """Flatten a multi-line match onto one display line.

    Only ASCII whitespace, and only after `_legible` has run. Python's
    `str.split()` counts U+00A0 and the U+2000 block as whitespace, so
    collapsing first would turn an exotic space into an ordinary one
    and leave nothing for the name to describe.
    """
    return re.sub(r"[ \t\n\r\f\v]+", " ", text).strip()


def _legible(text: str) -> str:
    """Name any character in *text* that would print as nothing.

    Every other category matches text the reader can read back, so the
    report echoes the match and the reader knows what to delete. A
    zero-width or bidi character echoes as a blank where the evidence
    should be, which tells the reader that a line is wrong and nothing
    further: not which column, and not which codepoint.
    """
    return "".join(
        char
        if char.isprintable() or char in _ASCII_WHITESPACE
        else f"<U+{ord(char):04X}>"
        for char in text
    )


@dataclass(frozen=True)
class AuditHit:
    """One located finding: where it is, what matched, how sure we are."""

    line: int
    category: str
    match: str
    confidence: str


def audit_text(
    text: str, language: str = "en", allowlist: frozenset | None = None
) -> list:
    """Locate every finding in *text*, sorted by line."""
    global _AUDIT_RULES_CACHE
    if not _AUDIT_RULES_CACHE:
        _AUDIT_RULES_CACHE = _audit_rules(language)
    allow = allowlist or frozenset()

    prose = _prose_keeping_offsets(text)
    hits = []
    for category, regex, confidence in _AUDIT_RULES_CACHE:
        body = text if category in _RAW_TEXT_CATEGORIES else prose
        for match in regex.finditer(body):
            if match.group(0).lower() in allow:
                continue
            hits.append(
                AuditHit(
                    line=body.count("\n", 0, match.start()) + 1,
                    category=category,
                    match=_collapse(_legible(match.group(0)))[:60],
                    confidence=confidence,
                )
            )
    hits.sort(key=lambda hit: (hit.line, hit.category))
    return hits


def score_text(
    text: str, language: str = "en", allowlist: frozenset | None = None
) -> Score:
    """Return the weighted slop score for *text*."""
    global _RULES_CACHE
    if not _RULES_CACHE:
        _RULES_CACHE = _rules(language)
    allow = allowlist or frozenset()

    prose = _prose_only(text)
    words = len(prose.split())
    if words == 0:
        return Score(score=0.0, words=0, findings=[])

    findings = []
    weighted = 0
    for category, regex, weight in _RULES_CACHE:
        body = text if category in _RAW_TEXT_CATEGORIES else prose
        for match in regex.finditer(body):
            if match.group(0).lower() in allow:
                continue
            findings.append(
                Finding(category=category, match=match.group(0), weight=weight)
            )
            weighted += weight

    return Score(score=weighted / words * 100, words=words, findings=findings)


_SKIP_PARTS = {".git", "worktrees", "node_modules", "__pycache__", ".venv"}


def _split_roots(roots: list) -> list:
    """Split any argument that arrived holding a whole file list.

    zsh does not word-split an unquoted parameter, so
    `--audit $CHANGED_FILES` arrives as one argument holding newline
    separated paths. Splitting on whitespace here means the obvious
    invocation works in every shell.
    """
    return [part for root in roots for part in str(root).split() if part]


def _iter_markdown(roots: list, python: bool = False) -> list:
    """Yield the prose files under each root, or the root itself if a file.

    The gate passes two directories. An audit usually passes the files a
    branch changed, so a directory-only argument would send the caller
    back to copying files into a scratch tree.

    A directory yields markdown, and yields `.py` as well when *python*
    is set. A file named directly is taken whatever its suffix, which is
    how a single module reaches `_read_prose`.

    Raises FileNotFoundError for a root that does not exist. Returning
    nothing instead would report "no findings" for a list nothing read,
    which is a clean bill of health the scan never earned.
    """
    found = []
    for root in _split_roots(roots):
        path = Path(root)
        if not path.exists():
            raise FileNotFoundError(root)
        if path.is_file():
            candidates = [path]
        else:
            candidates = sorted(path.rglob("*.md"))
            if python:
                candidates += sorted(path.rglob("*.py"))
        for candidate in candidates:
            if any(part in _SKIP_PARTS for part in candidate.parts):
                continue
            found.append(candidate)
    return found


def _python_prose(source: str) -> str:
    """The comments and docstrings of *source*, on their original lines.

    Every other line comes back blank. The line count is preserved, so
    a finding still points at the line that carries it and the text
    scorer needs no change to report a Python file.

    Half of what issue #65961 reports lives in a comment, and every
    Tier 5 category this repository has written reached markdown only.
    Projecting a module onto its prose is what brings the existing
    nine negation categories to a docstring.

    Doctest lines are dropped. ``>>> assert not stale`` is executable
    example code, and scoring it would flag the code a docstring is
    demonstrating.
    """
    lines = source.splitlines()
    kept = [""] * len(lines)

    def keep(start: int, end: int) -> None:
        for index in range(start - 1, min(end, len(lines))):
            stripped = lines[index].lstrip()
            if stripped.startswith((">>>", "...")):
                continue
            kept[index] = lines[index]

    try:
        for token in tokenize.generate_tokens(io.StringIO(source).readline):
            if token.type == tokenize.COMMENT:
                kept[token.start[0] - 1] = token.string
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "\n".join(kept)

    docstring_owners = (
        ast.Module,
        ast.ClassDef,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
    )
    for node in ast.walk(tree):
        if not isinstance(node, docstring_owners):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if not isinstance(first, ast.Expr):
            continue
        value = first.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        keep(value.lineno, value.end_lineno or value.lineno)

    return "\n".join(kept)


def _below_word_floor(path: Path, words: int) -> bool:
    """True when *path* is Python prose too short to score meaningfully.

    Gating only. `--audit` reports every finding whatever the length,
    because a finding is true regardless of how much surrounds it. It
    is the ratio that needs a denominator worth dividing by.
    """
    return path.suffix == ".py" and words < PYTHON_WORD_FLOOR


def _read_prose(path: Path) -> str:
    """The scorable prose of *path*: all of a .md, the comments of a .py."""
    text = path.read_text(errors="replace")
    return _python_prose(text) if path.suffix == ".py" else text


def _audit(paths: list, allow: frozenset) -> int:
    """Print every finding with its location. Always exits 0."""
    total = 0
    for path in paths:
        text = _read_prose(path)
        hits = audit_text(text, allowlist=allow)
        density = check_negation_density(text)
        if not hits and not density:
            continue
        print(f"{path}")
        for hit in hits:
            marker = "" if hit.confidence == "high" else f" ({hit.confidence})"
            print(f"  {path}:{hit.line}  {hit.category}{marker}  {hit.match!r}")
        for finding in density:
            print(f"  {path}: negation density  {finding.detail}")
        total += len(hits) + len(density)
    print(f"audited {len(paths)} files, {total} findings")
    print(
        "Findings marked (low) or (medium) are for a human to judge and are "
        "not gated. Rewrite guidance: .claude/rules/slop-scan-for-docs.md."
    )
    print(
        "A document that defines a pattern matches it. The rule files, the "
        "slop-detector modules and this catalog quote every tell they "
        "describe, so their hits are the definition, not a defect."
    )
    return 0


def _base_text(path: Path, ref: str) -> str | None:
    """The file as committed at *ref*, or None if it did not exist there."""
    shown = subprocess.run(
        ["git", "-C", str(path.parent), "show", f"{ref}:./{path.name}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if shown.returncode != 0:
        return None
    return _python_prose(shown.stdout) if path.suffix == ".py" else shown.stdout


def _ratchet(paths: list, allow: frozenset, ref: str, threshold: float) -> int:
    """Fail a file only if it is over the threshold and worse than at *ref*.

    Files already over the threshold are left as they are: a one-line
    edit to one of them should not wait on a whole-file cleanup. A file
    absent at *ref* is new and is held to the threshold alone.
    """
    failed = []
    for path in paths:
        current = score_text(_read_prose(path), allowlist=allow)
        if _below_word_floor(path, current.words):
            continue
        if current.score <= threshold:
            continue
        base_text = _base_text(path, ref)
        base = None if base_text is None else score_text(base_text, allowlist=allow)
        # A base under the floor is not a baseline. Comparing against a
        # 14-word docstring that scored 21 would let two hundred words
        # of new prose through as "not worse".
        if base is not None and _below_word_floor(path, base.words):
            base = None
        if base is not None and current.score <= base.score:
            continue
        failed.append((path, current, base))

    print(f"ratcheted {len(paths)} files against {ref}, {len(failed)} got worse")
    for path, current, base in failed:
        was = "new file" if base is None else f"was {base.score:.2f}"
        categories = sorted(
            {finding.category for finding in current.findings if finding.weight}
        )
        print(f"  {current.score:.2f} ({was})  {path}  [{', '.join(categories)}]")
    if failed:
        print(
            "Locate each finding: uv run --with pyyaml python "
            "scripts/slop_score.py --audit <file>"
        )
    return 1 if failed else 0


def main(argv: list | None = None) -> int:
    """Score every prose file under the given roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", help="directories or files to scan")
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument(
        "--audit",
        action="store_true",
        help=(
            "report every finding with a file and a line, opt-in and "
            "low-confidence categories included, and exit 0"
        ),
    )
    parser.add_argument(
        "--python",
        action="store_true",
        help=(
            "also sweep .py files under a directory root, scoring their "
            "comments and docstrings. A .py path named directly is always "
            "read this way. Off for a directory by default, because the "
            "gate CI runs is markdown. Pair it with --audit"
        ),
    )
    parser.add_argument(
        "--ratchet",
        metavar="REF",
        help=(
            "fail a file only when it is over the threshold and scores "
            "higher than its committed version at REF"
        ),
    )
    args = parser.parse_args(argv)

    allow = load_allowlist()
    try:
        paths = _iter_markdown(args.roots, python=args.python)
    except FileNotFoundError as missing:
        print(f"no such path: {missing.args[0]}")
        return 2

    if args.audit:
        return _audit(paths, allow)

    paths, excluded = _apply_excludes(paths, load_exclude_patterns())
    if excluded:
        print(f"excluded {len(excluded)} files ({CONFIG_NAME} exclude_patterns)")

    if args.ratchet:
        return _ratchet(paths, allow, args.ratchet, args.threshold)

    scored = []
    floored = []
    for path in paths:
        result = score_text(_read_prose(path), allowlist=allow)
        if not result.words:
            continue
        if _below_word_floor(path, result.words):
            floored.append(path)
            continue
        scored.append((result.score, path, result))

    if floored:
        print(
            f"{len(floored)} python files under the "
            f"{PYTHON_WORD_FLOOR}-word floor, not scored"
        )

    if not scored:
        print("no prose files scanned")
        return 0

    scored.sort(reverse=True, key=lambda row: row[0])
    over = [row for row in scored if row[0] > args.threshold]
    average = sum(row[0] for row in scored) / len(scored)

    print(f"scanned {len(scored)} files, avg {average:.2f}, max {scored[0][0]:.2f}")
    for score, path, result in over[: args.top]:
        categories = sorted(
            {finding.category for finding in result.findings if finding.weight}
        )
        print(f"  {score:.2f}  {path}  [{', '.join(categories)}]")
    if len(over) > args.top:
        print(f"  ... and {len(over) - args.top} more over {args.threshold}")

    surfaced = sorted(
        {
            finding.category
            for _, _, result in scored
            for finding in result.findings
            if not finding.weight
        }
    )
    if surfaced:
        print(
            "surfaced but not scored (low confidence, a human decides): "
            + ", ".join(surfaced)
        )

    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main())
