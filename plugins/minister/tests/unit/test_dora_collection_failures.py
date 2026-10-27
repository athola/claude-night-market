"""Collector failures must surface as partial results, not tracebacks or silent truncation."""

from __future__ import annotations

import json
import subprocess as _sub
from datetime import datetime, timezone
from pathlib import Path

import pytest

from minister import dora_metrics

_WINDOW_END = datetime(2026, 5, 1, tzinfo=timezone.utc)


class TestGitCollectorFailure:
    """git can fail outside a repository, on a bad ref, or by hanging."""

    @pytest.mark.parametrize(
        "failure",
        [
            _sub.CalledProcessError(128, ["git", "log"], stderr="not a git repository"),
            _sub.TimeoutExpired(cmd="git", timeout=15),
            FileNotFoundError("git not found"),
        ],
        ids=["nonzero-exit", "timeout", "missing-binary"],
    )
    def test_git_failure_is_reported_as_partial(
        self, monkeypatch: pytest.MonkeyPatch, failure: Exception
    ) -> None:
        """Git failure is reported as partial, with the failure named."""

        def failing_run(*args: object, **kwargs: object) -> object:
            raise failure

        monkeypatch.setattr(_sub, "run", failing_run)

        result = dora_metrics.collect_deployments_from_git(
            branch="main", window_days=30, window_end=_WINDOW_END
        )

        assert result.events == []
        assert result.partial is True
        assert result.warnings == (
            f"git log failed: {type(failure).__name__}: {failure}",
        )

    def test_cli_strict_exits_two_when_git_fails(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Outside a repository the CLI must reach the --strict exit code."""
        monkeypatch.setattr(
            dora_metrics,
            "collect_failures_from_gh",
            lambda **kw: dora_metrics.CollectionResult(events=[]),
        )

        code = dora_metrics.run_cli(["--strict", "--repo-path", str(tmp_path)])

        assert code == 2


class TestGhResultLimit:
    """`gh issue list --limit 200` truncates without saying so."""

    def test_full_page_of_issues_is_reported_as_partial(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """200 rows, the gh --limit, set partial and an 'older failures dropped' warning."""
        rows = [
            {"createdAt": "2026-04-20T10:00:00Z", "closedAt": None, "state": "OPEN"}
        ] * 200

        class FakeRun:
            stdout = json.dumps(rows)

        monkeypatch.setattr(_sub, "run", lambda *a, **k: FakeRun())

        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30, window_end=_WINDOW_END
        )

        assert len(result.events) == 200
        assert result.partial is True
        assert any("older failures dropped" in w for w in result.warnings)

    def test_page_below_the_limit_is_complete(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One row short of the limit means nothing was cut off."""
        rows = [
            {"createdAt": "2026-04-20T10:00:00Z", "closedAt": None, "state": "OPEN"}
        ] * 199

        class FakeRun:
            stdout = json.dumps(rows)

        monkeypatch.setattr(_sub, "run", lambda *a, **k: FakeRun())

        result = dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30, window_end=_WINDOW_END
        )

        assert len(result.events) == 199
        assert result.partial is False
        assert result.warnings == ()


class TestGhRowParsing:
    """Rows gh returns are untrusted input: bad ones are skipped visibly."""

    def _collect(
        self, monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, object]]
    ) -> dora_metrics.CollectionResult:
        class FakeRun:
            stdout = json.dumps(rows)

        monkeypatch.setattr(_sub, "run", lambda *a, **k: FakeRun())
        return dora_metrics.collect_failures_from_gh(
            failure_label="bug", window_days=30, window_end=_WINDOW_END
        )

    def test_row_without_created_at_is_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A row with no open time cannot be placed in the window, so it is dropped."""
        result = self._collect(
            monkeypatch,
            [
                {"createdAt": None, "closedAt": None, "state": "OPEN"},
                {
                    "createdAt": "2026-04-20T10:00:00Z",
                    "closedAt": None,
                    "state": "OPEN",
                },
            ],
        )

        assert [e.opened_at.day for e in result.events] == [20]

    def test_malformed_timestamp_marks_partial_and_keeps_good_rows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unparseable closedAt skips that row and flags the result partial."""
        result = self._collect(
            monkeypatch,
            [
                {"createdAt": "2026-04-20T10:00:00Z", "closedAt": "yesterday"},
                {"createdAt": "2026-04-21T10:00:00Z", "closedAt": None},
            ],
        )

        assert [e.opened_at.day for e in result.events] == [21]
        assert result.partial is True
        assert any("malformed timestamp" in w for w in result.warnings)
