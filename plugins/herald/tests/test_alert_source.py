"""PLR0913 regression tests for AlertContext.source in notify.py.

The PLR0913 refactor moved the ``source`` label from a standalone keyword
argument on ``alert()`` into ``AlertContext.source`` (default "herald").
The function now extracts it via ``source = ctx.source``.

These tests assert that the new extraction path works correctly for both
the default (ctx=None) and custom-source cases.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from notify import AlertContext, AlertEvent, alert


class TestAlertContextSourceField:
    """Feature: alert() extracts source from AlertContext.source field.

    As a herald plugin consumer
    I want the source label to be carried inside AlertContext
    So that I can control the issue prefix without a separate parameter.
    """

    @patch("notify.create_github_alert", return_value=True)
    def test_null_ctx_defaults_source_to_herald(self, mock_create: MagicMock) -> None:
        """Scenario: Omitting ctx extracts source="herald" from AlertContext default.

        Given ctx is not passed to alert() (defaults to None)
        When alert() constructs AlertContext() and calls source = ctx.source
        Then the GitHub issue title contains "[herald]".
        And "herald" appears in the issue labels.
        """
        alert(event=AlertEvent.COMPLETION)

        call_kwargs = mock_create.call_args[1]
        assert "[herald]" in call_kwargs["title"]
        assert "herald" in call_kwargs["labels"]

    @patch("notify.create_github_alert", return_value=True)
    def test_custom_source_extracted_from_ctx_field(
        self, mock_create: MagicMock
    ) -> None:
        """Scenario: Custom AlertContext.source appears in the issue prefix.

        Given ctx=AlertContext(source="sentinel")
        When alert() calls source = ctx.source
        Then the GitHub issue title contains "[sentinel]".
        And "sentinel" appears in the issue labels.
        """
        alert(
            event=AlertEvent.CRASH,
            ctx=AlertContext(source="sentinel"),
        )

        call_kwargs = mock_create.call_args[1]
        assert "[sentinel]" in call_kwargs["title"]
        assert "sentinel" in call_kwargs["labels"]
