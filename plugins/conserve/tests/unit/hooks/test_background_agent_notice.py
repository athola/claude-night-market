# ruff: noqa: D101,D102,D103,D205,D212,E402,I001
"""Tests for background_agent_notice: the Notification hook.

``Notification`` fires when a background agent needs input or finishes
(Claude Code 2.1.218). Anthropic documents the registration shape but
not the fields it puts on stdin, so this hook records the payload
verbatim rather than reading names nobody published. These tests pin
that: an unknown key must survive into the log, because the log is how
the schema gets discovered.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[3] / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from background_agent_notice import build_entry, main


class TestBuildEntry:
    """Feature: the payload is recorded without interpreting it."""

    @pytest.mark.unit
    def test_preserves_every_key_of_an_unknown_payload(self) -> None:
        """The schema is undocumented, so nothing may be dropped."""
        payload = {"message": "agent finished", "wibble": 1, "nested": {"a": [1, 2]}}
        entry = build_entry(payload)
        assert entry["payload"] == payload

    @pytest.mark.unit
    def test_stamps_the_event_and_a_utc_timestamp(self) -> None:
        entry = build_entry({})
        assert entry["event"] == "Notification"
        assert entry["timestamp"].endswith("+00:00")

    @pytest.mark.unit
    def test_records_the_observed_keys_for_schema_discovery(self) -> None:
        """The point of the log is learning what the fields are."""
        entry = build_entry({"b": 1, "a": 2})
        assert entry["observed_keys"] == ["a", "b"]

    @pytest.mark.unit
    def test_a_non_dict_payload_is_still_recorded(self) -> None:
        """A list or string on stdin must not lose the observation."""
        entry = build_entry(["surprise"])
        assert entry["payload"] == ["surprise"]
        assert entry["observed_keys"] == []


class TestMain:
    """Feature: the hook never blocks the session."""

    @pytest.mark.unit
    @pytest.mark.parametrize("raw", ["", "   ", "not json", "{unclosed"])
    def test_exits_zero_on_unusable_stdin(self, raw: str, tmp_path: Path) -> None:
        with patch("sys.stdin", StringIO(raw)):
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
                with pytest.raises(SystemExit) as exc:
                    main()
        assert exc.value.code == 0

    @pytest.mark.unit
    def test_appends_one_jsonl_line_per_event(self, tmp_path: Path) -> None:
        for _ in range(2):
            with patch("sys.stdin", StringIO(json.dumps({"message": "hi"}))):
                with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
                    with pytest.raises(SystemExit):
                        main()
        log = tmp_path / ".claude" / "logs" / "notifications.jsonl"
        lines = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln]
        assert len(lines) == 2
        assert json.loads(lines[0])["payload"] == {"message": "hi"}

    @pytest.mark.unit
    def test_an_unwritable_log_does_not_fail_the_session(self, tmp_path: Path) -> None:
        """Observability must never be load-bearing."""
        blocker = tmp_path / ".claude"
        blocker.write_text("not a directory", encoding="utf-8")
        with patch("sys.stdin", StringIO(json.dumps({"message": "hi"}))):
            with patch.dict("os.environ", {"CLAUDE_PROJECT_DIR": str(tmp_path)}):
                with pytest.raises(SystemExit) as exc:
                    main()
        assert exc.value.code == 0
