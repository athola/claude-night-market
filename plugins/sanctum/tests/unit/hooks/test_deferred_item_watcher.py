"""Unit tests for the deferred_item_watcher PostToolUse hook.

Tests cover: watch-list filtering, deferral detection regex,
title extraction, and ledger read/write operations.
"""
# ruff: noqa: D101,D102,D103,PLR2004,PLC0415,S603,S607

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
        """
        GIVEN CLAUDE_TOOL_NAME is set to 'Bash' (a non-Skill tool)
        WHEN should_process is called
        THEN the function returns False
        AND only tool invocations named exactly 'Skill' are processed
        """
        with patch.dict(
            os.environ, {"CLAUDE_TOOL_NAME": "Bash", "CLAUDE_TOOL_INPUT": "{}"}
        ):
            assert should_process() is False

    def test_skill_tool_name_required(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'skill' with lowercase initial letter
        WHEN should_process is called
        THEN the function returns False
        AND the tool name match is case-sensitive
        """
        with patch.dict(
            os.environ, {"CLAUDE_TOOL_NAME": "skill", "CLAUDE_TOOL_INPUT": "{}"}
        ):
            assert should_process() is False

    def test_unwatched_skill_is_ignored(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'commit-messages'
        WHEN should_process is called
        THEN the function returns False
        AND skills absent from WATCH_LIST are silently skipped
        """
        tool_input = json.dumps({"skill": "commit-messages"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is False

    def test_war_room_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'war-room'
        WHEN should_process is called
        THEN the function returns True
        AND 'war-room' is present in the WATCH_LIST set
        """
        tool_input = json.dumps({"skill": "war-room"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_brainstorm_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'brainstorm'
        WHEN should_process is called
        THEN the function returns True
        AND 'brainstorm' is present in the WATCH_LIST set
        """
        tool_input = json.dumps({"skill": "brainstorm"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_scope_guard_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'scope-guard'
        WHEN should_process is called
        THEN the function returns True
        AND 'scope-guard' is present in the WATCH_LIST set
        """
        tool_input = json.dumps({"skill": "scope-guard"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_feature_review_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'feature-review'
        WHEN should_process is called
        THEN the function returns True
        AND 'feature-review' is present in the WATCH_LIST set
        """
        tool_input = json.dumps({"skill": "feature-review"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_unified_review_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'unified-review'
        WHEN should_process is called
        THEN the function returns True
        AND 'unified-review' is present in the WATCH_LIST set
        """
        tool_input = json.dumps({"skill": "unified-review"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_rollback_reviewer_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'rollback-reviewer'
        WHEN should_process is called
        THEN the function returns True
        AND 'rollback-reviewer' is present in the WATCH_LIST set
        """
        tool_input = json.dumps({"skill": "rollback-reviewer"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_watch_list_contains_exactly_six_skills(self) -> None:
        """
        GIVEN the WATCH_LIST constant exported from the module
        WHEN its value is compared to the expected set of six skills
        THEN the sets are equal
        AND each of the six canonical skills is individually present
        """
        assert WATCH_LIST == {
            "war-room",
            "brainstorm",
            "scope-guard",
            "feature-review",
            "unified-review",
            "rollback-reviewer",
        }

    def test_plugin_qualified_skill_name_is_watched(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' and skill is 'sanctum:war-room'
        WHEN should_process is called
        THEN the function returns True
        AND the plugin prefix is stripped before WATCH_LIST lookup
        """
        tool_input = json.dumps({"skill": "sanctum:war-room"})
        with patch.dict(
            os.environ,
            {"CLAUDE_TOOL_NAME": "Skill", "CLAUDE_TOOL_INPUT": tool_input},
        ):
            assert should_process() is True

    def test_missing_tool_input_does_not_crash(self) -> None:
        """
        GIVEN CLAUDE_TOOL_NAME is 'Skill' but CLAUDE_TOOL_INPUT is absent
        WHEN should_process is called
        THEN the function returns False without raising an exception
        AND missing environment variables are handled gracefully
        """
        with patch.dict(os.environ, {"CLAUDE_TOOL_NAME": "Skill"}, clear=False):
            os.environ.pop("CLAUDE_TOOL_INPUT", None)
            processed = should_process()
        assert processed is False


# ---------------------------------------------------------------------------
# 2. TestDeferralDetection: scan_for_deferrals() regex coverage
# ---------------------------------------------------------------------------


class TestDeferralDetection:
    """Test that scan_for_deferrals() correctly identifies deferral signals."""

    def test_deferred_marker_triggers(self) -> None:
        """
        GIVEN text containing the '[Deferred]' bracketed marker
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND the bracketed-marker form is a recognized deferral pattern
        """
        assert scan_for_deferrals("[Deferred] Add OAuth support") is True

    def test_out_of_scope_triggers(self) -> None:
        """
        GIVEN text containing the phrase 'out of scope'
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND phrase-based signals are recognized alongside bracket markers
        """
        assert (
            scan_for_deferrals("This feature is out of scope for this cycle.") is True
        )

    def test_not_yet_applicable_triggers(self) -> None:
        """
        GIVEN text containing the phrase 'not yet applicable'
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND multi-word deferral phrases are covered by the regex
        """
        assert scan_for_deferrals("This change is not yet applicable.") is True

    def test_future_cycle_triggers(self) -> None:
        """
        GIVEN text containing the phrase 'future cycle'
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND forward-planning phrases are recognized as deferrals
        """
        assert scan_for_deferrals("Address this in a future cycle.") is True

    def test_rejected_word_boundary_triggers(self) -> None:
        """
        GIVEN text with 'rejected' appearing at a word boundary
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND word-boundary anchoring allows 'rejected' to trigger
        """
        assert scan_for_deferrals("This proposal was rejected by the team.") is True

    def test_deferred_word_boundary_triggers(self) -> None:
        """
        GIVEN text with 'deferred' appearing at a word boundary
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND the standalone word 'deferred' is a recognized signal
        """
        assert scan_for_deferrals("The task was deferred to next sprint.") is True

    def test_case_insensitive_out_of_scope(self) -> None:
        """
        GIVEN text with 'OUT OF SCOPE' in uppercase
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND pattern matching is case-insensitive for phrase signals
        """
        assert scan_for_deferrals("OUT OF SCOPE for now.") is True

    def test_case_insensitive_deferred(self) -> None:
        """
        GIVEN text with 'DEFERRED' in uppercase
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND pattern matching is case-insensitive for the deferred keyword
        """
        assert scan_for_deferrals("Status: DEFERRED") is True

    def test_rejected_not_triggered_mid_word(self) -> None:
        """
        GIVEN text with 'rejected' embedded inside the word 'unrejected'
        WHEN scan_for_deferrals is called with that text
        THEN the function returns False
        AND word-boundary anchoring prevents mid-word matches
        """
        assert scan_for_deferrals("The change was unrejected after review.") is False

    def test_deferred_not_triggered_mid_word(self) -> None:
        """
        GIVEN text with 'deferred' embedded inside 'nondeferred'
        WHEN scan_for_deferrals is called with that text
        THEN the function returns False
        AND word-boundary rules prevent 'deferred' matching mid-word
        """
        assert scan_for_deferrals("The nondeferred item was completed.") is False

    def test_normal_completion_text_does_not_trigger(self) -> None:
        """
        GIVEN text describing successful task completion with no deferral terms
        WHEN scan_for_deferrals is called with that text
        THEN the function returns False
        AND normal completion output does not produce false positives
        """
        assert (
            scan_for_deferrals("Task completed successfully. All tests pass.") is False
        )

    def test_empty_string_does_not_trigger(self) -> None:
        """
        GIVEN an empty string as input
        WHEN scan_for_deferrals is called with that text
        THEN the function returns False
        AND empty input is handled without raising an exception
        """
        assert scan_for_deferrals("") is False

    def test_multiline_text_with_signal_triggers(self) -> None:
        """
        GIVEN multiline text with a deferral signal on one of its lines
        WHEN scan_for_deferrals is called with that text
        THEN the function returns True
        AND the signal is detected regardless of its line position
        """
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
        """
        GIVEN text with exactly one '[Deferred]' marker
        WHEN extract_deferred_titles is called with that text
        THEN a list containing one title string is returned
        AND the title text excludes the marker prefix
        """
        titles = extract_deferred_titles("[Deferred] Add OAuth support")
        assert titles == ["Add OAuth support"]

    def test_extracts_multiple_markers(self) -> None:
        """
        GIVEN text with two '[Deferred]' markers on separate lines
        WHEN extract_deferred_titles is called with that text
        THEN a list of two title strings is returned
        AND each marker's title text is present in the result list
        """
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
        """
        GIVEN text with a deferral signal but no '[Deferred]' marker
        WHEN extract_deferred_titles is called with that text
        THEN the fallback title list is returned
        AND the fallback title is 'Untitled deferred item'
        """
        titles = extract_deferred_titles(
            "This feature is out of scope for this release."
        )
        assert titles == ["Untitled deferred item"]

    def test_empty_text_returns_fallback(self) -> None:
        """
        GIVEN text containing only a deferral signal with no explicit marker
        WHEN extract_deferred_titles is called with that text
        THEN the fallback title list is returned
        AND the fallback value is 'Untitled deferred item'
        """
        titles = extract_deferred_titles("out of scope")
        assert titles == ["Untitled deferred item"]

    def test_strips_leading_whitespace_from_title(self) -> None:
        """
        GIVEN a '[Deferred]' marker followed by padded whitespace and text
        WHEN extract_deferred_titles is called with that text
        THEN the extracted title has leading and trailing whitespace stripped
        AND the result is ['Trim me'] with no surrounding spaces
        """
        titles = extract_deferred_titles("[Deferred]   Trim me   ")
        assert titles == ["Trim me"]

    def test_marker_at_end_of_line_yields_nonempty_title(self) -> None:
        """
        GIVEN a '[Deferred]' marker with only whitespace after it
        WHEN extract_deferred_titles is called with that text
        THEN 'Untitled deferred item' is included in the result list
        AND an empty or whitespace-only title falls back to the sentinel
        """
        titles = extract_deferred_titles("[Deferred]   \n")
        assert "Untitled deferred item" in titles

    def test_prefix_stripped_from_title(self) -> None:
        """
        GIVEN a '[Deferred]' marker followed by a title string
        WHEN extract_deferred_titles is called with that text
        THEN none of the returned titles contain the '[Deferred]' prefix
        AND the bracket notation is removed from every extracted title
        """
        titles = extract_deferred_titles("[Deferred] Some feature")
        assert all("[Deferred]" not in t for t in titles)


# ---------------------------------------------------------------------------
# 4. TestLedger: read/write/update operations
# ---------------------------------------------------------------------------


class TestLedger:
    """Test ledger file operations for deferred item persistence."""

    def test_write_and_read_roundtrip(self, tmp_path: Path) -> None:
        """
        GIVEN a ledger entry with title, source, and filed fields
        WHEN write_ledger_entry then read_ledger are called in sequence
        THEN the read result contains exactly one entry
        AND the entry fields match the original written values
        """
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
        """
        GIVEN a ledger path with no prior entries
        WHEN write_ledger_entry is called three times with distinct entries
        THEN read_ledger returns all three entries
        AND the ledger file accumulates entries without overwriting
        """
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
        """
        GIVEN a ledger file path that does not exist on disk
        WHEN read_ledger is called with that path
        THEN an empty list is returned
        AND no exception is raised for a missing ledger file
        """
        ledger_path = tmp_path / "no-such-file.json"
        assert read_ledger(ledger_path) == []

    def test_read_corrupt_ledger_returns_empty_list(self, tmp_path: Path) -> None:
        """
        GIVEN a ledger file containing invalid JSON content
        WHEN read_ledger is called with that path
        THEN an empty list is returned
        AND corrupt JSON is handled gracefully without raising an exception
        """
        ledger_path = tmp_path / "corrupt.json"
        ledger_path.write_text("{corrupt json!!!")
        assert read_ledger(ledger_path) == []

    def test_update_ledger_entry_sets_filed(self, tmp_path: Path) -> None:
        """
        GIVEN a ledger entry with filed=False written to disk
        WHEN update_ledger_entry is called with filed=True and issue_number
        THEN the matching entry has its filed field set to True
        AND the issue_number field is also recorded on the entry
        """
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
        """
        GIVEN a ledger with one entry titled 'Existing item'
        WHEN update_ledger_entry is called with a non-matching title
        THEN the existing entry is not modified
        AND the filed field of the original entry remains False
        """
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
        """
        GIVEN a ledger entry with a title prefixed by '[Deferred] '
        WHEN write_ledger_entry is called with that entry
        THEN the stored title has the prefix stripped
        AND read_ledger returns 'Some feature' without the bracket prefix
        """
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
        """
        GIVEN a ledger entry stored with the normalized title 'Some feature'
        WHEN update_ledger_entry is called with '[Deferred] Some feature'
        THEN the entry is matched and its filed field is set to True
        AND the prefix is stripped from the update title before matching
        """
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
        # Update using prefixed variant: should still match after normalization
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
        """
        GIVEN a skill payload with the bare skill name 'war-room'
        WHEN _parse_skill_name is called with that payload
        THEN the skill name is returned unchanged
        AND no prefix stripping occurs when there is no colon separator
        """
        assert mod._parse_skill_name({"skill": "war-room"}) == "war-room"

    def test_plugin_qualified_name_strips_prefix(self) -> None:
        """
        GIVEN a skill payload with 'sanctum:war-room' as the skill value
        WHEN _parse_skill_name is called with that payload
        THEN the plugin prefix 'sanctum:' is stripped from the result
        AND the returned value is the bare skill name 'war-room'
        """
        assert mod._parse_skill_name({"skill": "sanctum:war-room"}) == "war-room"

    def test_empty_skill_field(self) -> None:
        """
        GIVEN a skill payload with an empty string as the skill value
        WHEN _parse_skill_name is called with that payload
        THEN an empty string is returned
        AND no error is raised for an empty skill field
        """
        assert mod._parse_skill_name({"skill": ""}) == ""

    def test_missing_skill_key(self) -> None:
        """
        GIVEN a skill payload with no 'skill' key present
        WHEN _parse_skill_name is called with that payload
        THEN an empty string is returned
        AND missing keys are handled without raising a KeyError
        """
        assert mod._parse_skill_name({}) == ""

    def test_multiple_colons_splits_on_first(self) -> None:
        """
        GIVEN a skill payload with 'a:b:c' containing multiple colons
        WHEN _parse_skill_name is called with that payload
        THEN the function returns 'unknown' due to sanitization failure
        AND the split occurs on the first colon only
        """
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
        AND the entry records the skill name as source with filed=False
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
        AND main() exits with code 0 indicating a clean skip
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
        AND main() exits with code 0 indicating a clean skip
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
        AND each marker title appears as a separate ledger entry
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


# ---------------------------------------------------------------------------
# 7. TestResponseText: _response_text() dict-to-JSON branch
# ---------------------------------------------------------------------------


class TestResponseText:
    """Test _response_text() serialises dict tool_response to JSON."""

    def test_str_response_returned_unchanged(self) -> None:
        """String tool_response is returned as-is.

        GIVEN a payload with a string tool_response
        WHEN _response_text is called
        THEN the exact string is returned
        AND no serialization or transformation is applied
        """
        assert mod._response_text({"tool_response": "plain text"}) == "plain text"

    def test_dict_response_serialized_to_json_string(self) -> None:
        """Dict tool_response is JSON-encoded.

        GIVEN a payload where tool_response is a dict
        WHEN _response_text is called
        THEN the dict is returned as a JSON string
        AND the result is the compact JSON encoding of the dict
        """
        encoded = mod._response_text({"tool_response": {"key": "value"}})
        assert encoded == '{"key": "value"}'

    def test_missing_response_returns_empty_string(self) -> None:
        """Absent tool_response key defaults to empty string.

        GIVEN a payload with no tool_response key
        WHEN _response_text is called
        THEN an empty string is returned
        AND no KeyError is raised for the missing key
        """
        assert mod._response_text({}) == ""


# ---------------------------------------------------------------------------
# 8. TestReadLedgerNonListJson: read_ledger with non-list root value
# ---------------------------------------------------------------------------


class TestReadLedgerNonListJson:
    """Test read_ledger returns [] when the JSON root is not a list."""

    def test_dict_root_returns_empty_list(self, tmp_path: Path) -> None:
        """read_ledger returns [] when the ledger root is a JSON object.

        GIVEN a ledger file whose root value is a JSON dict
        WHEN read_ledger is called
        THEN an empty list is returned
        AND non-list JSON roots are treated as invalid ledger data
        """
        ledger_path = tmp_path / "dict-root.json"
        ledger_path.write_text('{"key": "value"}', encoding="utf-8")
        assert read_ledger(ledger_path) == []


# ---------------------------------------------------------------------------
# 9. TestShouldProcessNonDictToolInput: non-dict tool_input guard
# ---------------------------------------------------------------------------


class TestShouldProcessNonDictToolInput:
    """Test should_process() rejects payloads with non-dict tool_input."""

    def test_list_tool_input_returns_false(self) -> None:
        """should_process returns False when tool_input is a list.

        GIVEN a payload with tool_name=Skill but tool_input as a list
        WHEN should_process is called with that payload
        THEN False is returned
        AND non-dict tool_input is rejected regardless of tool_name
        """
        payload = {"tool_name": "Skill", "tool_input": ["not", "a", "dict"]}
        assert should_process(payload) is False


# Keep the module import accessible for any patching tests
__all__ = ["mod"]
