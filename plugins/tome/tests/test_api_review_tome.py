"""Regression tests for the verified API-review findings in tome."""

from __future__ import annotations

import json
import os
import urllib.request
import warnings
from pathlib import Path
from typing import Any

import pytest

from tests.factories import make_finding
from tome.channels import academic, discourse, fetch, github, http, triz, web
from tome.metrics.retrieval import ndcg_at_k, recall_at_k
from tome.models import (
    Citation,
    CitationEdge,
    DomainClassification,
    QueryLog,
    ResearchPlan,
    SessionSummary,
)
from tome.output.citations import format_citation
from tome.scripts import verify_canaries
from tome.session import SessionManager
from tome.synthesis import ranker

# --- session store error contract ----------------------


def _write_session(manager: SessionManager, name: str, body: str, mtime: float) -> Path:
    path = manager._sessions_dir / f"{name}.json"
    path.write_text(body, encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


@pytest.fixture
def manager_with_valid_session(tmp_path: Path) -> SessionManager:
    manager = SessionManager(tmp_path)
    session = manager.create("topic", "algorithm", "light", ["code"])
    path = manager._store._session_path(session.id)
    os.utime(path, (1_000, 1_000))
    return manager


class TestSessionCorruption:
    @pytest.mark.unit
    def test_load_latest_skips_newest_file_missing_a_required_key(
        self, manager_with_valid_session: SessionManager
    ) -> None:
        _write_session(manager_with_valid_session, "bad", '{"id": "bad"}', 2_000)

        latest = manager_with_valid_session.load_latest()

        assert latest is not None
        assert latest.topic == "topic"

    @pytest.mark.unit
    def test_load_latest_skips_newest_file_with_invalid_json(
        self, manager_with_valid_session: SessionManager
    ) -> None:
        _write_session(manager_with_valid_session, "bad", "{not json", 2_000)

        assert manager_with_valid_session.load_latest() is not None

    @pytest.mark.unit
    def test_load_latest_returns_none_when_every_file_is_corrupt(
        self, tmp_path: Path
    ) -> None:
        manager = SessionManager(tmp_path)
        _write_session(manager, "bad", "{not json", 2_000)

        assert manager.load_latest() is None

    @pytest.mark.unit
    def test_load_reports_corrupt_file_as_value_error_not_missing(
        self, tmp_path: Path
    ) -> None:
        manager = SessionManager(tmp_path)
        _write_session(manager, "bad", "{not json", 1_000)

        with pytest.raises(ValueError, match="corrupt session"):
            manager.load("bad")

    @pytest.mark.unit
    def test_load_reports_bad_timestamp_as_corrupt_session(
        self, tmp_path: Path
    ) -> None:
        manager = SessionManager(tmp_path)
        body = json.dumps(
            {
                "id": "bad",
                "topic": "t",
                "domain": "d",
                "triz_depth": "light",
                "channels": [],
                "created_at": "garbage",
            }
        )
        _write_session(manager, "bad", body, 1_000)

        with pytest.raises(ValueError, match="corrupt session"):
            manager.load("bad")

    @pytest.mark.unit
    def test_load_still_raises_file_not_found_for_absent_session(
        self, tmp_path: Path
    ) -> None:
        with pytest.raises(FileNotFoundError):
            SessionManager(tmp_path).load("absent")

    @pytest.mark.unit
    def test_list_all_skips_session_with_bad_timestamp(
        self, manager_with_valid_session: SessionManager
    ) -> None:
        body = json.dumps(
            {
                "id": "bad",
                "topic": "t",
                "domain": "d",
                "triz_depth": "light",
                "channels": [],
                "created_at": "garbage",
            }
        )
        _write_session(manager_with_valid_session, "bad", body, 2_000)

        assert len(manager_with_valid_session.list_all()) == 1


# --- null snippet falls through to description -----------------------

_NULL_SNIPPET = {
    "title": "T",
    "url": "https://github.com/a/b",
    "snippet": None,
    "description": "real desc",
}


class TestNullSnippetFallthrough:
    @pytest.mark.unit
    def test_github_uses_description_when_snippet_is_null(self) -> None:
        assert github.parse_github_result(_NULL_SNIPPET).summary == "real desc"

    @pytest.mark.unit
    def test_lobsters_uses_description_when_snippet_is_null(self) -> None:
        assert discourse.parse_lobsters_result(_NULL_SNIPPET).summary == "real desc"

    @pytest.mark.unit
    def test_blog_uses_description_when_snippet_is_null(self) -> None:
        assert discourse.parse_blog_result(_NULL_SNIPPET).summary == "real desc"

    @pytest.mark.unit
    def test_blog_title_is_a_string_when_title_is_null(self) -> None:
        finding = discourse.parse_blog_result({"title": None, "url": "https://x.io/a"})

        assert finding.title == "https://x.io/a"

    @pytest.mark.unit
    def test_lobsters_title_is_a_string_when_title_is_null(self) -> None:
        finding = discourse.parse_lobsters_result(
            {"title": None, "url": "https://lobste.rs/s/a"}
        )

        assert finding.title == "https://lobste.rs/s/a"


# --- openalex authority and citation format --------------------------


class TestOpenAlexSource:
    @pytest.mark.unit
    @pytest.mark.parametrize("source", ["openalex", "semantic_scholar_chain"])
    def test_highly_cited_academic_source_earns_authority_bonus(
        self, source: str
    ) -> None:
        finding = make_finding(
            0.5, source=source, channel="academic", metadata={"citations": 900}
        )

        assert ranker.compute_relevance_score(finding) == pytest.approx(0.7)

    @pytest.mark.unit
    def test_openalex_citation_uses_academic_format(self) -> None:
        finding = make_finding(
            source="openalex",
            channel="academic",
            title="Paper X",
            url="https://doi.org/10.1/x",
            metadata={"year": 2024},
        )

        assert format_citation(finding).startswith("Unknown Author. ")


# --- unparseable 200 bodies do not abort the call --------------------


def _html_fetch(url: str, **_: Any) -> http.Response:
    return http.Response(200, "<html>maintenance</html>", {})


class TestUnparseableResponses:
    @pytest.mark.unit
    def test_search_academic_reports_unparseable_source_and_continues(self) -> None:
        report = fetch.search_academic("x", fetch=_html_fetch)

        sources = {e["source"] for e in report["errors"] if e["kind"] == "source_error"}
        assert {"semantic_scholar", "openalex"} <= sources
        assert len(report["queries"]) == 3

    @pytest.mark.unit
    def test_find_full_text_records_unparseable_source_and_continues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("TOME_CONTACT_EMAIL", "a@example.com")

        report = fetch.find_full_text(doi="10.1/x", fetch=_html_fetch)

        statuses = {t["source"]: t["status"] for t in report["tried"]}
        assert statuses["openalex"] == "unparseable response"
        assert "unpaywall" in statuses
        assert report["candidates"] == []


# --- canary opener follows redirects ---------------------------------


@pytest.mark.unit
def test_canary_opener_follows_https_redirects() -> None:
    opener = verify_canaries._https_only_opener()

    assert any(
        isinstance(h, urllib.request.HTTPRedirectHandler) for h in opener.handlers
    )


# --- unknown depth is rejected ---------------------------------------


class TestAdjacentFieldsDepth:
    @pytest.mark.unit
    @pytest.mark.parametrize("depth", ["Deep", "bogus", ""])
    def test_unknown_depth_is_rejected(self, depth: str) -> None:
        with pytest.raises(ValueError, match="depth"):
            triz.get_adjacent_fields("algorithm", depth)

    @pytest.mark.unit
    def test_maximum_depth_still_returns_five_fields(self) -> None:
        assert len(triz.get_adjacent_fields("algorithm", "maximum")) == 5


# --- counts below one are rejected ----------------------------------


class TestCountValidation:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "expand",
        [
            github.expand_github_queries,
            web.expand_web_queries,
            discourse.expand_discourse_queries,
            academic.expand_academic_queries,
        ],
    )
    @pytest.mark.parametrize("count", [0, -1])
    def test_expand_queries_rejects_count_below_one(
        self, expand: Any, count: int
    ) -> None:
        with pytest.raises(ValueError, match="at least 1"):
            expand("a b", count)

    @pytest.mark.unit
    @pytest.mark.parametrize("metric", [ndcg_at_k, recall_at_k])
    def test_metrics_reject_k_below_one(self, metric: Any) -> None:
        with pytest.raises(ValueError, match="k must be"):
            metric(["a", "b"], {"a"}, -1)


