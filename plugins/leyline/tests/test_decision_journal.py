"""Tests for the leyline decision-journal contract implementation.

Covers the pure string transforms (scaffold creation, ID allocation,
entry append, supersession, idempotency) and the file-level apply helper
(create-if-missing, dry-run no-write).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from leyline.decision_journal import (
    append_entry,
    apply_append,
    new_file_content,
    next_id,
)

# ---------------------------------------------------------------------------
# Scaffold creation
# ---------------------------------------------------------------------------


def test_new_file_tradeoffs_has_required_markers() -> None:
    content = new_file_content("tradeoffs")
    assert "maturity: growing" in content
    assert "## Active index" in content
    assert "## Archive" in content
    # Entry template ships inside the file so the fallback path (leyline
    # absent) can still produce a correctly shaped entry.
    assert "ENTRY TEMPLATE" in content
    assert "TR-NNN" in content


def test_new_file_lessons_has_required_markers() -> None:
    content = new_file_content("lessons")
    assert "maturity: growing" in content
    assert "## Active index" in content
    assert "## Archive" in content
    assert "LL-NNN" in content


def test_new_file_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError):
        new_file_content("nonsense")


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


def test_next_id_empty_scaffold_is_001() -> None:
    assert next_id(new_file_content("tradeoffs"), "TR") == "TR-001"
    assert next_id(new_file_content("lessons"), "LL") == "LL-001"


def test_next_id_ignores_template_placeholder() -> None:
    # The footer ENTRY TEMPLATE mentions TR-NNN; it must not be counted.
    content = new_file_content("tradeoffs")
    assert next_id(content, "TR") == "TR-001"


def test_next_id_increments_after_real_entry() -> None:
    content = append_entry(
        new_file_content("tradeoffs"),
        "tradeoffs",
        {"title": "Pick Postgres", "context": "Need durable storage."},
    )
    assert next_id(content, "TR") == "TR-002"


# ---------------------------------------------------------------------------
# Append behaviour
# ---------------------------------------------------------------------------


def test_append_adds_heading_and_index_row() -> None:
    content = append_entry(
        new_file_content("tradeoffs"),
        "tradeoffs",
        {"title": "Pick Postgres", "context": "Need durable storage."},
    )
    assert "## TR-001: Pick Postgres" in content
    # Active index gets a scannable row referencing the new ID.
    index_region = content.split("## Active index", 1)[1].split("## ", 1)[0]
    assert "TR-001" in index_region


def test_append_inserts_entry_above_archive() -> None:
    content = append_entry(
        new_file_content("tradeoffs"),
        "tradeoffs",
        {"title": "Pick Postgres", "context": "x"},
    )
    assert content.index("## TR-001:") < content.index("## Archive")


def test_tradeoff_default_status_proposed() -> None:
    content = append_entry(
        new_file_content("tradeoffs"),
        "tradeoffs",
        {"title": "Pick Postgres", "context": "x"},
    )
    entry = content.split("## TR-001:", 1)[1]
    assert "Status: proposed" in entry


def test_lesson_default_status_open() -> None:
    content = append_entry(
        new_file_content("lessons"),
        "lessons",
        {"title": "Cache stampede", "what_happened": "x"},
    )
    entry = content.split("## LL-001:", 1)[1]
    assert "Status: open" in entry


def test_second_append_increments_and_keeps_first() -> None:
    content = new_file_content("tradeoffs")
    content = append_entry(content, "tradeoffs", {"title": "A", "context": "x"})
    content = append_entry(content, "tradeoffs", {"title": "B", "context": "y"})
    assert "## TR-001: A" in content
    assert "## TR-002: B" in content


# ---------------------------------------------------------------------------
# Supersession
# ---------------------------------------------------------------------------


def test_supersede_flips_old_status_and_adds_backlinks() -> None:
    content = new_file_content("tradeoffs")
    content = append_entry(content, "tradeoffs", {"title": "Use REST", "context": "x"})
    content = append_entry(
        content,
        "tradeoffs",
        {"title": "Switch to gRPC", "context": "perf"},
        supersedes="TR-001",
    )
    old = content.split("## TR-001:", 1)[1].split("## TR-002:", 1)[0]
    new = content.split("## TR-002:", 1)[1]
    assert "superseded-by: TR-002" in old
    assert "Supersedes: TR-001" in new


def test_supersede_unknown_id_raises() -> None:
    content = new_file_content("tradeoffs")
    with pytest.raises(ValueError):
        append_entry(
            content,
            "tradeoffs",
            {"title": "B", "context": "x"},
            supersedes="TR-999",
        )


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_identical_append_is_idempotent() -> None:
    fields = {"title": "Pick Postgres", "context": "Need durable storage."}
    once = append_entry(new_file_content("tradeoffs"), "tradeoffs", dict(fields))
    twice = append_entry(once, "tradeoffs", dict(fields))
    assert once == twice
    assert once.count("## TR-001:") == 1


# ---------------------------------------------------------------------------
# Rich-field rendering
# ---------------------------------------------------------------------------


def test_tradeoff_renders_drivers_options_and_consequences() -> None:
    content = append_entry(
        new_file_content("tradeoffs"),
        "tradeoffs",
        {
            "title": "Adopt event-driven core",
            "context": "decoupling needed",
            "drivers": ["latency", "loose coupling"],
            "options": [
                {
                    "name": "Event bus",
                    "pros": "decoupled",
                    "cons": "harder to trace",
                    "chosen": True,
                },
                {"name": "Direct calls", "pros": "simple", "cons": "tight coupling"},
            ],
            "decision": "Use an event bus.",
            "consequences_positive": "subscribers scale independently",
            "consequences_negative": "tracing is harder",
        },
    )
    entry = content.split("## TR-001:", 1)[1]
    assert "### Decision drivers" in entry
    assert "- latency" in entry
    assert "### Options considered" in entry
    assert "Event bus (chosen)" in entry
    assert "Direct calls |" in entry
    assert "### Consequences" in entry
    assert "- Positive: subscribers scale independently" in entry
    assert "- Negative / debt accepted: tracing is harder" in entry


def test_lesson_renders_all_optional_sections() -> None:
    content = append_entry(
        new_file_content("lessons"),
        "lessons",
        {
            "title": "Migration rollback",
            "what_happened": "the migration locked the table",
            "what_went_well": "we caught it in staging",
            "what_didnt_work": "the online-migration assumption",
            "root_cause": "missing CONCURRENTLY",
            "action": "add a migration lint rule",
        },
    )
    entry = content.split("## LL-001:", 1)[1]
    assert "### What happened" in entry
    assert "### What went well / where we got lucky" in entry
    assert "### What did not work" in entry
    assert "### Root cause" in entry
    assert "### Recommendation / action item" in entry


def test_append_requires_non_empty_title() -> None:
    with pytest.raises(ValueError, match="title"):
        append_entry(new_file_content("tradeoffs"), "tradeoffs", {"context": "x"})


def test_lesson_supersession_links_both_ways() -> None:
    content = new_file_content("lessons")
    content = append_entry(
        content, "lessons", {"title": "Old finding", "what_happened": "x"}
    )
    content = append_entry(
        content,
        "lessons",
        {"title": "Revised finding", "what_happened": "y"},
        supersedes="LL-001",
    )
    old = content.split("## LL-001:", 1)[1].split("## LL-002:", 1)[0]
    new = content.split("## LL-002:", 1)[1]
    assert "superseded-by: LL-002" in old
    assert "Supersedes: LL-001" in new


# ---------------------------------------------------------------------------
# Robustness: table-breaking characters and cross-tool compatibility
# ---------------------------------------------------------------------------


def test_index_row_escapes_pipe_in_title() -> None:
    """A pipe in the title must not add a stray column to the index table."""
    content = append_entry(
        new_file_content("tradeoffs"),
        "tradeoffs",
        {"title": "Use A | B routing", "context": "x"},
    )
    index = content.split("## Active index", 1)[1].split("## Decisions", 1)[0]
    row = next(ln for ln in index.splitlines() if ln.startswith("| TR-001"))
    # Four data cells (id, status, title, date) => exactly five unescaped pipes.
    assert row.replace(r"\|", "").count("|") == 5
    assert r"\|" in row


def test_append_works_on_vendored_style_scaffold() -> None:
    """Guard the contract attune:project-init's vendored fallback relies on.

    When leyline is absent, attune scaffolds the journal from its own vendored
    template. A file created that way may later be appended to by leyline, so
    leyline's appender must accept the shared structural shape: frontmatter, an
    Active index table, a Decisions section, an Archive heading, and a footer
    template. This pins that contract from leyline's side.
    """
    vendored = (
        "---\nmaturity: growing\ntype: tradeoffs\n---\n\n"
        "# Tradeoffs\n\nintro\n\n"
        "## Active index\n\n"
        "| ID | Status | Title | Date |\n"
        "|----|--------|-------|------|\n\n"
        "## Decisions\n\n"
        "## Archive\n\nnote\n\n"
        "<!-- ENTRY TEMPLATE ... TR-NNN ... -->\n"
    )
    out = append_entry(vendored, "tradeoffs", {"title": "X", "context": "y"})
    assert "## TR-001: X" in out
    assert out.index("## TR-001:") < out.index("## Archive")
    index = out.split("## Active index", 1)[1].split("## Decisions", 1)[0]
    assert "TR-001" in index


# ---------------------------------------------------------------------------
# File-level apply helper
# ---------------------------------------------------------------------------


def test_apply_append_creates_file_when_missing(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "tradeoffs.md"
    apply_append(target, "tradeoffs", {"title": "A", "context": "x"})
    assert target.exists()
    assert "## TR-001: A" in target.read_text()


def test_apply_append_dry_run_writes_nothing(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "tradeoffs.md"
    result = apply_append(
        target, "tradeoffs", {"title": "A", "context": "x"}, dry_run=True
    )
    assert not target.exists()
    assert "## TR-001: A" in result  # returns what it *would* write
