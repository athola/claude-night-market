"""Egregore's notify surface must not drift from herald's (TC-008).

`egregore/scripts/notify.py` is a compatibility shim, not a copy. It loads
`herald/scripts/notify.py` by path with
``importlib.util.spec_from_file_location`` and re-exports what it finds,
because ADR-0001 (Plugin Dependency Isolation) forbids a cross-plugin
import. When that load raises, a second branch in the same file supplies
stubs so egregore still starts.

That shape leaves three surfaces that can drift, and none of them is
covered by the 26 tests egregore shares byte-for-byte with herald. Those
tests exercise herald's own function objects through an egregore-shaped
name, so they pass whatever egregore does:

1. the stub branch, which runs on exactly the machines nobody tests on
2. egregore's kwargs-to-``AlertContext`` wrappers, which are its own code
3. the names egregore reads off herald, which herald may rename freely

Change either file without changing the other and these tests go red.
The matching test on herald's side is
`plugins/herald/tests/test_egregore_consumer_surface.py`.
"""

from __future__ import annotations

import dataclasses
import importlib
import importlib.util
import inspect
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

_PLUGINS = Path(__file__).resolve().parents[2]
_HERALD_SOURCE = _PLUGINS / "herald" / "scripts" / "notify.py"
_EGREGORE_SOURCE = _PLUGINS / "egregore" / "scripts" / "notify.py"

#: Names egregore promises to expose whichever branch it took.
_PUBLIC_NAMES = (
    "AlertContext",
    "AlertEvent",
    "WebhookURLError",
    "alert",
    "build_issue_body",
    "config_alert",
    "create_github_alert",
    "send_webhook",
    "validate_webhook_url",
)

#: Names the shim binds straight through to herald with no wrapper.
_RE_EXPORTED_NAMES = (
    "AlertEvent",
    "AlertContext",
    "WebhookURLError",
    "validate_webhook_url",
    "create_github_alert",
)

#: One call per shape the kwargs wrapper could map wrong.
_CONTEXT_KWARGS: dict[str, dict[str, str]] = {
    "empty": {},
    "id_only": {"work_item_id": "wrk_001"},
    "ref_only": {"work_item_ref": "owner/repo#7"},
    "stage_and_step": {"stage": "build", "step": "compile"},
    "detail_only": {"detail": "exit code 2"},
    "every_field": {
        "work_item_id": "wrk_002",
        "work_item_ref": "owner/repo#8",
        "stage": "review",
        "step": "lint",
        "detail": "three findings",
    },
}

_TIMESTAMP_LINE = re.compile(r"^\*\*Timestamp:\*\*.*$", re.MULTILINE)


