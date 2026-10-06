"""Channels keep reporting when a source rate-limits or blocks (coverage gaps).

A 2026-10-05 research run lost its whole academic channel to HTTP 429 from
arXiv and Semantic Scholar. Reddit was unreachable because reddit.com
refuses WebFetch and its JSON API returns a block page. The anchor paper's
full text stopped at an ACM 403. Live probes the same day: OpenAlex
answered while arXiv and Semantic Scholar returned 429, Reddit's
search.rss answered while its JSON API returned 403, and OpenAlex reports
open-access locations by DOI.

Every test here runs against a fake transport. None touches the network.
"""

from __future__ import annotations

import json
from collections.abc import Callable

import pytest

from tome.channels import academic, discourse, http
from tome.channels import fetch as fetch_cli

Transport = Callable[[str, dict], http.Response]


def _scripted(*responses: http.Response) -> tuple[Transport, list[str]]:
    """A transport that answers with `responses` in order and logs URLs."""
    calls: list[str] = []
    queue = list(responses)

    def transport(url: str, headers: dict) -> http.Response:
        calls.append(url)
        return queue.pop(0)

    return transport, calls


def _ok(body: str) -> http.Response:
    return http.Response(200, body, {})


def _routed(routes: dict[str, http.Response]) -> tuple[Transport, list[tuple]]:
    """A transport keyed on a URL substring; records (url, headers)."""
    seen: list[tuple] = []

    def transport(url: str, headers: dict) -> http.Response:
        seen.append((url, dict(headers)))
        for needle, response in routes.items():
            if needle in url:
                return response
        return http.Response(404, "", {})

    return transport, seen


# --- http.fetch -----------------------------------------------------------


def test_a_429_is_retried_after_the_server_named_delay() -> None:
    transport, calls = _scripted(
        http.Response(429, "slow down", {"Retry-After": "7"}), _ok("done")
    )
    waits: list[float] = []
    result = http.fetch("https://x", transport=transport, sleep=waits.append)
    assert result.status == 200
    assert result.attempts == 2
    assert waits == [7.0]
    assert len(calls) == 2


def test_retry_after_is_capped() -> None:
    transport, _ = _scripted(
        http.Response(429, "", {"retry-after": "3600"}), _ok("done")
    )
    waits: list[float] = []
    http.fetch("https://x", transport=transport, sleep=waits.append)
    assert waits == [http.MAX_WAIT]


def test_without_retry_after_the_backoff_grows() -> None:
    transport, _ = _scripted(
        http.Response(503, "", {}), http.Response(429, "", {}), _ok("done")
    )
    waits: list[float] = []
    http.fetch("https://x", transport=transport, sleep=waits.append)
    assert waits[1] > waits[0] > 0


def test_it_gives_up_and_reports_the_last_status() -> None:
    transport, calls = _scripted(*[http.Response(429, "", {})] * 4)
    result = http.fetch(
        "https://x", transport=transport, sleep=lambda s: None, retries=3
    )
    assert result.status == 429
    assert result.attempts == 4
    assert len(calls) == 4


def test_a_403_is_not_retried() -> None:
    transport, calls = _scripted(http.Response(403, "blocked", {}))
    result = http.fetch("https://x", transport=transport, sleep=lambda s: None)
    assert result.status == 403
    assert len(calls) == 1


