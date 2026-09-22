"""The registry half of the package-hallucination guard.

The existing suite runs the hook as a subprocess with
``IMBUE_PKG_REGISTRY_CHECK=0``, which is what keeps it hermetic and
also means the registry probe has never run under test. That probe is
where the guard decides between "this package does not exist" and "I
could not tell", and the difference is a block versus a warning.

``urlopen`` is the network boundary and is the only thing replaced
here. The URL builder and the response classification are the real
functions.
"""

from __future__ import annotations

import importlib.util
import urllib.error
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
HOOK = REPO_ROOT / "plugins" / "imbue" / "hooks" / "guard_package_hallucination.py"


def _module():
    """Load the hook as a module without registering it on sys.path."""
    spec = importlib.util.spec_from_file_location("guard_package_hallucination", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response:
    """A urlopen context manager returning one status code."""

    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


@pytest.fixture
def guard(monkeypatch: pytest.MonkeyPatch):
    """Load the guard with registry checks enabled."""
    monkeypatch.setenv("IMBUE_PKG_REGISTRY_CHECK", "1")
    return _module()


class TestRegistryUrlIsBuiltOrRefused:
    """Feature: deciding whether a name is checkable at all."""

    @pytest.mark.unit
    @pytest.mark.parametrize("disabled", ["0", "false", "no", " no "])
    def test_disabled_by_environment_yields_no_url(
        self, guard, monkeypatch: pytest.MonkeyPatch, disabled: str
    ) -> None:
        """
        GIVEN IMBUE_PKG_REGISTRY_CHECK set to a disabling value
        WHEN a registry URL is requested
        THEN None comes back and no lookup can follow

        The module docstring offers this switch as the way to run the
        guard offline, so a spelling it failed to recognize would send
        a request from a machine that asked for none.
        """
        monkeypatch.setenv("IMBUE_PKG_REGISTRY_CHECK", disabled)

        assert guard._registry_url("requests", "pypi") is None

    @pytest.mark.unit
    def test_unknown_ecosystem_yields_no_url(self, guard) -> None:
        """
        GIVEN an ecosystem with no registry template
        WHEN a registry URL is requested
        THEN None comes back

        A name parsed out of an installer this guard does not know
        cannot be denied on registry evidence it never had.
        """
        assert guard._registry_url("some-gem", "rubygems") is None

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("ecosystem", "expected"),
        [
            ("pypi", "https://pypi.org/pypi/requests/json"),
            ("npm", "https://registry.npmjs.org/requests"),
            ("crates", "https://crates.io/api/v1/crates/requests"),
        ],
    )
    def test_each_known_ecosystem_builds_its_https_url(
        self, guard, ecosystem: str, expected: str
    ) -> None:
        """
        GIVEN a known ecosystem
        WHEN a registry URL is requested
        THEN the https URL for that registry is returned
        """
        assert guard._registry_url("requests", ecosystem) == expected

    @pytest.mark.unit
    def test_a_name_carrying_url_syntax_is_quoted(self, guard) -> None:
        """
        GIVEN a package name containing a slash and a query character
        WHEN a registry URL is requested
        THEN those characters are percent-encoded

        The name comes from a command the agent proposed, so an
        unquoted one could reach a different path on the registry host
        than the name it claims to check.
        """
        url = guard._registry_url("evil/../?x=1", "pypi")

        assert url == "https://pypi.org/pypi/evil%2F..%2F%3Fx%3D1/json"


