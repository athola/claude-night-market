"""Herald's notify surface is a published contract egregore reads (TC-008).

`plugins/egregore/scripts/notify.py` does not import herald. ADR-0001
(Plugin Dependency Isolation) forbids that, so it loads
`plugins/herald/scripts/notify.py` from disk with
``importlib.util.spec_from_file_location`` and reads seven names off the
result, then calls three of them by keyword. Nothing in herald's own
suite records that, and nothing in Python's import machinery will:
renaming a herald function raises ``AttributeError`` at egregore's import
time, on a machine where herald's tests are already green.

This file is herald's half of the pin. It names the surface egregore
depends on and checks herald still provides it, without importing
egregore and inverting the dependency. Egregore's half, which compares
behavior across the two files, is
`plugins/egregore/tests/test_herald_notify_drift.py`.

The consumer list below is written out rather than derived from
egregore's file on purpose: it is what herald promises, and it stays
true whether or not egregore is checked out beside it.
"""

from __future__ import annotations

import dataclasses
import inspect

import notify
import pytest
from notify import (
    AlertContext,
    AlertEvent,
    build_issue_body,
    send_webhook,
)

#: Attribute names egregore's shim reads off the loaded herald module.
CONSUMED_NAMES = (
    "AlertContext",
    "AlertEvent",
    "WebhookURLError",
    "build_issue_body",
    "create_github_alert",
    "send_webhook",
    "validate_webhook_url",
)

#: Keywords egregore's wrappers forward. The shim calls by keyword only.
FORWARDED_KEYWORDS = {
    "build_issue_body": ("event", "ctx", "source"),
    "send_webhook": ("url", "event", "detail", "webhook_format", "source"),
}

#: AlertEvent values egregore maps to AlertsConfig flags by hand, in
#: `_EVENT_TO_CONFIG_FLAG`. An event herald adds without a flag there is
#: dispatched whatever the config says.
CONFIGURED_EVENT_VALUES = frozenset(
    {
        "crash",
        "rate_limit",
        "pipeline_failure",
        "completion",
        "watchdog_relaunch",
    }
)

#: AlertContext fields egregore's `_build_ctx` fills from kwargs, passing
#: "" for every one the caller left out.
FORWARDED_CONTEXT_FIELDS = frozenset(
    {"work_item_id", "work_item_ref", "stage", "step", "detail"}
)


@pytest.mark.parametrize("name", CONSUMED_NAMES)
def test_the_name_egregores_shim_reads_still_exists(name: str) -> None:
    """GIVEN the attribute names egregore looks up on herald's module.

    WHEN herald's notify module is inspected
    THEN the name is present

    Renaming one of these is a breaking change to a consumer that cannot
    be found by grepping herald's imports, because there are none.
    """
    assert hasattr(notify, name), name


@pytest.mark.parametrize("function_name", sorted(FORWARDED_KEYWORDS))
def test_the_keywords_egregore_forwards_are_still_accepted(
    function_name: str,
) -> None:
    """GIVEN the keyword arguments egregore's wrappers pass through.

    WHEN herald's signature for that function is inspected
    THEN every forwarded keyword names a parameter

    A parameter rename here raises TypeError at alert time, which is the
    moment something has already gone wrong elsewhere.
    """
    parameters = inspect.signature(getattr(notify, function_name)).parameters
    for keyword in FORWARDED_KEYWORDS[function_name]:
        assert keyword in parameters, f"{function_name}({keyword}=)"


def test_every_alert_event_has_a_flag_on_egregores_side() -> None:
    """GIVEN egregore's hand-kept event-to-config-flag table.

    WHEN herald's AlertEvent values are compared to it
    THEN the two sets match

    Adding an event to herald alone leaves it unconfigurable in
    egregore, where _is_event_enabled fails open for unknown values.
    Adding a flag alone leaves a dead entry. Either way, edit both.
    """
    assert {member.value for member in AlertEvent} == CONFIGURED_EVENT_VALUES


@pytest.mark.parametrize("field_name", sorted(FORWARDED_CONTEXT_FIELDS))
def test_a_forwarded_context_field_defaults_to_empty(field_name: str) -> None:
    """GIVEN egregore's _build_ctx, which passes "" for unset fields.

    WHEN herald's AlertContext default for that field is inspected
    THEN it is the empty string

    Giving one of these a non-empty default would have egregore silently
    blank it on every call that did not name the field.
    """
    defaults = {f.name: f.default for f in dataclasses.fields(AlertContext)}
    assert defaults[field_name] == ""


def test_the_source_label_is_a_parameter_and_not_a_constant() -> None:
    """GIVEN egregore, which relabels every alert as "egregore".

    WHEN a body is built with a caller-supplied source
    THEN that label appears in the rendered heading

    Hardcoding "Herald" in the heading would make every egregore alert
    claim the wrong origin, and no herald test would notice.
    """
    body = build_issue_body(
        AlertEvent.CRASH, AlertContext(detail="d"), source="egregore"
    )
    assert body.startswith("## Egregore Alert: crash")


def test_send_webhook_rejects_a_bad_url_by_returning_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GIVEN egregore's wrapper, which returns bool(herald's answer).

    WHEN send_webhook is handed a URL that fails validation
    THEN it returns False rather than raising

    Egregore coerces the result with bool() and has no except around it,
    so an exception here would propagate out of a shim documented to
    degrade quietly.
    """

    def _no_subprocess(*args: object, **kwargs: object) -> None:
        raise AssertionError("a rejected URL must not reach curl")

    monkeypatch.setattr(notify.subprocess, "run", _no_subprocess)
    assert (
        send_webhook(
            "http://example.com/hook",
            AlertEvent.CRASH,
            "detail",
            source="egregore",
        )
        is False
    )
