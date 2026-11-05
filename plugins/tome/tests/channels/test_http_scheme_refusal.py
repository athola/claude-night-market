"""Only https is fetched, and a refusal is a result, not an exception.

The opener has an https handler and nothing else, so urllib returned None
for any other scheme and the caller died on ``AttributeError``. That
included an https server redirecting to http.
"""

from __future__ import annotations

import email.message
import io
import urllib.request
import urllib.response
from pathlib import Path

import pytest

from tome.channels import fetch as fetch_cli
from tome.channels import http


@pytest.mark.unit
@pytest.mark.parametrize(
    "url", ["http://example.com/", "ftp://example.com/x", "data:text/plain,hi"]
)
def test_non_https_url_is_refused_without_raising(url: str) -> None:
    reply = http.urllib_transport(url, {})

    assert reply.status == http.REFUSED
    assert "https" in reply.error


@pytest.mark.unit
def test_file_url_is_refused_and_reads_nothing(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("do-not-read")

    reply = http.urllib_transport(secret.as_uri(), {})

    assert reply.status == http.REFUSED
    assert "do-not-read" not in reply.body


@pytest.mark.unit
def test_a_refused_url_is_not_retried() -> None:
    waits: list[float] = []

    reply = http.fetch("http://example.com/", sleep=waits.append)

    assert reply.status == http.REFUSED
    assert reply.attempts == 1
    assert waits == []


class _RedirectToHttp(urllib.request.HTTPSHandler):
    def __init__(self) -> None:
        super().__init__()
        self.seen: list[str] = []

    def https_open(self, req: urllib.request.Request) -> urllib.response.addinfourl:
        self.seen.append(req.full_url)
        headers = email.message.Message()
        headers["Location"] = "http://example.org/plain"
        reply = urllib.response.addinfourl(io.BytesIO(b""), headers, req.full_url, 302)
        reply.msg = "Found"
        return reply


@pytest.mark.unit
def test_redirect_from_https_to_http_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _RedirectToHttp()
    monkeypatch.setattr(http.urllib.request, "HTTPSHandler", lambda: fake)

    reply = http.urllib_transport("https://api.example.com/x", {"x-api-key": "k"})

    assert reply.status == http.REFUSED
    assert fake.seen == ["https://api.example.com/x"]


@pytest.mark.unit
def test_response_headers_cannot_be_changed_after_construction() -> None:
    reply = http.Response(200, "", {"a": "b"})

    with pytest.raises(TypeError):
        reply.headers["a"] = "c"  # type: ignore[index] - a write to a read-only mapping is the point


@pytest.mark.unit
@pytest.mark.parametrize(
    ("status", "error"),
    [(http.NO_RESPONSE, ""), (http.REFUSED, ""), (200, "boom"), (429, "boom")],
)
def test_error_text_is_present_exactly_when_no_response_came_back(
    status: int, error: str
) -> None:
    with pytest.raises(ValueError, match="error"):
        http.Response(status, "", {}, error=error)


@pytest.mark.unit
def test_fetch_does_not_wait_past_its_deadline() -> None:
    waits: list[float] = []

    reply = http.fetch(
        "https://x",
        transport=lambda u, h: http.Response(429, "", {"Retry-After": "20"}),
        sleep=waits.append,
        deadline=10.0,
        clock=lambda: 0.0,
    )

    assert reply.status == 429
    assert reply.attempts == 1
    assert waits == []


@pytest.mark.unit
def test_search_academic_reports_sources_skipped_when_the_budget_runs_out() -> None:
    now = [0.0]

    def slow_fetch(url: str, **kwargs: object) -> http.Response:
        assert kwargs["deadline"] == 75.0
        now[0] += 50.0
        return http.Response(200, '{"data": [], "results": []}', {})

    report = fetch_cli.search_academic(
        "x", fetch=slow_fetch, budget_seconds=75.0, clock=lambda: now[0]
    )

    skipped = [e for e in report["errors"] if "budget" in e["message"]]
    assert [e["source"] for e in skipped] == ["openalex"]
    assert [q["source"] for q in report["queries"]] == [
        "arxiv",
        "semantic_scholar",
        "openalex",
    ]


@pytest.mark.unit
def test_default_budget_leaves_room_under_the_bash_timeout() -> None:
    """One in-flight request can outlast the budget by its own timeout."""
    assert fetch_cli.BUDGET_SECONDS + 30.0 <= 120.0


@pytest.mark.unit
def test_search_reddit_stops_at_the_budget_and_names_the_skipped_subreddits() -> None:
    now = [0.0]

    def slow_fetch(url: str, **kwargs: object) -> http.Response:
        now[0] += 50.0
        return http.Response(200, "", {})

    report = fetch_cli.search_reddit(
        "x",
        ["a", "b", "c"],
        fetch=slow_fetch,
        sleep=lambda s: None,
        budget_seconds=75.0,
        clock=lambda: now[0],
    )

    skipped = [e["message"] for e in report["errors"] if "budget" in e["message"]]
    assert skipped == ["r/c: skipped, time budget spent"]


@pytest.mark.unit
def test_search_reddit_does_not_sleep_for_subreddits_the_budget_skips() -> None:
    """Spacing belongs between requests, never before a skipped subreddit.

    Sleeping first made 45 subreddits cost 88s of spacing after the budget
    was gone, past the 120s Bash cap the budget exists to stay under.
    """
    now = [0.0]
    fetched: list[str] = []
    waits: list[float] = []

    def slow_fetch(url: str, **kwargs: object) -> http.Response:
        fetched.append(url)
        now[0] += 50.0
        return http.Response(200, "", {})

    def sleep(seconds: float) -> None:
        waits.append(seconds)
        now[0] += seconds

    fetch_cli.search_reddit(
        "x",
        [f"s{i}" for i in range(45)],
        fetch=slow_fetch,
        sleep=sleep,
        budget_seconds=75.0,
        clock=lambda: now[0],
    )

    assert len(fetched) == 2
    assert len(waits) == len(fetched) - 1
    assert now[0] < 120.0


@pytest.mark.unit
def test_find_full_text_stops_at_the_budget() -> None:
    now = [0.0]

    def slow_fetch(url: str, **kwargs: object) -> http.Response:
        now[0] += 80.0
        return http.Response(404, "", {})

    report = fetch_cli.find_full_text(
        doi="10.1/x",
        title="t",
        fetch=slow_fetch,
        budget_seconds=75.0,
        clock=lambda: now[0],
    )

    assert len([t for t in report["tried"] if t["status"] == 404]) == 1
    assert any("budget" in str(t["status"]) for t in report["tried"])
