# ruff: noqa: D101,D102,D103,PLR2004,PLC0415,S603,S607
"""Unit tests for the deferred_item_watcher PostToolUse hook.

Tests cover: watch-list filtering, deferral detection regex,
title extraction, and ledger read/write operations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import deferred_item_watcher as mod
import pytest
from deferred_item_watcher import (
    WATCH_LIST,
    extract_deferred_titles,
    read_ledger,
    scan_for_deferrals,
    should_process,
    update_ledger_entry,
    write_ledger_entry,
)

# ---------------------------------------------------------------------------
# 1. TestWatchList: env-var filtering of tool name and skill name
# ---------------------------------------------------------------------------


class TestWatchList:
    """Test that only watched Skill invocations are processed."""

    def test_non_skill_tool_is_ignored(self) -> None:
        """Non-Skill tools (Bash, Read, etc.) are not processed."""
        with patch.dict(
            os.environ, {"CLAUDE_TOOL_NAME": "Bash", "CLAUDE_TOOL_INPUT": "{}"}
        ):
            assert should_process() is False

    def test_skill_tool_name_required(self) -> None:
        """CLAUDE_TOOL_NAME must equal 'Skill' to proceed."""
        with patch.dict(
            os.environ, {"CLAUDE_TOOL_NAME": "skill", "CLAUDE_TOOL_INPUT": "{}"}
        ):
            assert should_process() is False

    def test_unwatched_skill_is_ignored(self) -> None:
        """Skills not in WATCH_LIST are not processed."""
        tool_input = json.dumps({"skill": "commit-messages"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is False

    def test_war_room_is_watched(self) -> None:
        """war-room skill is in the watch list."""
        tool_input = json.dumps({"skill": "war-room"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_brainstorm_is_watched(self) -> None:
        """brainstorm skill is in the watch list."""
        tool_input = json.dumps({"skill": "brainstorm"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_scope_guard_is_watched(self) -> None:
        """scope-guard skill is in the watch list."""
        tool_input = json.dumps({"skill": "scope-guard"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_feature_review_is_watched(self) -> None:
        """feature-review skill is in the watch list."""
        tool_input = json.dumps({"skill": "feature-review"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_unified_review_is_watched(self) -> None:
        """unified-review skill is in the watch list."""
        tool_input = json.dumps({"skill": "unified-review"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_rollback_reviewer_is_watched(self) -> None:
        """rollback-reviewer skill is in the watch list."""
        tool_input = json.dumps({"skill": "rollback-reviewer"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_watch_list_contains_exactly_six_skills(self) -> None:
        """WATCH_LIST contains the six canonical skills."""
        assert WATCH_LIST == {
            "war-room",
            "brainstorm",
            "scope-guard",
            "feature-review",
            "unified-review",
            "rollback-reviewer",
        }

    def test_plugin_qualified_skill_name_is_watched(self) -> None:
        """Skills specified as 'plugin:skill' are normalised and matched."""
        tool_input = json.dumps({"skill": "sanctum:war-room"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_missing_tool_input_does_not_crash(self) -> None:
        """Missing CLAUDE_TOOL_INPUT defaults to no-match gracefully."""
        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "Skill"}, clear=False):
            os.environ.pop("CLAUDE_TOOL_INPUT", None)
            result = should_process()
        assert result is False


# ---------------------------------------------------------------------------
# 2. TestDeferralDetection: scan_for_deferrals() regex coverage
# ---------------------------------------------------------------------------


class TestDeferralDetection:
    """Test that scan_for_deferrals() correctly identifies deferral signals."""

    def test_deferred_marker_triggers(self) -> None:
        """[Deferred] marker triggers a positive result."""
        assert scan_for_deferrals("[Deferred] Add OAuth support") is True

    def test_out_of_scope_triggers(self) -> None:
        """'out of scope' phrase triggers a positive result."""
        assert (
            scan_for_deferrals("This feature is out of scope for this cycle.") is True
        )

    def test_not_yet_applicable_triggers(self) -> None:
        """'not yet applicable' phrase triggers a positive result."""
        assert scan_for_deferrals("This change is not yet applicable.") is True

    def test_future_cycle_triggers(self) -> None:
        """'future cycle' phrase triggers a positive result."""
        assert scan_for_deferrals("Address this in a future cycle.") is True

    def test_rejected_word_boundary_triggers(self) -> None:
        """'rejected' at a word boundary triggers a positive result."""
        assert scan_for_deferrals("This proposal was rejected by the team.") is True

    def test_deferred_word_boundary_triggers(self) -> None:
        """'deferred' at a word boundary triggers a positive result."""
        assert scan_for_deferrals("The task was deferred to next sprint.") is True

    def test_case_insensitive_out_of_scope(self) -> None:
        """Pattern matching is case insensitive."""
        assert scan_for_deferrals("OUT OF SCOPE for now.") is True

    def test_case_insensitive_deferred(self) -> None:
        """Pattern matching is case insensitive for 'DEFERRED'."""
        assert scan_for_deferrals("Status: DEFERRED") is True

    def test_rejected_not_triggered_mid_word(self) -> None:
        """'rejected' embedded mid-word does not trigger (word boundary)."""
        assert scan_for_deferrals("The change was unrejected after review.") is False

    def test_deferred_not_triggered_mid_word(self) -> None:
        """'deferred' embedded in another word does not match."""
        assert scan_for_deferrals("The nondeferred item was completed.") is False

    def test_normal_completion_text_does_not_trigger(self) -> None:
        """Normal completion text returns False."""
        assert (
            scan_for_deferrals("Task completed successfully. All tests pass.") is False
        )

    def test_empty_string_does_not_trigger(self) -> None:
        """Empty string returns False."""
        assert scan_for_deferrals("") is False

    def test_multiline_text_with_signal_triggers(self) -> None:
        """Signal on any line within a multiline block triggers True."""
        text = (
            "## War Room Results\n"
            "- Item A: completed\n"
            "[Deferred] Add retry logic\n"
            "- Item B: completed\n"
        )
        assert scan_for_deferrals(text) is True


# ---------------------------------------------------------------------------
# 3. TestTitleExtraction: extract_deferred_titles()
# ---------------------------------------------------------------------------


class TestTitleExtraction:
    """Test that extract_deferred_titles() pulls titles from [Deferred] markers."""

    def test_extracts_single_marker(self) -> None:
        """Single [Deferred] marker yields one title."""
        titles = extract_deferred_titles("[Deferred] Add OAuth support")
        assert titles == ["Add OAuth support"]

    def test_extracts_multiple_markers(self) -> None:
        """Multiple [Deferred] markers are all extracted."""
        text = (
            "Some text.\n"
            "[Deferred] Improve error messages\n"
            "More text.\n"
            "[Deferred] Refactor database layer\n"
        )
        titles = extract_deferred_titles(text)
        assert "Improve error messages" in titles
        assert "Refactor database layer" in titles
        assert len(titles) == 2

    def test_fallback_when_signal_but_no_marker(self) -> None:
        """When deferral signal exists but no [Deferred] marker, return
        fallback title."""
        titles = extract_deferred_titles(
            "This feature is out of scope for this release."
        )
        assert titles == ["Untitled deferred item"]

    def test_empty_text_returns_fallback(self) -> None:
        """Phrase with signal but no marker returns fallback list."""
        titles = extract_deferred_titles("out of scope")
        assert titles == ["Untitled deferred item"]

    def test_strips_leading_whitespace_from_title(self) -> None:
        """Titles extracted from markers have leading/trailing whitespace
        stripped."""
        titles = extract_deferred_titles("[Deferred]   Trim me   ")
        assert titles == ["Trim me"]

    def test_marker_at_end_of_line_yields_nonempty_title(self) -> None:
        """A [Deferred] marker followed only by spaces returns fallback
        for that entry."""
        titles = extract_deferred_titles("[Deferred]   \n")
        assert "Untitled deferred item" in titles

    def test_prefix_stripped_from_title(self) -> None:
        """The [Deferred] prefix itself is NOT included in the title."""
        titles = extract_deferred_titles("[Deferred] Some feature")
        assert all("[Deferred]" not in t for t in titles)


# ---------------------------------------------------------------------------
# 4. TestLedger: read/write/update operations
# ---------------------------------------------------------------------------


class TestLedger:
    """Test ledger file operations for deferred item persistence."""

    def test_write_and_read_roundtrip(self, tmp_path: Path) -> None:
        """An entry written to the ledger can be read back intact."""
        ledger_path = tmp_path / "deferred-items-session.json"
        entry = {
            "title": "Add OAuth support",
            "source": "war-room",
            "filed": False,
            "timestamp": "2026-03-19T10:00:00",
        }
        write_ledger_entry(ledger_path, entry)
        entries = read_ledger(ledger_path)

        assert len(entries) == 1
        assert entries[0]["title"] == "Add OAuth support"
        assert entries[0]["source"] == "war-room"
        assert entries[0]["filed"] is False

    def test_multiple_entries_accumulate(self, tmp_path: Path) -> None:
        """Multiple write_ledger_entry calls accumulate all entries."""
        ledger_path = tmp_path / "deferred-items-session.json"
        for i in range(3):
            write_ledger_entry(
                ledger_path,
                {
                    "title": f"Item {i}",
                    "source": "brainstorm",
                    "filed": False,
                    "timestamp": "2026-03-19T10:00:00",
                },
            )
        entries = read_ledger(ledger_path)
        assert len(entries) == 3

    def test_read_nonexistent_ledger_returns_empty_list(self, tmp_path: Path) -> None:
        """Reading a ledger that does not exist returns an empty list."""
        ledger_path = tmp_path / "no-such-file.json"
        assert read_ledger(ledger_path) == []

    def test_read_corrupt_ledger_returns_empty_list(self, tmp_path: Path) -> None:
        """Reading a corrupt JSON ledger returns an empty list gracefully."""
        ledger_path = tmp_path / "corrupt.json"
        ledger_path.write_text("{corrupt json!!!")
        assert read_ledger(ledger_path) == []

    def test_update_ledger_entry_sets_filed(self, tmp_path: Path) -> None:
        """update_ledger_entry marks the matching entry as filed=True."""
        ledger_path = tmp_path / "deferred-items-session.json"
        write_ledger_entry(
            ledger_path,
            {
                "title": "Add retry logic",
                "source": "scope-guard",
                "filed": False,
                "timestamp": "2026-03-19T10:00:00",
            },
        )
        update_ledger_entry(
            ledger_path, title="Add retry logic", filed=True, issue_number=42
        )
        entries = read_ledger(ledger_path)
        assert entries[0]["filed"] is True
        assert entries[0]["issue_number"] == 42

    def test_update_nonexistent_title_is_noop(self, tmp_path: Path) -> None:
        """Updating a title that does not exist does not modify other entries."""
        ledger_path = tmp_path / "deferred-items-session.json"
        write_ledger_entry(
            ledger_path,
            {
                "title": "Existing item",
                "source": "war-room",
                "filed": False,
                "timestamp": "2026-03-19T10:00:00",
            },
        )
        update_ledger_entry(
            ledger_path, title="Nonexistent item", filed=True, issue_number=99
        )
        entries = read_ledger(ledger_path)
        assert entries[0]["filed"] is False

    def test_write_normalizes_deferred_prefix_from_title(self, tmp_path: Path) -> None:
        """Titles stored in the ledger have the '[Deferred] ' prefix stripped."""
        ledger_path = tmp_path / "deferred-items-session.json"
        write_ledger_entry(
            ledger_path,
            {
                "title": "[Deferred] Some feature",
                "source": "war-room",
                "filed": False,
                "timestamp": "2026-03-19T10:00:00",
            },
        )
        entries = read_ledger(ledger_path)
        assert entries[0]["title"] == "Some feature"

    def test_update_matches_normalized_title(self, tmp_path: Path) -> None:
        """update_ledger_entry matches by normalized title (no prefix)."""
        ledger_path = tmp_path / "deferred-items-session.json"
        write_ledger_entry(
            ledger_path,
            {
                "title": "Some feature",
                "source": "war-room",
                "filed": False,
                "timestamp": "2026-03-19T10:00:00",
            },
        )
        # Update using prefixed variant -- should still match after normalization
        update_ledger_entry(
            ledger_path,
            title="[Deferred] Some feature",
            filed=True,
            issue_number=7,
        )
        entries = read_ledger(ledger_path)
        assert entries[0]["filed"] is True


# ---------------------------------------------------------------------------
# 5. TestParseSkillName: _parse_skill_name() direct unit tests
# ---------------------------------------------------------------------------


class TestParseSkillName:
    """Test _parse_skill_name() handles all skill reference formats."""

    def test_bare_skill_name(self) -> None:
        """A bare skill name like 'war-room' is returned unchanged."""
        assert mod._parse_skill_name({"skill": "war-room"}) == "war-room"

    def test_plugin_qualified_name_strips_prefix(self) -> None:
        """'sanctum:war-room' strips the plugin prefix to return 'war-room'."""
        assert mod._parse_skill_name({"skill": "sanctum:war-room"}) == "war-room"

    def test_empty_skill_field(self) -> None:
        """Empty skill field returns empty string."""
        assert mod._parse_skill_name({"skill": ""}) == ""

    def test_missing_skill_key(self) -> None:
        """Missing 'skill' key returns empty string."""
        assert mod._parse_skill_name({}) == ""

    def test_multiple_colons_splits_on_first(self) -> None:
        """'a:b:c' splits on first colon; 'b:c' fails sanitization."""
        assert mod._parse_skill_name({"skill": "a:b:c"}) == "unknown"


# ---------------------------------------------------------------------------
# 6. TestMainOrchestration: main() entry point integration
# ---------------------------------------------------------------------------


class TestMainOrchestration:
    """Test main() wires detection, extraction, and ledger writes together."""

    def test_main_writes_ledger_when_deferral_detected(self, tmp_path: Path) -> None:
        """
        GIVEN a watched skill with deferral signals in output
        WHEN main() runs
        THEN entries are written to the session ledger
        """
        ledger_path = tmp_path / "deferred-items-session.json"
        tool_input = json.dumps({"skill": "war-room"})
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": tool_input,
            "CLAUDE_TOOL_OUTPUT": "[Deferred] Add OAuth support\nSome other text.",
        }
        with (
            patch.dict(os.environ, env),
            patch.object(mod, "get_ledger_path", return_value=ledger_path),
        ):
            mod.main()

        entries = json.loads(ledger_path.read_text())
        assert len(entries) == 1
        assert entries[0]["title"] == "Add OAuth support"
        assert entries[0]["source"] == "war-room"
        assert entries[0]["filed"] is False

    def test_main_skips_non_watched_skill(self, tmp_path: Path) -> None:
        """
        GIVEN a non-watched skill
        WHEN main() runs
        THEN no ledger file is created
        """
        ledger_path = tmp_path / "deferred-items-session.json"
        tool_input = json.dumps({"skill": "commit-messages"})
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": tool_input,
            "CLAUDE_TOOL_OUTPUT": "[Deferred] Some item",
        }
        with (
            patch.dict(os.environ, env),
            patch.object(mod, "get_ledger_path", return_value=ledger_path),
        ):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()
            assert exc_info.value.code == 0
        assert not ledger_path.exists()

    def test_main_skips_when_no_deferral_signal(self, tmp_path: Path) -> None:
        """
        GIVEN a watched skill with no deferral signals
        WHEN main() runs
        THEN no ledger file is created
        """
        ledger_path = tmp_path / "deferred-items-session.json"
        tool_input = json.dumps({"skill": "war-room"})
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": tool_input,
            "CLAUDE_TOOL_OUTPUT": "All items approved and completed.",
        }
        with (
            patch.dict(os.environ, env),
            patch.object(mod, "get_ledger_path", return_value=ledger_path),
        ):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()
            assert exc_info.value.code == 0
        assert not ledger_path.exists()

    def test_main_writes_multiple_deferred_items(self, tmp_path: Path) -> None:
        """
        GIVEN output with multiple [Deferred] markers
        WHEN main() runs
        THEN all items are written to the ledger
        """
        ledger_path = tmp_path / "deferred-items-session.json"
        tool_input = json.dumps({"skill": "brainstorm"})
        output = (
            "[Deferred] Add retry logic\n"
            "Normal text here.\n"
            "[Deferred] Improve error messages\n"
        )
        env = {
            "CLAUDE_TOOL_NAME": "Skill",
            "CLAUDE_TOOL_INPUT": tool_input,
            "CLAUDE_TOOL_OUTPUT": output,
        }
        with (
            patch.dict(os.environ, env),
            patch.object(mod, "get_ledger_path", return_value=ledger_path),
        ):
            mod.main()

        entries = json.loads(ledger_path.read_text())
        assert len(entries) == 2
        titles = {e["title"] for e in entries}
        assert "Add retry logic" in titles
        assert "Improve error messages" in titles


# Keep the module import accessible for any patching tests
__all__ = ["mod"]
