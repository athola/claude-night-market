"""Shared decision-journal logic (leyline contract implementation).

Owns the single source of truth for two append-only, in-repo logs:

- ``docs/tradeoffs.md``      -- decisions and the alternatives sacrificed.
- ``docs/lessons-learned.md`` -- insights, failed approaches, rework.

Discipline (grounded in ADR/MADR + PMI/SRE practice):

- Append-only. Accepted entries are never edited or deleted; only ``Status``
  changes.
- Supersede, do not overwrite: a reversal adds a new entry, flips the old
  one's status, and links the two bidirectionally.
- Stable IDs (``TR-001`` / ``LL-001``) so links from PRs and code never break.
- A scannable ``## Active index`` keeps the live set readable as the log grows.

Plugin wrappers and ``scripts/journal_append.py`` import this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Kind configuration
# ---------------------------------------------------------------------------

_KINDS = {
    "tradeoffs": {
        "prefix": "TR",
        "title": "Tradeoffs",
        "default_status": "proposed",
        "intro": (
            "Decisions made over this project's lifetime, and the "
            "alternatives\nwe deliberately gave up. Records the *why*, not "
            "just the *what*.\n"
        ),
    },
    "lessons": {
        "prefix": "LL",
        "title": "Lessons Learned",
        "default_status": "open",
        "intro": (
            "Insights, failed approaches, rework, and blockers, captured "
            "blamelessly\nso the team replicates what worked and avoids what "
            "did not.\n"
        ),
    },
}


def _cfg(kind: str) -> dict[str, Any]:
    if kind not in _KINDS:
        raise ValueError(
            f"unknown journal kind {kind!r}; expected one of {sorted(_KINDS)}"
        )
    return _KINDS[kind]


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------

_ARCHIVE_HEADING = "## Archive"

_TRADEOFF_TEMPLATE = """\
<!-- ENTRY TEMPLATE -- copy a block into the Decisions section above the
Archive heading, assign the next TR-NNN id, and fill it in. The journal_append
helper does this automatically; this block is the fallback for hand-editing.

## TR-NNN: <short decision title>

- Status: proposed
- Date: YYYY-MM-DD
- Phase: brainstorm | specify | plan | execute | review
- Deciders: <names/roles>
- Links: <PR/commit/issue>, <code paths>

### Context & problem

<the situation forcing a choice>

### Decision drivers

- <competing quality / constraint>

### Options considered

| Option | Pros | Cons / what it sacrifices |
|--------|------|---------------------------|
| A (chosen) | ... | ... |
| B | ... | ... |

### Decision

We chose A.

### Y-statement

In the context of <X>, facing <concern>, we chose A over B,
to achieve <quality>, accepting <the sacrifice / road not taken>.

### Consequences

- Positive: <what gets easier>
- Negative / debt accepted: <what gets harder; revisit trigger>
-->
"""

_LESSON_TEMPLATE = """\
<!-- ENTRY TEMPLATE -- copy a block into the Lessons section above the Archive
heading, assign the next LL-NNN id, and fill it in. The journal_append helper
does this automatically; this block is the fallback for hand-editing.

## LL-NNN: <short lesson title>

- Status: open
- Date: YYYY-MM-DD
- Phase: execute | review
- Category: process | technology | requirements | testing | communication
- Owner: <who carries the follow-up>
- Links: <PR/commit/issue>, <related TR-NNN>

### What happened

<blameless, factual: the situation/activity>

### What went well / where we got lucky

<successes worth replicating>

### What did not work

<the gap or failure>

### Root cause

<5 Whys / contributing factors>

### Recommendation / action item

