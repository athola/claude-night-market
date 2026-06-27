"""Tests for EGR-003 and EGR-004 -- classify_technique guard and alert title
extraction."""

from __future__ import annotations

from unittest.mock import patch

from notify import (  # type: ignore[import-not-found]  # pytest pythonpath
    AlertContext,
    AlertEvent,
    _build_alert_title,
    alert,
)
from scout import classify_technique


class TestEgr003ClassifyTechniqueEmptyGuard:
    """EGR-003: classify_technique returns None when no keywords match."""

    def test_gibberish_description_returns_none(self) -> None:
        """Description with no matching keywords returns None (not 'general')."""
        assert classify_technique("zzz xyzzy qqqq") is None

    def test_empty_description_returns_none(self) -> None:
        """Empty string has no matching keywords, returns None."""
        assert classify_technique("") is None

    def test_testing_keywords_match_testing_category(self) -> None:
        """Description with testing keywords classifies as 'testing'."""
        assert classify_technique("write pytest tests for coverage") == "testing"

    def test_security_keywords_match_security_category(self) -> None:
        """Description with security keywords classifies as 'security'."""
        assert classify_technique("check for vulnerabilities in auth") == "security"


class TestEgr004BuildAlertTitle:
    """EGR-004: _build_alert_title extracted from alert() duplication."""

    def test_title_without_work_item(self) -> None:
        """Title is '[source] event' when no work_item_id."""
        event = AlertEvent.CRASH
        ctx = AlertContext()
        assert _build_alert_title(event, ctx, "egregore") == "[egregore] crash"

    def test_title_with_work_item(self) -> None:
        """Title includes work_item_id when present."""
        event = AlertEvent.COMPLETION
        ctx = AlertContext(work_item_id="wrk_042")
        assert (
            _build_alert_title(event, ctx, "egregore")
            == "[egregore] completion - wrk_042"
        )

    def test_alert_constructs_title_via_build_alert_title(self) -> None:
        """alert() passes the title built by _build_alert_title to create_github_alert."""
        event = AlertEvent.CRASH
        captured: list[str] = []

        def _capture(title: str, body: str, labels: list[str]) -> bool:
            captured.append(title)
            return True

        with patch("notify.create_github_alert", side_effect=_capture):
            alert(event, overseer_method="github-repo-owner", source="egregore")

        assert captured == ["[egregore] crash"]

    def test_custom_source_prefix_in_title(self) -> None:
        """Source prefix is included in the title."""
        event = AlertEvent.RATE_LIMIT
        ctx = AlertContext(work_item_id="wrk_007")
        assert (
            _build_alert_title(event, ctx, "herald") == "[herald] rate_limit - wrk_007"
        )
