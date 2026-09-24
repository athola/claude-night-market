"""Read labelled fields and sections out of review and learnings markdown.

Split from ``utils`` for the same reason as ``paths``: ``utils`` imports
PyYAML, and the Discussions posting scripts run under the operator's
``python3``, which has only the standard library. ``utils`` re-exports
both functions.
"""

from __future__ import annotations

import re

__all__ = ["extract_bold_field", "extract_section"]


def extract_bold_field(text: str, field: str) -> str:
    """Extract a ``**Field**: value`` pair from a markdown body.

    Companion to :func:`extract_section`: that returns a section body,
    this reads one labelled field out of it.

    Returns:
        The trimmed value, or an empty string when the field is absent.

    """
    match = re.search(rf"\*\*{re.escape(field)}\*\*:\s*(.+)", text)
    return match.group(1).strip() if match else ""


def extract_section(content: str, heading: str) -> str | None:
    """Extract the body of a markdown ``## Section`` heading (D-03).

    Returns the text between ``heading`` and the next ``## ``
    heading, ``---`` rule, or end-of-document. ``heading`` should
    include the leading ``## `` so the caller can target deeper
    levels. Result is ``None`` when the heading is not found and
    the matched body is ``strip()``-ed.
    """
    # F1 fix: the lookahead must terminate when the next ``## `` /
    # ``---`` is at the start of the very next line (no preceding
    # blank line). The original ``\n## ``/``\n---`` lookahead missed
    # that case and captured the next section's body too.
    pattern = re.escape(heading) + r"(?:\n|$)(.*?)(?=(?:\n|^)## |(?:\n|^)---|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else None