- Action: <specific change> -- Owner: <name> -- Due: <date> -- Status: <...>
-->
"""

_SECTION_HEADING = {"tradeoffs": "## Decisions", "lessons": "## Lessons"}


def new_file_content(kind: str) -> str:
    """Return the scaffold for a fresh journal file of ``kind``."""
    cfg = _cfg(kind)
    template = _TRADEOFF_TEMPLATE if kind == "tradeoffs" else _LESSON_TEMPLATE
    return (
        "---\n"
        "maturity: growing\n"
        f"type: {kind}\n"
        f"updated: {_today()}\n"
        "---\n\n"
        f"# {cfg['title']}\n\n"
        f"{cfg['intro']}\n"
        "## Active index\n\n"
        "| ID | Status | Title | Date |\n"
        "|----|--------|-------|------|\n\n"
        f"{_SECTION_HEADING[kind]}\n\n"
        f"{_ARCHIVE_HEADING}\n\n"
        "Superseded or deprecated entries sink here; nothing is deleted "
        "(git keeps history).\n\n"
        f"{template}"
    )


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


def next_id(content: str, prefix: str) -> str:
    """Return the next free ``<prefix>-NNN`` id given current file content."""
    # Capture the full integer (not exactly three digits) so the allocator
    # does not collide once the log passes 999 entries.
    pattern = rf"^## {re.escape(prefix)}-(\d+):"
    nums = [int(m) for m in re.findall(pattern, content, re.M)]
    nxt = (max(nums) + 1) if nums else 1
    return f"{prefix}-{nxt:03d}"


# ---------------------------------------------------------------------------
# Entry rendering
# ---------------------------------------------------------------------------


def _entry_key(fields: dict[str, Any]) -> str:
    """Stable dedup key from substantive fields (ignores status/date/phase)."""
    volatile = {"status", "date", "phase", "deciders", "owner", "links"}
    core = {k: v for k, v in fields.items() if k not in volatile}
    blob = json.dumps(core, sort_keys=True, ensure_ascii=False)
    # Not a security hash -- just a stable dedup fingerprint for idempotency.
    digest = hashlib.sha1(blob.encode("utf-8"), usedforsecurity=False)
    return digest.hexdigest()[:12]


def _oneline(text: str) -> str:
    """Collapse a value to a single trimmed line (safe for a heading)."""
    return " ".join(text.split())


def _opt_section(heading: str, value: object) -> str:
    if value is None or value in ("", []):
        return ""
    if isinstance(value, list):
        body = "\n".join(f"- {item}" for item in value)
    else:
        body = str(value)
    return f"\n### {heading}\n\n{body}\n"


def _render_options_table(options: list[dict[str, Any]]) -> str:
    if not options:
        return ""
    rows = [
        "\n### Options considered\n",
        "| Option | Pros | Cons / what it sacrifices |",
        "|--------|------|---------------------------|",
    ]
    for opt in options:
        name = opt.get("name", "?")
        if opt.get("chosen"):
            name = f"{name} (chosen)"
        pros = _escape_cell(str(opt.get("pros", "")))
        cons = _escape_cell(str(opt.get("cons", "")))
        rows.append(f"| {_escape_cell(str(name))} | {pros} | {cons} |")
    return "\n".join(rows) + "\n"


def _render_tradeoff(
    entry_id: str, fields: dict[str, Any], supersedes: str | None
) -> str:
    status = fields.get("status", _KINDS["tradeoffs"]["default_status"])
    meta = [
        f"- Status: {status}",
        f"- Date: {fields.get('date', _today())}",
        f"- Phase: {fields.get('phase', '-')}",
        f"- Deciders: {fields.get('deciders', '-')}",
        f"- Links: {fields.get('links', '-')}",
    ]
    if supersedes:
        meta.append(f"- Supersedes: {supersedes}")
    meta.append(f"<!-- key: {_entry_key(fields)} -->")
    cons = ""
    pos = fields.get("consequences_positive")
    neg = fields.get("consequences_negative")
    if pos or neg:
        cons = "\n### Consequences\n\n"
        if pos:
            cons += f"- Positive: {pos}\n"
        if neg:
            cons += f"- Negative / debt accepted: {neg}\n"
    body = (
        f"## {entry_id}: {_oneline(fields['title'])}\n\n"
        + "\n".join(meta)
        + "\n"
        + _opt_section("Context & problem", fields.get("context"))
        + _opt_section("Decision drivers", fields.get("drivers"))
        + _render_options_table(fields.get("options", []))
        + _opt_section("Decision", fields.get("decision"))
        + _opt_section("Y-statement", fields.get("ystatement"))
        + cons
    )
    return body.rstrip() + "\n"


def _render_lesson(
    entry_id: str, fields: dict[str, Any], supersedes: str | None
) -> str:
    status = fields.get("status", _KINDS["lessons"]["default_status"])
    meta = [
        f"- Status: {status}",
        f"- Date: {fields.get('date', _today())}",
        f"- Phase: {fields.get('phase', '-')}",
        f"- Category: {fields.get('category', '-')}",
        f"- Owner: {fields.get('owner', '-')}",
        f"- Links: {fields.get('links', '-')}",
    ]
    if supersedes:
        meta.append(f"- Supersedes: {supersedes}")
    meta.append(f"<!-- key: {_entry_key(fields)} -->")
    body = (
        f"## {entry_id}: {_oneline(fields['title'])}\n\n"
        + "\n".join(meta)
        + "\n"
        + _opt_section("What happened", fields.get("what_happened"))
        + _opt_section(
            "What went well / where we got lucky", fields.get("what_went_well")
        )
        + _opt_section("What did not work", fields.get("what_didnt_work"))
        + _opt_section("Root cause", fields.get("root_cause"))
        + _opt_section("Recommendation / action item", fields.get("action"))
    )
    return body.rstrip() + "\n"


# ---------------------------------------------------------------------------
# Active index maintenance
# ---------------------------------------------------------------------------


def _require(content: str, marker: str, *, start: int = 0) -> int:
    """Locate ``marker`` or raise a clear "malformed journal" error."""
    pos = content.find(marker, start)
    if pos == -1:
        raise ValueError(
            f"journal is malformed: required marker {marker!r} not found; "
            "the file may have been hand-edited. Restore the section or "
            "regenerate it from the scaffold."
        )
    return pos


def _index_bounds(content: str) -> tuple[int, int]:
    start = _require(content, "## Active index")
    nxt = _require(content, "\n## ", start=start + 1)
    return start, nxt


def _escape_cell(text: str) -> str:
    """Make free text safe for a markdown table cell (escape pipes, flatten)."""
    return text.replace("|", r"\|").replace("\n", " ")


def _add_index_row(
    content: str, entry_id: str, status: str, title: str, date: str
) -> str:
    start, nxt = _index_bounds(content)
    section = content[start:nxt]
    row = f"| {entry_id} | {status} | {_escape_cell(title)} | {date} |"
    lines = section.rstrip("\n").splitlines()
    # Append after the last table line (header/separator/existing rows).
    insert_at = max(i for i, ln in enumerate(lines) if ln.lstrip().startswith("|"))
    lines.insert(insert_at + 1, row)
    return content[:start] + "\n".join(lines) + "\n\n" + content[nxt + 1 :]


def _set_index_status(content: str, entry_id: str, status: str) -> str:
    start, nxt = _index_bounds(content)
    section = content[start:nxt]
    pattern = re.compile(rf"(\|\s*{re.escape(entry_id)}\s*\|\s*)[^|]*(\|)")
    section2 = pattern.sub(rf"\g<1>{status} \g<2>", section, count=1)
    return content[:start] + section2 + content[nxt:]


# ---------------------------------------------------------------------------
# Append
# ---------------------------------------------------------------------------


def append_entry(
    content: str,
    kind: str,
    fields: dict[str, Any],
    supersedes: str | None = None,
) -> str:
    """Return ``content`` with a new entry appended (pure transform).

    Idempotent: appending an entry whose substantive fields already appear in
    the file returns the content unchanged.
    """
    cfg = _cfg(kind)
    if not str(fields.get("title", "")).strip():
        raise ValueError("entry requires a non-empty 'title'")

    # Idempotency: skip if an entry with this key is already present.
    key = _entry_key(fields)
    if f"<!-- key: {key} -->" in content:
        return content

    if supersedes is not None:
        if f"## {supersedes}:" not in content:
            raise ValueError(f"cannot supersede unknown entry {supersedes!r}")

    entry_id = next_id(content, cfg["prefix"])
    render = _render_tradeoff if kind == "tradeoffs" else _render_lesson
    entry = render(entry_id, fields, supersedes)

    # Insert the entry above the Archive heading.
    marker = f"\n{_ARCHIVE_HEADING}"
    pos = _require(content, marker)
    new_content = content[:pos] + "\n" + entry + content[pos:]

    # Update the active index.
    status = fields.get("status", cfg["default_status"])
    new_content = _add_index_row(
        new_content, entry_id, status, fields["title"], fields.get("date", _today())
    )

    # Supersession: flip the old entry's status + index row.
    if supersedes is not None:
        new_content = _supersede(new_content, supersedes, entry_id)

    return new_content


def _supersede(content: str, old_id: str, new_id: str) -> str:
    """Flip ``old_id``'s status line to point at ``new_id`` and update index."""
    old_start = _require(content, f"## {old_id}:")
    # Bound the search to this entry only (up to the next heading), so a
    # missing Status line is detected rather than silently grabbing the next
    # entry's status.
    # A heading (at minimum "## Archive") always follows an entry.
    entry_end = _require(content, "\n## ", start=old_start + 1)
    status_re = re.compile(r"^- Status: .*$", re.M)
    m = status_re.search(content, old_start, entry_end)
    if m is None:
        raise ValueError(
            f"entry {old_id} has no '- Status:' line to supersede; "
            "the entry may have been hand-edited."
        )
    new_status = f"- Status: superseded-by: {new_id}"
    content = content[: m.start()] + new_status + content[m.end() :]
    content = _set_index_status(content, old_id, f"superseded-by: {new_id}")
    return content


# ---------------------------------------------------------------------------
# File-level apply
# ---------------------------------------------------------------------------


def apply_append(
    path: Path,
    kind: str,
    fields: dict[str, Any],
    supersedes: str | None = None,
    dry_run: bool = False,
) -> str:
    """Append an entry to ``path`` (creating the file if missing).

    Returns the resulting file content. With ``dry_run`` nothing is written.
    """
    path = Path(path)
    content = (
        path.read_text(encoding="utf-8") if path.exists() else new_file_content(kind)
    )
    new_content = append_entry(content, kind, fields, supersedes)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new_content, encoding="utf-8")
    return new_content
