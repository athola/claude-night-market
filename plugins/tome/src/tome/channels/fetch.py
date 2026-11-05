"""Fetch a channel's sources directly, for agents whose WebFetch falls short.

WebFetch cannot retry a 429, send an API key, or reach reddit.com. On
2026-10-05 that left a research run with no academic results, since arXiv
and Semantic Scholar both answered 429, and no Reddit results. The
channel agents run this module through Bash instead::

    python -m tome.channels.fetch academic "wifi halow mesh throughput"
    python -m tome.channels.fetch reddit "meshtastic speed" -s amateurradio
    python -m tome.channels.fetch fulltext --doi 10.1145/3570361.3613268

Each prints the channel JSON the agents return: findings, one ``queries``
row per source with its result count, and ``errors`` naming each source
that was rate-limited or blocked. A rate-limited source then reads as
rate-limited, not as an empty field.

The parsers stay pure in ``academic`` and ``discourse``. This module is
the only one that touches the network.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable, Sequence
from typing import Any

from tome.channels import academic, discourse, http

Fetch = Callable[..., http.Response]
Parser = Callable[[str], list]

# Reddit answered a second rapid feed request with 429 (probed 2026-10-05).
REDDIT_SPACING_SECONDS = 2.0

# Agents run this through Bash, which stops a command at 120s by default
# and loses everything it would have printed. One request already in
# flight can run 30s past the budget, so the budget ends at 90s. A source
# not started by then is reported as skipped.
BUDGET_SECONDS = 90.0
_BUDGET_SPENT = "skipped, time budget spent"


# json.JSONDecodeError is a ValueError. KeyError and TypeError cover a
# well-formed body that is not the shape the service documents.
_UNPARSEABLE = (ValueError, KeyError, TypeError)


def _error(source: str, reply: http.Response) -> dict[str, str]:
    if reply.status == http.TOO_MANY_REQUESTS:
        return {"kind": "rate_limit", "source": source, "message": "HTTP 429"}
    reason = reply.error or f"HTTP {reply.status}"
    return {"kind": "source_error", "source": source, "message": reason}


def _s2_headers() -> dict[str, str]:
    """Semantic Scholar's shared anonymous pool is what returned 429."""
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    return {"x-api-key": key} if key else {}


def _spent(source: str) -> dict[str, str]:
    return {"kind": "source_error", "source": source, "message": _BUDGET_SPENT}


