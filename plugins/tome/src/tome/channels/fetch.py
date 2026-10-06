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


def _error(source: str, reply: http.Response) -> dict[str, str]:
    if reply.status == http.TOO_MANY_REQUESTS:
        return {"kind": "rate_limit", "source": source, "message": "HTTP 429"}
    reason = reply.error or f"HTTP {reply.status}"
    return {"kind": "source_error", "source": source, "message": reason}


def _s2_headers() -> dict[str, str]:
    """Semantic Scholar's shared anonymous pool is what returned 429."""
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    return {"x-api-key": key} if key else {}


def search_academic(
    topic: str, *, fetch: Fetch = http.fetch, limit: int = 10
) -> dict[str, Any]:
    """Search arXiv, Semantic Scholar and OpenAlex; report each source."""
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
        reply = fetch(url, headers=headers)
        found = (
            [f.to_dict() for f in parse(reply.body)] if reply.status == http.OK else []
        )
        if reply.status != http.OK:
            errors.append(_error(source, reply))
        findings.extend(found)
        queries.append({"source": source, "query": topic, "result_count": len(found)})
    return {
        "channel": "academic",
        "findings": findings,
        "queries": queries,
        "errors": errors,
    }


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
    *, doi: str | None = None, title: str | None = None, fetch: Fetch = http.fetch
) -> dict[str, Any]:
    """Collect open-access copies of one paper, recording every source tried."""
    lookups: list[tuple[str, str, dict[str, str], Callable[[str], list]]] = []
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
        reply = fetch(url, headers=headers)
        tried.append({"source": source, "status": reply.status})
        if reply.status == http.OK:
            candidates.extend(extract(reply.body))

    unique: list[dict[str, str]] = []
    for candidate in candidates:
        if candidate["url"] not in {c["url"] for c in unique}:
            unique.append(candidate)
    return {"doi": doi, "title": title, "candidates": unique, "tried": tried}


def search_reddit(
    topic: str,
    subreddits: Sequence[str],
    *,
    fetch: Fetch = http.fetch,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Search each subreddit's Atom feed, spacing the requests."""
    findings: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for index, subreddit in enumerate(subreddits):
        if index:
            sleep(REDDIT_SPACING_SECONDS)
        reply = fetch(discourse.build_reddit_rss_search_url(topic, subreddit))
        found = []
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
    return {
        "channel": "discourse",
        "findings": findings,
        "queries": queries,
        "errors": errors,
    }


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
