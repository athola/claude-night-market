#!/usr/bin/env python3
"""Nen Court validator: Markdown line wrapping at 80 characters (issue #406).

Graduates the "Markdown line wrapping at 80 chars" constraint from the
Soft Vow layer (skill instructions in CLAUDE.md / .claude/rules/) to the
Nen Court layer (external validator agent).

Contract (per imbue:vow-enforcement skill):

    input  (stdin JSON):
      {"text": "...", "filename": "x.md"}    -- single doc
      {"files": ["a.md", "b.md"]}            -- list of files

    output (stdout JSON):
      {
        "verdict": "pass" | "violation" | "inconclusive",
        "evidence": [{"file": "...", "line": N, "length": L, "preview": "..."}],
        "recommendation": "..."
      }

    exit code:
      0 = pass         (phase advances)
      1 = violation    (phase blocked until fixed or user overrides)
      2 = inconclusive (flag for human review, do not block)

The validator skips lines that cannot reasonably wrap: code blocks,
tables, headings, frontmatter, link/image references, and lines
dominated by URLs or inline code spans.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

DEFAULT_MAX_WIDTH = 80
_PREVIEW_MAX = 90  # Truncate evidence preview at 90 chars (just past 80-char rule).

_FENCE_PATTERN = re.compile(r"^\s*(```|~~~)")
_TABLE_PATTERN = re.compile(r"^\s*\|")
_HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s")
_LINK_REF_PATTERN = re.compile(r"^\s*\[[^\]]+\]:\s+\S+")
_FRONTMATTER_FENCE = re.compile(r"^---\s*$")
_URL_PATTERN = re.compile(r"https?://\S+")
_INLINE_CODE_PATTERN = re.compile(r"`[^`]+`")


_LINE_KIND_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (_FENCE_PATTERN, "code-fence"),
    (_FRONTMATTER_FENCE, "frontmatter-fence"),
    (_HEADING_PATTERN, "heading"),
    (_TABLE_PATTERN, "table"),
    (_LINK_REF_PATTERN, "link-ref"),
)


def classify_line(line: str, *, in_code_block: bool) -> str:
    """Classify a markdown line.

    Returns one of: 'blank', 'code-fence', 'code', 'heading', 'table',
    'link-ref', 'frontmatter-fence', 'prose'.
    """
    if in_code_block:
        return "code"
    stripped = line.rstrip()
    if stripped == "":
        return "blank"
    for pattern, kind in _LINE_KIND_RULES:
        if pattern.match(stripped):
            return kind
    return "prose"


def _strip_unwrappable_tokens(line: str) -> str:
    """Remove URLs and inline code spans before measuring length.

    Both are unbreakable -- a line whose excess length comes from a
    long URL or a long backtick-quoted token is not a wrap violation.
    """
    no_urls = _URL_PATTERN.sub("", line)
    no_inline_code = _INLINE_CODE_PATTERN.sub("", no_urls)
    return no_inline_code


def exceeds_budget(line: str, *, max_width: int = DEFAULT_MAX_WIDTH) -> bool:
    """Return True iff *line* breaks the wrap budget after stripping URLs/code."""
    if len(line) <= max_width:
        return False
    measured = _strip_unwrappable_tokens(line)
    return len(measured) > max_width


def validate_text(
    text: str,
    *,
    filename: str = "<text>",
    max_width: int = DEFAULT_MAX_WIDTH,
) -> dict[str, Any]:
    """Validate a single markdown document.

    Returns a verdict dict with verdict, evidence list, and recommendation.
    """
    in_code_block = False
    in_frontmatter = False
    evidence: list[dict[str, Any]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        # Track frontmatter state: doc starts with --- on line 1 -> in_frontmatter.
        if lineno == 1 and _FRONTMATTER_FENCE.match(raw):
            in_frontmatter = True
            continue
        if in_frontmatter:
            if _FRONTMATTER_FENCE.match(raw):
                in_frontmatter = False
            continue

        kind = classify_line(raw, in_code_block=in_code_block)
        if kind == "code-fence":
            in_code_block = not in_code_block
            continue
        if kind != "prose":
            continue
        if exceeds_budget(raw, max_width=max_width):
            evidence.append(
                {
                    "file": filename,
                    "line": lineno,
                    "length": len(raw),
                    "preview": raw[:_PREVIEW_MAX]
                    + ("..." if len(raw) > _PREVIEW_MAX else ""),
                }
            )

    if evidence:
        return {
            "verdict": "violation",
            "evidence": evidence,
            "recommendation": (
                "Wrap prose lines at 80 characters. Break at sentence "
                "boundaries first, then at clause/word boundaries. "
                "See .claude/rules/markdown-formatting.md."
            ),
        }
    return {"verdict": "pass", "evidence": [], "recommendation": ""}


def validate_files(
    paths: list[str], *, max_width: int = DEFAULT_MAX_WIDTH
) -> dict[str, Any]:
    """Validate a list of markdown files on disk.

    Aggregates verdicts: pass if all pass, violation if any violates,
    inconclusive if any file is missing or unreadable.
    """
    all_evidence: list[dict[str, Any]] = []
    inconclusive = False
    for path in paths:
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            inconclusive = True
            all_evidence.append(
                {"file": path, "error": "not found", "line": 0, "length": 0}
            )
            continue
        except OSError as exc:
            inconclusive = True
            all_evidence.append(
                {"file": path, "error": f"unreadable: {exc}", "line": 0, "length": 0}
            )
            continue
        result = validate_text(text, filename=path, max_width=max_width)
        all_evidence.extend(result["evidence"])

    real_violations = [ev for ev in all_evidence if "error" not in ev]
    if real_violations:
        return {
            "verdict": "violation",
            "evidence": all_evidence,
            "recommendation": (
                "Wrap prose lines at 80 characters. Break at sentence "
                "boundaries first, then at clause/word boundaries. "
                "See .claude/rules/markdown-formatting.md."
            ),
        }
    if inconclusive:
        return {
            "verdict": "inconclusive",
            "evidence": all_evidence,
            "recommendation": (
                "Some files were not found or could not be read; "
                "validator cannot determine compliance."
            ),
        }
    return {"verdict": "pass", "evidence": [], "recommendation": ""}


def main() -> None:
    """Entry point for stdin-driven validator invocation."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                {
                    "verdict": "inconclusive",
                    "evidence": [{"error": f"invalid JSON on stdin: {exc}"}],
                    "recommendation": "Send a JSON object with 'text' or 'files'.",
                }
            )
        )
        sys.exit(2)

    max_width = int(payload.get("max_width", DEFAULT_MAX_WIDTH))

    if "files" in payload:
        result = validate_files(list(payload["files"]), max_width=max_width)
    elif "text" in payload:
        result = validate_text(
            str(payload["text"]),
            filename=str(payload.get("filename", "<text>")),
            max_width=max_width,
        )
    else:
        result = {
            "verdict": "inconclusive",
            "evidence": [{"error": "missing 'text' or 'files' key"}],
            "recommendation": "Send a JSON object with 'text' or 'files'.",
        }

    print(json.dumps(result))
    if result["verdict"] == "pass":
        sys.exit(0)
    if result["verdict"] == "violation":
        sys.exit(1)
    sys.exit(2)


if __name__ == "__main__":
    main()