class TestRegistryAnswerIsClassified:
    """Feature: absent, present, or could not tell."""

    @pytest.mark.unit
    def test_a_2xx_response_confirms_the_package(
        self, guard, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        GIVEN a registry that answers 200
        WHEN the package is probed
        THEN it is reported as existing
        """
        monkeypatch.setattr(
            guard.urllib.request, "urlopen", lambda *a, **k: _Response(200)
        )

        assert guard._registry_exists("requests", "pypi") is True

    @pytest.mark.unit
    def test_a_404_denies_the_package(
        self, guard, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        GIVEN a registry that answers 404
        WHEN the package is probed
        THEN it is reported as absent

        This is the one answer that can escalate a finding to a block,
        so it must not be reachable from any other status.
        """

        def _raise(*_args: object, **_kwargs: object):
            raise urllib.error.HTTPError(
                url="https://pypi.org", code=404, msg="Not Found", hdrs=None, fp=None
            )

        monkeypatch.setattr(guard.urllib.request, "urlopen", _raise)

        assert guard._registry_exists("reqeusts", "pypi") is False

    @pytest.mark.unit
    @pytest.mark.parametrize("code", [429, 500, 503])
    def test_any_other_http_error_leaves_the_package_unverified(
        self, guard, monkeypatch: pytest.MonkeyPatch, code: int
    ) -> None:
        """
        GIVEN a registry that answers with a rate limit or a server
              error
        WHEN the package is probed
        THEN the result is None rather than False

        The module docstring promises the guard never blocks on a
        network failure. Treating a 503 as absence would block installs
        of real packages whenever the registry has a bad afternoon.
        """

        def _raise(*_args: object, **_kwargs: object):
            raise urllib.error.HTTPError(
                url="https://pypi.org", code=code, msg="nope", hdrs=None, fp=None
            )

        monkeypatch.setattr(guard.urllib.request, "urlopen", _raise)

        assert guard._registry_exists("requests", "pypi") is None

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "error",
        [
            urllib.error.URLError("offline"),
            TimeoutError("slow"),
            OSError("socket gone"),
            ValueError("bad response"),
        ],
        ids=["urlerror", "timeout", "oserror", "valueerror"],
    )
    def test_a_transport_failure_leaves_the_package_unverified(
        self, guard, monkeypatch: pytest.MonkeyPatch, error: Exception
    ) -> None:
        """
        GIVEN a lookup that fails before any status arrives
        WHEN the package is probed
        THEN the result is None

        An agent working offline would otherwise have every install
        denied on the grounds that nothing could be reached.
        """

        def _raise(*_args: object, **_kwargs: object):
            raise error

        monkeypatch.setattr(guard.urllib.request, "urlopen", _raise)

        assert guard._registry_exists("requests", "pypi") is None

    @pytest.mark.unit
    def test_an_unbuildable_url_skips_the_lookup_entirely(
        self, guard, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        GIVEN registry checks disabled
        WHEN the package is probed
        THEN None comes back and urlopen is never called
        """
        monkeypatch.setenv("IMBUE_PKG_REGISTRY_CHECK", "0")
        calls: list[object] = []
        monkeypatch.setattr(
            guard.urllib.request, "urlopen", lambda *a, **k: calls.append(a)
        )

        assert guard._registry_exists("requests", "pypi") is None
        assert calls == []


class TestReasonTextTellsTheOperatorWhatToDo:
    """Feature: the message attached to a finding."""

    @pytest.mark.unit
    def test_shadow_mode_says_the_block_is_coming(self, guard) -> None:
        """
        GIVEN a finding reported under shadow mode
        WHEN the reason is formatted
        THEN it names the finding and says blocking is not yet on

        Shadow mode's whole purpose is a warning the operator can
        calibrate against before flipping VOW_SHADOW_MODE, which needs
        the text to say that is what it is.
        """
        reason = guard._format_reason(
            [{"kind": "typosquat", "detail": "reqeusts is 1 edit from requests"}],
            shadow=True,
        )

        assert "[typosquat] reqeusts is 1 edit from requests" in reason
        assert "VOW_SHADOW_MODE=0" in reason

    @pytest.mark.unit
    def test_blocking_mode_tells_the_operator_to_re_run(self, guard) -> None:
        """
        GIVEN a finding reported with blocking enabled
        WHEN the reason is formatted
        THEN it asks for the name to be verified and the install re-run

        A denial with no next step is a dead end: the operator cannot
        tell whether to fix a typo or override the guard.
        """
        reason = guard._format_reason(
            [{"kind": "nonexistent", "detail": "flask-utils-pro is not on PyPI"}],
            shadow=False,
        )

        assert "[nonexistent] flask-utils-pro is not on PyPI" in reason
        assert "VOW_SHADOW_MODE" not in reason
        assert "re-run the install" in reason

    @pytest.mark.unit
    def test_every_finding_gets_its_own_line(self, guard) -> None:
        """
        GIVEN three findings in one command
        WHEN the reason is formatted
        THEN each appears on its own line under the header

        One install command can name several packages, and a reason
        that reported only the first would hide the rest.
        """
        reason = guard._format_reason(
            [
                {"kind": "typosquat", "detail": "a"},
                {"kind": "nonexistent", "detail": "b"},
                {"kind": "unverified", "detail": "c"},
            ],
            shadow=True,
        )

        assert reason.count("  - [") == 3