def _load_by_path(name: str, source: Path) -> ModuleType:
    """Execute a module from its file without touching the shared import."""
    spec = importlib.util.spec_from_file_location(name, source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def _without_timestamp(body: str) -> str:
    """Drop the one line that differs when two calls straddle a second."""
    return _TIMESTAMP_LINE.sub("**Timestamp:** <pinned>", body)


@pytest.fixture(scope="module")
def herald() -> Iterator[ModuleType]:
    """Herald's notify module, loaded from its file as egregore loads it.

    Loaded under a private name rather than read out of ``sys.modules``,
    so the comparisons below run herald's file against egregore's file
    instead of running one loaded object against itself.
    """
    module = _load_by_path("_canonical_herald_notify", _HERALD_SOURCE)
    yield module
    sys.modules.pop("_canonical_herald_notify", None)


@pytest.fixture(scope="module")
def shim() -> ModuleType:
    """Egregore's notify as the rest of the plugin imports it."""
    return importlib.import_module("notify")


@pytest.fixture
def stub_notify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[ModuleType]:
    """Egregore's notify with the herald load forced to fail.

    ``HERALD_NOTIFY_PATH`` points the shim at a file that does not exist,
    so ``exec_module`` raises ``FileNotFoundError`` (an ``OSError``) and
    the stub branch runs. The module is loaded under a private name so
    the shared ``notify`` entry the rest of the suite imports is never
    replaced. ``_herald_notify`` is saved and restored because the shim
    writes that key before it knows the load will succeed.
    """
    monkeypatch.setenv("HERALD_NOTIFY_PATH", str(tmp_path / "absent_notify.py"))
    saved = sys.modules.get("_herald_notify")
    module = _load_by_path("_egregore_notify_stub", _EGREGORE_SOURCE)
    yield module
    sys.modules.pop("_egregore_notify_stub", None)
    if saved is None:
        sys.modules.pop("_herald_notify", None)
    else:
        sys.modules["_herald_notify"] = saved


# --- The fixtures must exercise the branches they claim ----------------


@pytest.mark.parametrize("name", _RE_EXPORTED_NAMES)
def test_the_shim_re_exports_herald_rather_than_defining_its_own(
    name: str, shim: ModuleType
) -> None:
    """GIVEN egregore imported normally, with herald present on disk.

    WHEN each straight-through name is asked which module defined it
    THEN it names the loaded herald module, not egregore's own

    Without this, every herald-present comparison below could be herald
    measured against itself while egregore had quietly forked.
    """
    assert shim._HERALD_AVAILABLE is True
    assert getattr(shim, name).__module__ == "_herald_notify", name


def test_the_stub_fixture_really_takes_the_herald_absent_branch(
    stub_notify: ModuleType,
) -> None:
    """GIVEN HERALD_NOTIFY_PATH aimed at a file that does not exist.

    WHEN egregore's notify module is executed
    THEN it reports herald as unavailable and defines its own AlertEvent

    Without this, the stub assertions could be reading herald's objects.
    """
    assert stub_notify._HERALD_AVAILABLE is False
    assert stub_notify._herald_mod is None
    assert stub_notify.AlertEvent.__module__ == "_egregore_notify_stub"


# --- Surface 1: the stub branch matches herald -------------------------


def test_stub_alert_events_match_herald_exactly(
    stub_notify: ModuleType, herald: ModuleType
) -> None:
    """GIVEN herald absent, so egregore defines its own AlertEvent.

    WHEN its member names and values are compared to herald's
    THEN both sets match

    An event added to herald and not to the stub is dispatched on a
    machine with herald and silently unknown on a machine without it.
    """
    stub_members = {member.name: member.value for member in stub_notify.AlertEvent}
    herald_members = {member.name: member.value for member in herald.AlertEvent}
    assert stub_members == herald_members


def test_stub_alert_context_carries_every_field_herald_defines(
    stub_notify: ModuleType, herald: ModuleType
) -> None:
    """GIVEN herald absent, so egregore defines its own AlertContext.

    WHEN its dataclass fields are compared to herald's
    THEN the stub defines at least every field herald does

    A caller that sets a field herald has and the stub lacks raises
    TypeError only on the machine without herald.
    """
    stub_fields = {f.name for f in dataclasses.fields(stub_notify.AlertContext)}
    herald_fields = {f.name for f in dataclasses.fields(herald.AlertContext)}
    assert herald_fields <= stub_fields, sorted(herald_fields - stub_fields)


def test_the_config_flag_map_covers_every_herald_event(
    stub_notify: ModuleType, herald: ModuleType
) -> None:
    """GIVEN the _EVENT_TO_CONFIG_FLAG table egregore keeps by hand.

    WHEN its keys are compared to herald's AlertEvent values
    THEN every event has a flag and no flag names a dead event

    An unmapped event fails open in _is_event_enabled, so a config that
    disables it is ignored rather than honored.
    """
    assert set(stub_notify._EVENT_TO_CONFIG_FLAG) == {
        member.value for member in herald.AlertEvent
    }


@pytest.mark.parametrize("name", _PUBLIC_NAMES)
def test_every_public_name_resolves_without_herald(
    name: str, stub_notify: ModuleType
) -> None:
    """GIVEN herald absent.

    WHEN each name egregore's __all__ promises is looked up
    THEN it resolves

    The stub branch is the one no import error ever surfaces from, so a
    name defined only in the herald-backed branch fails at call time.
    """
    assert getattr(stub_notify, name, None) is not None


def test_the_stub_branch_reports_failure_rather_than_raising(
    stub_notify: ModuleType,
) -> None:
    """GIVEN herald absent.

    WHEN the three dispatch entry points are called
    THEN each returns a falsy value instead of raising

    ADR-0001 asks egregore to degrade, so a missing herald must not take
    the orchestrator down with it.
    """
    event = stub_notify.AlertEvent.CRASH
    assert stub_notify.build_issue_body(event, detail="boom") == ""
    assert stub_notify.send_webhook("https://example.com/h", event, "boom") is False
    assert stub_notify.create_github_alert("t", "b") is False


# --- Surface 2: egregore's own kwargs wrappers -------------------------


@pytest.mark.parametrize("shape", sorted(_CONTEXT_KWARGS))
def test_kwargs_build_the_same_body_as_an_explicit_context(
    shape: str, shim: ModuleType, herald: ModuleType
) -> None:
    """GIVEN a set of AlertContext fields passed to egregore as kwargs.

    WHEN the resulting issue body is compared to herald's for the same
        fields passed as an AlertContext
    THEN the two bodies match once the timestamp line is pinned

    This is egregore's own mapping code, not herald's, and it is the half
    of the shim the shared tests never reach.
    """
    kwargs = _CONTEXT_KWARGS[shape]
    event = herald.AlertEvent.PIPELINE_FAILURE
    from_kwargs = shim.build_issue_body(event, **kwargs)
    from_context = herald.build_issue_body(
        event, herald.AlertContext(**kwargs), source="egregore"
    )
    assert _without_timestamp(from_kwargs) == _without_timestamp(from_context)


def test_an_explicit_context_wins_over_the_kwargs(
    shim: ModuleType, herald: ModuleType
) -> None:
    """GIVEN both a populated ctx and a conflicting work_item_id kwarg.

    WHEN the body is built
    THEN the ctx value appears and the kwarg does not

    _build_ctx documents ctx as taking precedence; the published
    positional order makes the conflict reachable by accident.
    """
    body = shim.build_issue_body(
        herald.AlertEvent.CRASH,
        ctx=herald.AlertContext(work_item_id="from_ctx"),
        work_item_id="from_kwarg",
    )
    assert "from_ctx" in body
    assert "from_kwarg" not in body


def test_egregore_labels_its_alerts_as_egregore_not_herald(
    shim: ModuleType, herald: ModuleType
) -> None:
    """GIVEN no explicit source argument.

    WHEN egregore builds an issue body and herald builds one
    THEN egregore's says egregore and herald's says herald

    The source default is the one deliberate divergence in the shim, so
    a test that let them match would pin the wrong thing.
    """
    event = herald.AlertEvent.COMPLETION
    assert "Egregore Alert" in shim.build_issue_body(event)
    assert "Herald Alert" in herald.build_issue_body(event, herald.AlertContext())


def test_the_alert_title_names_the_source_and_the_work_item(
    shim: ModuleType, herald: ModuleType
) -> None:
    """GIVEN a context carrying a work item id.

    WHEN egregore builds the GitHub issue title
    THEN it matches the title herald builds for the same alert

    _build_alert_title is a re-implementation of the four lines herald
    keeps inline in alert(); the two must agree or the same incident
    opens two differently named issues.
    """
    event = herald.AlertEvent.RATE_LIMIT
    ctx = herald.AlertContext(work_item_id="wrk_009", source="egregore")
    assert shim._build_alert_title(event, ctx, "egregore") == (
        f"[egregore] {event.value} - {ctx.work_item_id}"
    )


def test_a_context_without_a_work_item_leaves_the_title_bare(
    shim: ModuleType, herald: ModuleType
) -> None:
    """GIVEN a context with no work item id.

    WHEN the title is built
    THEN it carries the source and event and no trailing separator
    """
    event = herald.AlertEvent.WATCHDOG_RELAUNCH
    title = shim._build_alert_title(event, herald.AlertContext(), "egregore")
    assert title == f"[egregore] {event.value}"


# --- Surface 3: the names egregore reads off herald --------------------


@pytest.mark.parametrize(
    "name",
    [
        "AlertContext",
        "AlertEvent",
        "WebhookURLError",
        "build_issue_body",
        "create_github_alert",
        "send_webhook",
        "validate_webhook_url",
    ],
)
def test_herald_still_exposes_the_name_the_shim_reads(
    name: str, herald: ModuleType
) -> None:
    """GIVEN the attribute names the shim looks up on the loaded module.

    WHEN herald's module is inspected
    THEN each name is present

    A rename in herald turns into an AttributeError at egregore import
    time, before any of egregore's own tests get to run.
    """
    assert hasattr(herald, name), name


def test_herald_accepts_the_keywords_the_shim_forwards(herald: ModuleType) -> None:
    """GIVEN the keyword names egregore's wrappers pass through.

    WHEN herald's signatures are inspected
    THEN each keyword is accepted

    The shim calls herald by keyword only, so a parameter rename in
    herald is silent until an alert fires.
    """
    forwarded: dict[str, tuple[str, ...]] = {
        "build_issue_body": ("event", "ctx", "source"),
        "send_webhook": ("url", "event", "detail", "webhook_format", "source"),
    }
    for function_name, keywords in forwarded.items():
        parameters = inspect.signature(getattr(herald, function_name)).parameters
        for keyword in keywords:
            assert keyword in parameters, f"{function_name}({keyword}=)"


def test_herald_alert_context_defaults_are_all_empty_strings(
    herald: ModuleType,
) -> None:
    """GIVEN egregore's _build_ctx, which passes "" for every unset field.

    WHEN herald's AlertContext defaults are inspected
    THEN each field egregore forwards already defaults to empty

    If herald gave a field a non-empty default, egregore would overwrite
    it with "" on every call that did not name it.
    """
    forwarded = {"work_item_id", "work_item_ref", "stage", "step", "detail"}
    for field in dataclasses.fields(herald.AlertContext):
        if field.name in forwarded:
            assert field.default == "", field.name


def test_a_failed_herald_load_leaves_no_half_module_behind(
    stub_notify: ModuleType,
) -> None:
    """GIVEN HERALD_NOTIFY_PATH aimed at a file that does not exist.

    WHEN egregore's notify module is executed and the herald load fails
    THEN sys.modules holds no half-initialized "_herald_notify" entry

    The shim registered the module before exec_module ran, so a failed
    load left an empty module under that name for the next importer.
    """
    leftover = sys.modules.get("_herald_notify")
    assert leftover is None or hasattr(leftover, "AlertEvent")
