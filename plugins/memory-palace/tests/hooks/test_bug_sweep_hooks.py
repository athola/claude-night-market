"""Regression tests for the bug-review sweep over the memory-palace hooks.

Each class pins one defect found by reading the hook code, with the input
shape that triggered it.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import recall  # noqa: E402 - import after sys.path setup
import research_queue  # noqa: E402 - import after sys.path setup
import session_lifecycle as lc  # noqa: E402 - import after sys.path setup
import url_detector  # noqa: E402 - import after sys.path setup

import shared.config as config_module  # noqa: E402 - import after sys.path setup
from memory_palace.session_history import (  # noqa: E402 - import after sys.path setup
    SessionHistoryManager,
    SessionQuery,
    SessionRecord,
)
from shared.deduplication import get_url_key  # noqa: E402 - import after sys.path setup
from shared.safety_checks import (  # noqa: E402 - import after sys.path setup
    check_data_bombs,
)


class TestRecallToleratesOddSessionRecords:
    """A bad file in sessions/ must not crash the prompt hook."""

    @pytest.mark.unit
    def test_session_record_that_is_a_json_list_is_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A sessions/ file holding `[]` is ignored and good.json still loads."""
        sessions = tmp_path / "sessions"
        sessions.mkdir()
        (sessions / "odd.json").write_text("[]")
        (sessions / "good.json").write_text(
            json.dumps(
                {
                    "handoff_units": [
                        {"thread": "cache", "type": "finding", "state": "ok"}
                    ]
                }
            )
        )
        monkeypatch.setattr(recall, "_sessions_dir", lambda: sessions)

        units = recall._load_units()

        assert [u["thread"] for u in units] == ["cache"]

    @pytest.mark.unit
    def test_unit_with_null_date_gets_neutral_weight(self) -> None:
        """A unit whose date is None weighs exactly 1.0."""
        unit = {"thread": "cache", "type": "finding", "date": None}

        assert recall._weight_for(unit) == 1.0