# --- citation docstring matches output ------------------------------


@pytest.mark.unit
def test_citation_docstring_does_not_promise_an_owner_repo_prefix() -> None:
    finding = make_finding(source="github", metadata={"stars": 5})

    assert not format_citation(finding).startswith("Owner/Repo")
    assert "Owner/Repo" not in (format_citation.__doc__ or "")


# --- group_by_channel, group_by_theme deprecated --------------------


class TestGroupByChannel:
    @pytest.mark.unit
    def test_group_by_channel_groups_by_finding_channel(self) -> None:
        findings = [make_finding(channel="code"), make_finding(channel="web")]

        assert set(ranker.group_by_channel(findings)) == {"code", "web"}

    @pytest.mark.unit
    def test_group_by_theme_warns_and_delegates(self) -> None:
        findings = [make_finding(channel="code")]

        with pytest.warns(DeprecationWarning, match="group_by_channel"):
            grouped = ranker.group_by_theme(findings)

        assert grouped == ranker.group_by_channel(findings)

    @pytest.mark.unit
    def test_group_by_channel_does_not_warn(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            ranker.group_by_channel([make_finding()])


# --- from_dict names the class on a missing key ---------------------


class TestFromDictMissingKey:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "model",
        [
            CitationEdge,
            DomainClassification,
            SessionSummary,
            Citation,
            QueryLog,
            ResearchPlan,
        ],
    )
    def test_missing_key_error_names_the_class_and_keys_present(
        self, model: Any
    ) -> None:
        with pytest.raises(KeyError, match=f"{model.__name__}.from_dict"):
            model.from_dict({"unrelated": 1})


# --- every result parser skips a result with no URL ------------------


class TestResultWithoutUrlIsSkipped:
    @pytest.mark.unit
    @pytest.mark.parametrize(
        "parse",
        [
            github.parse_github_result,
            discourse.parse_lobsters_result,
            discourse.parse_blog_result,
            lambda result: web.parse_websearch_result(result, "topic"),
        ],
        ids=["github", "lobsters", "blog", "websearch"],
    )
    @pytest.mark.parametrize("result", [{}, {"title": "t"}, {"title": "t", "url": ""}])
    def test_parser_returns_none_when_url_is_missing_or_blank(
        self, parse: Any, result: dict[str, Any]
    ) -> None:
        assert parse(result) is None
