"""Render queue-entry frontmatter that any YAML reader parses back.

Stdlib only: hooks run under the system interpreter, where pyyaml may
be absent. Strings go out as JSON strings, because JSON string syntax
is a subset of YAML's double-quoted style, so ``json.dumps`` escapes
the quotes, newlines, and control characters that would otherwise
close the scalar early or start a new key. Page titles, queries, URLs
and session ids are outside this plugin's control, and one bare value
is enough to leave an entry that no downstream reader can parse.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime
from typing import Union

Scalar = Union[str, int, bool, datetime]


def _render_scalar(key: str, value: Scalar) -> str:
    # bool first: it is an int subclass, and YAML spells it lowercase.
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    # Unquoted so yaml.safe_load still returns a datetime, as readers of
    # created_at expect. isoformat() emits no YAML-significant characters.
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        # ensure_ascii would write an emoji as a \ud83d\ude80 surrogate
        # pair, which YAML reads back as two lone surrogates that cannot
        # be encoded. Quotes and control characters are still escaped.
        return json.dumps(value, ensure_ascii=False)
    raise TypeError(f"frontmatter field {key!r} has unsupported type {type(value)}")


def render_frontmatter(fields: Mapping[str, Scalar]) -> str:
    """Return a ``---`` delimited block with one line per field, in order."""
    lines = [f"{key}: {_render_scalar(key, value)}" for key, value in fields.items()]
    return "\n".join(["---", *lines, "---"])