class TestSessionLifecycleKeepsHistory:
    """Stop fires every turn; later turns must not rewrite earlier facts."""

    @pytest.mark.unit
    def test_started_at_survives_a_second_stop(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two Stop events for one session_id keep the first started_at."""
        mgr = SessionHistoryManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: mgr)
        monkeypatch.setattr(lc, "_STAGING_PATH", tmp_path / "no-staging.json")
        payload = {
            "hook_event_name": "Stop",
            "session_id": "sess-keep-start",
            "stop_reason": "end_turn",
        }

        def run_stop() -> None:
            monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
            with pytest.raises(SystemExit):
                lc.main()

        run_stop()
        first = mgr.get_session("sess-keep-start")
        assert first is not None
        first_started = first.started_at

        run_stop()
        second = mgr.get_session("sess-keep-start")

        assert second is not None
        assert second.started_at == first_started

    @pytest.mark.unit
    def test_staged_units_survive_a_failed_record_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Units staged before a failed record write reach the next Stop."""
        staging = tmp_path / "handoff_units.json"
        staging.write_text(
            json.dumps(
                {
                    "units": [
                        {
                            "thread": "auth",
                            "type": "finding",
                            "date": "2026-10-07",
                            "state": "token refresh races",
                        }
                    ]
                }
            )
        )
        monkeypatch.setattr(lc, "_STAGING_PATH", staging)

        class _FailingManager(SessionHistoryManager):
            def record_session(self, record: SessionRecord) -> Path:
                raise OSError("disk full")

        failing = _FailingManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: failing)
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"hook_event_name": "Stop", "session_id": "s-1"})),
        )

        with pytest.raises(SystemExit):
            lc.main()

        working = SessionHistoryManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: working)
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"hook_event_name": "Stop", "session_id": "s-1"})),
        )
        with pytest.raises(SystemExit):
            lc.main()

        recorded = working.get_session("s-1")
        assert recorded is not None, "the second Stop did not record the session"
        assert [u.state for u in recorded.handoff_units] == ["token refresh races"], (
            "units were consumed before the record was saved"
        )

    @pytest.mark.unit
    def test_unit_staged_during_a_stop_is_kept_for_the_next_stop(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A unit written after the hook read the staging file is not deleted."""
        staging = tmp_path / "handoff_units.json"
        early = {"thread": "auth", "type": "finding", "date": "2026-10-07"}
        late = {"thread": "cache", "type": "finding", "date": "2026-10-07"}
        staging.write_text(json.dumps({"units": [dict(early, state="early")]}))
        monkeypatch.setattr(lc, "_STAGING_PATH", staging)
        mgr = SessionHistoryManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: mgr)
        original_read = lc._read_staged_units

        def read_then_writer_stages_more(path: Path) -> list[dict]:
            units = original_read(path)
            staging.write_text(json.dumps({"units": [dict(late, state="late")]}))
            return units

        monkeypatch.setattr(lc, "_read_staged_units", read_then_writer_stages_more)
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"hook_event_name": "Stop", "session_id": "s-2"})),
        )

        with pytest.raises(SystemExit):
            lc.main()

        recorded = mgr.get_session("s-2")
        assert recorded is not None
        assert [u.state for u in recorded.handoff_units] == ["early"]
        assert staging.exists(), "a unit staged during the Stop was deleted"
        assert json.loads(staging.read_text())["units"][0]["state"] == "late"


class TestStopClaimsOnlyItsOwnStagedUnits:
    """A Stop must not record a claim another session's Stop is holding."""

    @staticmethod
    def _write_claim(staging: Path, time_ns: int, pid: int, state: str) -> Path:
        claim = staging.with_name(f"{staging.name}.{time_ns}.{pid}.claim")
        claim.write_text(
            json.dumps(
                {
                    "units": [
                        {
                            "thread": "auth",
                            "type": "finding",
                            "date": "2026-10-07",
                            "state": state,
                        }
                    ]
                }
            )
        )
        return claim

    @staticmethod
    def _run_stop(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, staging: Path
    ) -> SessionHistoryManager:
        mgr = SessionHistoryManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: mgr)
        monkeypatch.setattr(lc, "_STAGING_PATH", staging)
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"hook_event_name": "Stop", "session_id": "s-3"})),
        )
        with pytest.raises(SystemExit):
            lc.main()
        return mgr

    @pytest.mark.unit
    def test_fresh_claim_from_another_live_pid_is_not_taken(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A claim a running Stop just made stays on disk, unrecorded."""
        staging = tmp_path / "handoff_units.json"
        claim = self._write_claim(
            staging, time.time_ns(), os.getppid(), "other session"
        )

        mgr = self._run_stop(tmp_path, monkeypatch, staging)

        recorded = mgr.get_session("s-3")
        assert recorded is not None
        assert recorded.handoff_units == []
        assert claim.exists(), "another session's claim was consumed"

    @pytest.mark.unit
    def test_claim_whose_pid_has_exited_is_recovered(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A claim left by a Stop process that died is recorded and removed."""
        exited = subprocess.Popen([sys.executable, "-c", "pass"])
        exited.wait()
        staging = tmp_path / "handoff_units.json"
        claim = self._write_claim(staging, time.time_ns(), exited.pid, "stranded")

        mgr = self._run_stop(tmp_path, monkeypatch, staging)

        recorded = mgr.get_session("s-3")
        assert recorded is not None
        assert [u.state for u in recorded.handoff_units] == ["stranded"]
        assert not claim.exists()

    @pytest.mark.unit
    def test_claim_older_than_the_threshold_is_recovered(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An hour-old claim is recovered even if its pid now names a live process."""
        staging = tmp_path / "handoff_units.json"
        an_hour_ago = time.time_ns() - 3600 * 10**9
        claim = self._write_claim(staging, an_hour_ago, os.getppid(), "old")

        mgr = self._run_stop(tmp_path, monkeypatch, staging)

        recorded = mgr.get_session("s-3")
        assert recorded is not None
        assert [u.state for u in recorded.handoff_units] == ["old"]
        assert not claim.exists()

    @pytest.mark.unit
    def test_claim_rename_failure_still_records_the_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A permission error moving the staging file aside costs the claim only."""
        staging = tmp_path / "handoff_units.json"
        staging.write_text(json.dumps({"units": []}))

        def deny_rename(src: object, dst: object) -> None:
            raise PermissionError("read-only state dir")

        monkeypatch.setattr(lc.os, "rename", deny_rename)
        mgr = self._run_stop(tmp_path, monkeypatch, staging)

        assert mgr.get_session("s-3") is not None

    @pytest.mark.unit
    def test_one_stop_reads_a_bounded_number_of_stale_claims_oldest_first(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Claims piling up after failed records are drained a batch per Stop."""
        staging = tmp_path / "handoff_units.json"
        an_hour_ago = time.time_ns() - 3600 * 10**9
        claims = [
            self._write_claim(staging, an_hour_ago + n, os.getppid(), f"old-{n}")
            for n in range(lc._MAX_CLAIMS_PER_STOP + 3)
        ]

        self._run_stop(tmp_path, monkeypatch, staging)

        remaining = [c for c in claims if c.exists()]
        assert remaining == claims[lc._MAX_CLAIMS_PER_STOP :]


class TestSessionQueryUntilIsInclusive:
    """``until`` is documented as an inclusive ISO date upper bound."""

    @pytest.mark.unit
    def test_date_only_until_includes_sessions_started_that_day(
        self, tmp_path: Path
    ) -> None:
        """until='2026-10-07' matches a session started at 10:00 UTC that day."""
        mgr = SessionHistoryManager(data_dir=tmp_path)
        mgr.record_session(
            SessionRecord(
                session_id="sess-day",
                started_at="2026-10-07T10:00:00+00:00",
            )
        )

        found = mgr.query_sessions(SessionQuery(until="2026-10-07"))

        assert [r.session_id for r in found] == ["sess-day"]


class TestUrlKeyNormalization:
    """Cosmetic URL variants must map to one key."""

    @pytest.mark.unit
    def test_leading_tracking_param_keeps_the_query_separator(self) -> None:
        """Dropping utm_source from `?utm_source=a&article=123` leaves `?article=123`."""
        key = get_url_key("https://example.com/p?utm_source=a&article=123")

        assert key == "https://example.com/p?article=123"

    @pytest.mark.unit
    def test_only_tracking_params_leave_no_dangling_separator(self) -> None:
        """A query made only of utm_* params loses the `?` as well."""
        key = get_url_key("https://example.com/p?utm_source=a&utm_medium=b")

        assert key == "https://example.com/p"

    @pytest.mark.unit
    def test_trailing_slash_before_fragment_is_dropped(self) -> None:
        """`/a/#top` and `/a` produce the same key."""
        assert get_url_key("https://example.com/a/#top") == get_url_key(
            "https://example.com/a"
        )


class TestPathExclusionGlobs:
    """Default exclude patterns written as globs must match real files."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "path",
        [
            "docs/credentials.json",
            "docs/secrets.yaml",
            "docs/pkg.egg-info/PKG-INFO",
        ],
    )
    def test_glob_patterns_exclude_matching_paths(
        self, path: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Defaults exclude credentials.json, secrets.yaml and egg-info contents."""
        monkeypatch.setattr(config_module, "_config_cache", None)
        monkeypatch.setattr(config_module, "_config_mtime", 0)
        monkeypatch.setattr(
            config_module,
            "get_config",
            lambda: config_module.CONFIG_DEFAULTS,
        )

        assert config_module.is_path_excluded(path)

    @pytest.mark.unit
    def test_glob_does_not_exclude_unrelated_paths(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """docs/guide.md stays included under the default exclude patterns."""
        monkeypatch.setattr(
            config_module,
            "get_config",
            lambda: config_module.CONFIG_DEFAULTS,
        )

        assert not config_module.is_path_excluded("docs/guide.md")


class TestUrlDetectorExtraction:
    """URLs pasted into prose carry punctuation that is not part of them."""

    @pytest.mark.unit
    def test_trailing_sentence_punctuation_is_not_part_of_the_url(self) -> None:
        """A comma or full stop after a URL in prose is stripped from it."""
        urls = url_detector.extract_urls(
            "Read https://example.com/guide, then https://example.org/x."
        )

        assert urls == ["https://example.com/guide", "https://example.org/x"]

    @pytest.mark.unit
    def test_skip_domain_matches_the_host_not_the_path(self) -> None:
        """A path segment containing 'localhost' does not drop the URL."""
        urls = url_detector.extract_urls(
            "see https://example.com/posts/localhost-setup"
        )

        assert urls == ["https://example.com/posts/localhost-setup"]

    @pytest.mark.unit
    def test_localhost_host_is_still_skipped(self) -> None:
        """http://localhost:8080/app is still dropped as a local address."""
        assert url_detector.extract_urls("run http://localhost:8080/app") == []


class TestUnicodeBombAtEndOfSample:
    """A run of combining marks is a bomb wherever it sits."""

    @pytest.mark.unit
    def test_trailing_combining_run_is_detected(self) -> None:
        """500 combining acute accents at the end of a sample fail the bomb check."""
        content = "plain text then" + "́" * 500

        result = check_data_bombs(content, {})

        assert result is not None
        assert not result.is_safe


class TestResearchQueueRedaction:
    """Redaction must catch the credential shapes users actually hold."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "secret",
        [
            "sk-ant-api03-" + "A1b2C3d4E5f6G7h8I9j0",
            "sk-proj-" + "A1b2C3d4E5f6G7h8I9j0",
        ],
    )
    def test_hyphenated_api_keys_are_redacted(self, secret: str) -> None:
        """sk-ant-api03- and sk-proj- keys are redacted along with their bodies."""
        text = f"research this with key {secret} please"

        redacted = research_queue.SECRET_PATTERN.sub("[redacted]", text)

        assert secret not in redacted
        assert "A1b2C3d4" not in redacted

    @pytest.mark.unit
    def test_ordinary_hyphenated_words_survive(self) -> None:
        """risk-assessment and longer hyphenated words pass SECRET_PATTERN unchanged."""
        text = "risk-assessment and task-driven-development-pipeline notes"

        assert research_queue.SECRET_PATTERN.sub("[redacted]", text) == text


class TestCaptureFilenamesAreUnique:
    """Two captures in the same second must not overwrite each other."""

    @pytest.mark.unit
    def test_same_title_same_second_keeps_both_captures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two 'Release Notes' captures under a frozen now() get separate files."""
        import web_research_handler as handler

        monkeypatch.setattr(handler, "QUEUE_DIR", tmp_path)
        monkeypatch.setattr(handler, "DATA_ROOT", tmp_path)
        monkeypatch.setattr(handler, "update_index", lambda **kwargs: None)

        class _FrozenDatetime(handler.datetime):  # type: ignore[name-defined, misc]  # handler is a hook script mypy cannot resolve
            @classmethod
            def now(cls, tz=None):  # type: ignore[no-untyped-def]  # mirrors datetime.now, which takes an optional tzinfo
                return cls(2026, 10, 7, 12, 0, 0, tzinfo=tz)

        monkeypatch.setattr(handler, "datetime", _FrozenDatetime)

        first = handler.store_webfetch_content(
            "# Release Notes\n\nfirst page body\n", "https://a.example/notes", ""
        )
        second = handler.store_webfetch_content(
            "# Release Notes\n\nsecond page body\n", "https://b.example/notes", ""
        )

        assert first is not None
        assert second is not None
        assert first != second
        assert "first page body" in Path(first).read_text(encoding="utf-8")


class TestCorruptStagedUnitsAreKept:
    """A staging file that does not parse is set aside, not deleted."""

    @staticmethod
    def _run_stop(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, staging: Path
    ) -> SessionHistoryManager:
        mgr = SessionHistoryManager(data_dir=tmp_path)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: mgr)
        monkeypatch.setattr(lc, "_STAGING_PATH", staging)
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"hook_event_name": "Stop", "session_id": "s-4"})),
        )
        with pytest.raises(SystemExit):
            lc.main()
        return mgr

    @pytest.mark.unit
    def test_unparsable_staging_file_is_moved_aside_with_a_warning(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A trailing comma keeps the text on disk as *.corrupt and logs its path."""
        state = tmp_path / "state"
        state.mkdir()
        staging = state / "handoff_units.json"
        broken = '{"units": [{"thread": "auth", "type": "finding", "state": "x"},]}'
        staging.write_text(broken)

        with caplog.at_level("WARNING", logger=lc.logger.name):
            mgr = self._run_stop(tmp_path, monkeypatch, staging)

        corrupt = list(state.glob("handoff_units.json.*.corrupt"))
        assert [p.read_text() for p in corrupt] == [broken]
        assert any(str(corrupt[0]) in r.getMessage() for r in caplog.records)
        assert mgr.get_session("s-4") is not None

    @pytest.mark.unit
    def test_unreadable_claim_stays_for_a_later_stop(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A claim whose read raises OSError is not discarded."""
        staging = tmp_path / "handoff_units.json"
        staging.write_text(json.dumps({"units": []}))
        real_read_text = Path.read_text

        def deny_claim_read(self: Path, *args: object, **kwargs: object) -> str:
            if self.name.endswith(".claim"):
                raise PermissionError("unreadable")
            return real_read_text(self, *args, **kwargs)  # type: ignore[arg-type]  # forwards the caller's own arguments

        monkeypatch.setattr(Path, "read_text", deny_claim_read)
        self._run_stop(tmp_path, monkeypatch, staging)

        assert len(list(tmp_path.glob("handoff_units.json.*.claim"))) == 1


class TestStopWithUnsafeSessionId:
    """A Stop payload whose session_id is a path writes nothing outside sessions/."""

    @pytest.mark.unit
    def test_traversal_session_id_records_nothing_and_keeps_staged_units(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """session_id '../x' is refused with a warning and the staging file survives."""
        data = tmp_path / "data"
        mgr = SessionHistoryManager(data_dir=data)
        monkeypatch.setattr(lc, "SessionHistoryManager", lambda *a, **kw: mgr)
        staging = tmp_path / "handoff_units.json"
        staging.write_text(json.dumps({"units": []}))
        monkeypatch.setattr(lc, "_STAGING_PATH", staging)
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"hook_event_name": "Stop", "session_id": "../x"})),
        )

        with (
            caplog.at_level("WARNING", logger=lc.logger.name),
            pytest.raises(SystemExit),
        ):
            lc.main()

        assert staging.exists()
        assert not (data / "x.json").exists()
        assert not (tmp_path / "x.json").exists()
        assert any("Invalid session" in r.getMessage() for r in caplog.records)
