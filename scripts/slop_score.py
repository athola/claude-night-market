#!/usr/bin/env python3
"""Score markdown for AI slop, sourcing every pattern from the YAML.

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
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "plugins" / "scribe" / "src"))

from scribe.pattern_loader import (  # noqa: E402 - path must be set before import
    get_tier1_words,
    get_tier2_words,
    get_tier5_patterns,
    load_language_patterns,
)

TIER1_WEIGHT = 3
TIER2_WEIGHT = 2
EM_DASH_WEIGHT = 1

CONFIG_NAME = ".slop-config.yaml"

_FENCED_CODE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
_INLINE_CODE = re.compile(r"`[^`\n]*`")


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


def load_allowlist(config_path: Path | None = None) -> frozenset:
    """Read the `allowlist` field from a .slop-config.yaml.

    Only that field is read. `config-file.md` documents more, and a
    config that sets the rest gets no error and no effect here, which
    is worth knowing before relying on it.
    """
    path = config_path or (_REPO_ROOT / CONFIG_NAME)
    if not path.is_file():
        return frozenset()
    try:
        import yaml  # noqa: PLC0415 - deferred so a missing pyyaml degrades to an empty allowlist rather than breaking the gate

        loaded = yaml.safe_load(path.read_text()) or {}
    except (OSError, ValueError):
        return frozenset()
    return frozenset(str(word).lower() for word in loaded.get("allowlist", []) or [])


def _prose_only(text: str) -> str:
    """Drop code spans, where a slop word is a symbol rather than prose."""
    return _INLINE_CODE.sub(" ", _FENCED_CODE.sub(" ", text))


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
    return rules


_RULES_CACHE: list = []


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
        for match in regex.finditer(prose):
            if match.group(0).lower() in allow:
                continue
            findings.append(
                Finding(category=category, match=match.group(0), weight=weight)
            )
            weighted += weight

    return Score(score=weighted / words * 100, words=words, findings=findings)


def main(argv: list | None = None) -> int:
    """Score every markdown file under the given roots."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", help="directories to scan")
    parser.add_argument("--threshold", type=float, default=3.0)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args(argv)

    allow = load_allowlist()
    scored = []
    for root in args.roots:
        for path in sorted(Path(root).rglob("*.md")):
            if any(
                part in {".git", "worktrees", "node_modules", "__pycache__", ".venv"}
                for part in path.parts
            ):
                continue
            result = score_text(path.read_text(errors="replace"), allowlist=allow)
            if result.words:
                scored.append((result.score, path, result))

    if not scored:
        print("no markdown files scanned")
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
