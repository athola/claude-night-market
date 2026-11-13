"""Read the text out of a transcript content block.

A ``tool_result`` block carries ``content`` either as a string or as a
list of ``{"type": "text", "text": ...}`` items, and the list is what
Claude Code usually writes. Walkers that assumed a string crashed or
counted the list's length.
"""

from __future__ import annotations

__all__ = ["block_text"]


def block_text(block: dict) -> str:
    """Return every piece of text in *block*, joined by newlines."""
    text = block.get("text")
    if isinstance(text, str) and text:
        return text
    content = block.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    pieces = []
    for item in content:
        if isinstance(item, str):
            pieces.append(item)
        elif isinstance(item, dict) and isinstance(item.get("text"), str):
            pieces.append(item["text"])
    return "\n".join(pieces)