def test_the_user_agent_names_the_contact(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOME_CONTACT_EMAIL", "me@example.org")
    transport, seen = _routed({"x": _ok("")})
    http.fetch("https://x", transport=transport, sleep=lambda s: None)
    assert "me@example.org" in seen[0][1]["User-Agent"]


# --- academic search ------------------------------------------------------

OPENALEX = {
    "results": [
        {
            "id": "https://openalex.org/W1",
            "doi": "https://doi.org/10.1145/1",
            "display_name": "Multi-hop HaLow throughput",
            "publication_year": 2025,
            "cited_by_count": 120,
            "open_access": {"is_oa": True, "oa_url": "https://arxiv.org/pdf/2605.1"},
            "abstract_inverted_index": {"We": [0], "measure": [1], "throughput": [2]},
        }
    ]
}


def test_openalex_results_become_findings() -> None:
    [finding] = academic.parse_openalex_response(OPENALEX)
    assert finding.title == "Multi-hop HaLow throughput"
    assert finding.channel == "academic"
    assert finding.url == "https://doi.org/10.1145/1"
    assert finding.metadata["oa_url"] == "https://arxiv.org/pdf/2605.1"
    assert finding.summary == "We measure throughput"


def test_rate_limited_sources_do_not_empty_the_channel() -> None:
    limited = http.Response(429, "Rate exceeded.", {})
    transport, _ = _routed(
        {
            "export.arxiv.org": limited,
            "api.semanticscholar.org": limited,
            "api.openalex.org": _ok(json.dumps(OPENALEX)),
        }
    )
    report = fetch_cli.search_academic(
        "halow mesh",
        fetch=lambda u, **kw: http.fetch(
            u, transport=transport, sleep=lambda s: None, **kw
        ),
    )
    assert [f["title"] for f in report["findings"]] == ["Multi-hop HaLow throughput"]
    errors = {(e["source"], e["kind"]) for e in report["errors"]}
    assert errors == {("arxiv", "rate_limit"), ("semantic_scholar", "rate_limit")}
    counts = {q["source"]: q["result_count"] for q in report["queries"]}
    assert counts == {"arxiv": 0, "semantic_scholar": 0, "openalex": 1}


def test_a_semantic_scholar_key_is_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEMANTIC_SCHOLAR_API_KEY", "k123")
    transport, seen = _routed({"semanticscholar": _ok('{"data": []}')})
    fetch_cli.search_academic(
        "x",
        fetch=lambda u, **kw: http.fetch(
            u, transport=transport, sleep=lambda s: None, **kw
        ),
    )
    s2 = [h for u, h in seen if "semanticscholar" in u]
    assert s2 and s2[0].get("x-api-key") == "k123"


# --- full text ------------------------------------------------------------


def test_full_text_prefers_a_repository_copy_over_the_publisher() -> None:
    work = {
        "locations": [
            {
                "pdf_url": "https://dl.acm.org/doi/pdf/10.1/x",
                "source": {"type": "journal"},
            },
            {
                "pdf_url": "https://repo.example.edu/x.pdf",
                "source": {"type": "repository"},
            },
        ]
    }
    transport, _ = _routed({"api.openalex.org/works/doi:": _ok(json.dumps(work))})
    found = fetch_cli.find_full_text(
        doi="10.1/x",
        fetch=lambda u, **kw: http.fetch(
            u, transport=transport, sleep=lambda s: None, **kw
        ),
    )
    assert found["candidates"][0]["url"] == "https://repo.example.edu/x.pdf"
    assert found["candidates"][1]["url"] == "https://dl.acm.org/doi/pdf/10.1/x"


def test_full_text_tries_every_source_and_says_which() -> None:
    arxiv_hit = (
        "<feed><entry><id>http://arxiv.org/abs/2605.17349v1</id>"
        "<title>Enabling Concurrency</title>"
        '<link title="pdf" href="http://arxiv.org/pdf/2605.17349v1"/></entry></feed>'
    )
    transport, _ = _routed(
        {
            "api.openalex.org/works/doi:": _ok(json.dumps({"locations": []})),
            "export.arxiv.org": _ok(arxiv_hit),
            "api.semanticscholar.org": http.Response(429, "", {}),
        }
    )
    found = fetch_cli.find_full_text(
        doi="10.1/x",
        title="Enabling Concurrency",
        fetch=lambda u, **kw: http.fetch(
            u, transport=transport, sleep=lambda s: None, **kw
        ),
    )
    assert [c["url"] for c in found["candidates"]] == [
        "http://arxiv.org/pdf/2605.17349v1"
    ]
    tried = {t["source"]: t["status"] for t in found["tried"]}
    assert tried["openalex"] == 200
    assert tried["arxiv"] == 200
    assert tried["semantic_scholar"] == 429
    assert tried["unpaywall"] == "skipped: TOME_CONTACT_EMAIL unset"


# --- reddit ---------------------------------------------------------------

REDDIT_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Meshtastic file transfer is slow</title>
<link href="https://www.reddit.com/r/amateurradio/comments/abc/meshtastic/"/>
<content type="html">&lt;p&gt;LongFast tops out near 1 kbit/s.&lt;/p&gt;</content>
<updated>2026-09-01T00:00:00+00:00</updated></entry>
</feed>"""


def test_reddit_search_uses_the_rss_feed() -> None:
    url = discourse.build_reddit_rss_search_url("meshtastic speed", "amateurradio")
    assert url.startswith("https://www.reddit.com/r/amateurradio/search.rss?")
    assert "restrict_sr=1" in url


def test_reddit_rss_entries_become_findings() -> None:
    [finding] = discourse.parse_reddit_rss(REDDIT_RSS, "amateurradio")
    assert finding.title == "Meshtastic file transfer is slow"
    assert finding.url.endswith("/comments/abc/meshtastic/")
    assert finding.summary == "LongFast tops out near 1 kbit/s."
    assert finding.metadata["subreddit"] == "amateurradio"


def test_reddit_calls_are_spaced_and_rate_limits_recorded() -> None:
    transport, _ = _scripted(_ok(REDDIT_RSS), http.Response(403, "blocked", {}))
    waits: list[float] = []
    report = fetch_cli.search_reddit(
        "meshtastic",
        ["amateurradio", "meshtastic"],
        fetch=lambda u, **kw: http.fetch(
            u, transport=transport, sleep=lambda s: None, **kw
        ),
        sleep=waits.append,
    )
    assert waits == [fetch_cli.REDDIT_SPACING_SECONDS]
    assert len(report["findings"]) == 1
    assert report["errors"] == [
        {
            "kind": "source_error",
            "source": "reddit",
            "message": "r/meshtastic: HTTP 403",
        }
    ]


# --- CLI ------------------------------------------------------------------


def test_cli_prints_the_channel_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        fetch_cli,
        "_SEARCHES",
        {
            "academic": lambda args: {
                "channel": "academic",
                "findings": [],
                "errors": [],
            }
        },
    )
    assert fetch_cli.main(["academic", "halow mesh"]) == 0
    assert json.loads(capsys.readouterr().out)["channel"] == "academic"


def test_a_network_failure_is_retried() -> None:
    """arXiv timed out in the live smoke run; a timeout is transient."""
    transport, calls = _scripted(
        http.Response(0, "", {}, error="The read operation timed out"), _ok("done")
    )
    result = http.fetch("https://x", transport=transport, sleep=lambda s: None)
    assert result.status == 200
    assert len(calls) == 2