def _channel_report(
    channel: str,
    findings: list[dict[str, Any]],
    queries: list[dict[str, Any]],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    """The report shape every channel search returns."""
    return {
        "channel": channel,
        "findings": findings,
        "queries": queries,
        "errors": errors,
    }


def search_academic(
    topic: str,
    *,
    fetch: Fetch = http.fetch,
    limit: int = 10,
    budget_seconds: float = BUDGET_SECONDS,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Search arXiv, Semantic Scholar and OpenAlex; report each source."""
    deadline = clock() + budget_seconds
    sources: list[tuple[str, str, dict[str, str], Parser]] = [
        (
            "arxiv",
            academic.build_arxiv_search_url(topic, limit),
            {},
            academic.parse_arxiv_response,
        ),
        (
            "semantic_scholar",
            academic.build_semantic_scholar_url(topic, limit),
            _s2_headers(),
            lambda body: academic.parse_semantic_scholar_response(json.loads(body)),
        ),
        (
            "openalex",
            academic.build_openalex_search_url(topic, limit),
            {},
            lambda body: academic.parse_openalex_response(json.loads(body)),
        ),
    ]
    findings: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for source, url, headers, parse in sources:
        found: list[dict[str, Any]] = []
        if clock() >= deadline:
            errors.append(_spent(source))
            queries.append({"source": source, "query": topic, "result_count": 0})
            continue
        reply = fetch(url, headers=headers, deadline=deadline)
        if reply.status != http.OK:
            errors.append(_error(source, reply))
        else:
            try:
                found = [f.to_dict() for f in parse(reply.body)]
            except _UNPARSEABLE:
                errors.append(
                    {
                        "kind": "source_error",
                        "source": source,
                        "message": "unparseable response",
                    }
                )
        findings.extend(found)
        queries.append({"source": source, "query": topic, "result_count": len(found)})
    return _channel_report("academic", findings, queries, errors)


def _openalex_candidates(body: str) -> list[dict[str, str]]:
    """PDF locations, repository copies first: publishers block bots (ACM 403)."""
    locations = json.loads(body).get("locations") or []
    ranked = sorted(
        (loc for loc in locations if loc.get("pdf_url")),
        key=lambda loc: (loc.get("source") or {}).get("type") != "repository",
    )
    return [{"url": loc["pdf_url"], "source": "openalex"} for loc in ranked]


def _arxiv_candidates(body: str) -> list[dict[str, str]]:
    return [
        {"url": f.metadata["pdf_url"], "source": "arxiv"}
        for f in academic.parse_arxiv_response(body)
        if f.metadata.get("pdf_url")
    ]


def _s2_candidates(body: str) -> list[dict[str, str]]:
    pdf = (json.loads(body).get("openAccessPdf") or {}).get("url")
    return [{"url": pdf, "source": "semantic_scholar"}] if pdf else []


def _unpaywall_candidates(body: str) -> list[dict[str, str]]:
    best = academic.parse_unpaywall_response(json.loads(body))
    return [{"url": best, "source": "unpaywall"}] if best else []


def find_full_text(
    *,
    doi: str | None = None,
    title: str | None = None,
    fetch: Fetch = http.fetch,
    budget_seconds: float = BUDGET_SECONDS,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Collect open-access copies of one paper, recording every source tried."""
    deadline = clock() + budget_seconds
    lookups: list[tuple[str, str, dict[str, str], Parser]] = []
    tried: list[dict[str, Any]] = []
    if doi:
        lookups.append(
            ("openalex", academic.build_openalex_doi_url(doi), {}, _openalex_candidates)
        )
    if title:
        lookups.append(
            ("arxiv", academic.build_arxiv_title_url(title), {}, _arxiv_candidates)
        )
    if doi:
        lookups.append(
            (
                "semantic_scholar",
                academic.build_semantic_scholar_doi_url(doi),
                _s2_headers(),
                _s2_candidates,
            )
        )
        try:
            lookups.append(
                (
                    "unpaywall",
                    academic.build_unpaywall_url(doi),
                    {},
                    _unpaywall_candidates,
                )
            )
        except ValueError:
            tried.append(
                {"source": "unpaywall", "status": "skipped: TOME_CONTACT_EMAIL unset"}
            )

    candidates: list[dict[str, str]] = []
    for source, url, headers, extract in lookups:
        if clock() >= deadline:
            tried.append({"source": source, "status": _BUDGET_SPENT})
            continue
        reply = fetch(url, headers=headers, deadline=deadline)
        tried.append({"source": source, "status": reply.status})
        if reply.status == http.OK:
            try:
                candidates.extend(extract(reply.body))
            except _UNPARSEABLE:
                tried[-1]["status"] = "unparseable response"

    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate["url"] not in seen:
            seen.add(candidate["url"])
            unique.append(candidate)
    return {"doi": doi, "title": title, "candidates": unique, "tried": tried}


def search_reddit(  # noqa: PLR0913 - four keyword-only seams (fetch, sleep, budget, clock) the tests inject
    topic: str,
    subreddits: Sequence[str],
    *,
    fetch: Fetch = http.fetch,
    sleep: Callable[[float], None] = time.sleep,
    budget_seconds: float = BUDGET_SECONDS,
    clock: Callable[[], float] = time.monotonic,
) -> dict[str, Any]:
    """Search each subreddit's Atom feed, spacing the requests."""
    deadline = clock() + budget_seconds
    findings: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for index, subreddit in enumerate(subreddits):
        found = []
        # Budget first: spacing before a subreddit that is then skipped spends
        # the time the budget exists to save.
        if clock() >= deadline:
            error = _spent("reddit")
            error["message"] = f"r/{subreddit}: {_BUDGET_SPENT}"
            errors.append(error)
            queries.append(
                {
                    "source": "reddit",
                    "query": f"r/{subreddit} {topic}",
                    "result_count": 0,
                }
            )
            continue
        if index:
            sleep(REDDIT_SPACING_SECONDS)
        reply = fetch(
            discourse.build_reddit_rss_search_url(topic, subreddit), deadline=deadline
        )
        if reply.status == http.OK:
            found = [
                f.to_dict() for f in discourse.parse_reddit_rss(reply.body, subreddit)
            ]
        else:
            error = _error("reddit", reply)
            error["message"] = f"r/{subreddit}: {error['message']}"
            errors.append(error)
        findings.extend(found)
        queries.append(
            {
                "source": "reddit",
                "query": f"r/{subreddit} {topic}",
                "result_count": len(found),
            }
        )
    return _channel_report("discourse", findings, queries, errors)


_SEARCHES: dict[str, Callable[[argparse.Namespace], dict[str, Any]]] = {
    "academic": lambda args: search_academic(args.topic),
    "reddit": lambda args: search_reddit(args.topic, args.subreddit or ["programming"]),
    "fulltext": lambda args: find_full_text(doi=args.doi, title=args.title),
}


def main(argv: Sequence[str] | None = None) -> int:
    """Run one search and print its JSON report."""
    parser = argparse.ArgumentParser(prog="python -m tome.channels.fetch")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("academic").add_argument("topic")
    reddit = sub.add_parser("reddit")
    reddit.add_argument("topic")
    reddit.add_argument("-s", "--subreddit", action="append")
    fulltext = sub.add_parser("fulltext")
    fulltext.add_argument("--doi")
    fulltext.add_argument("--title")
    args = parser.parse_args(argv)
    if args.command == "fulltext" and not (args.doi or args.title):
        parser.error("fulltext needs --doi or --title")
    json.dump(_SEARCHES[args.command](args), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
