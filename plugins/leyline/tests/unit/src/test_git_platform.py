"""Tests for leyline.git_platform Python wrapper (AR-30).

Feature: One Python module exposing the contract of the
``leyline:git-platform`` skill so plugin scripts no longer
reinvent ``["gh", "api", ...]`` argv plus error handling plus
JSON parsing in seven places.

As a plugin script
I want ``gh_api()`` and ``gh_graphql()`` helpers
So that gh-cli interactions are routed through one tested shim.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any
from unittest.mock import patch

import pytest

from leyline.git_platform import GhCommandError, gh_api, gh_graphql


def _make_completed(returncode: int, stdout: str = "", stderr: str = "") -> Any:
    """Construct a CompletedProcess-shaped stand-in for ``subprocess.run``."""
    return subprocess.CompletedProcess(
        args=["gh"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


class TestGhApi:
    """Scenarios for gh_api()."""

    @pytest.mark.unit
    def test_returns_parsed_json_on_success(self):
        """Given gh exits 0 with JSON stdout,
        When gh_api is called,
        Then the parsed JSON is returned.
        """
        payload = {"id": "abc", "name": "repo"}
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout=json.dumps(payload))
            result = gh_api("repos/foo/bar")
        assert result == payload

    @pytest.mark.unit
    def test_raises_on_non_zero_exit(self):
        """Given gh exits non-zero,
        When gh_api is called,
        Then GhCommandError is raised carrying the stderr.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(1, stderr="not found")
            with pytest.raises(GhCommandError) as excinfo:
                gh_api("repos/none/nope")
        assert "not found" in str(excinfo.value)

    @pytest.mark.unit
    def test_raises_on_invalid_json(self):
        """Given gh exits 0 with non-JSON stdout,
        When gh_api is called,
        Then GhCommandError is raised.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="<html>oops</html>")
            with pytest.raises(GhCommandError):
                gh_api("repos/foo/bar")

    @pytest.mark.unit
    def test_rejects_equals_in_field_key(self):
        """Field-key guard (#484): ``=`` in a field key would split
        the ``-f key=value`` argv pair when ``gh`` parses it, smuggling
        extra fields. Reject up-front with ValueError so callers cannot
        accidentally introduce that drift.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            with pytest.raises(ValueError, match="="):
                gh_api(
                    "repos/foo/bar",
                    method="POST",
                    fields={"title=evil": "value"},
                )
        run.assert_not_called()

    @pytest.mark.unit
    def test_passes_endpoint_to_gh(self):
        """Given an endpoint string,
        When gh_api is called,
        Then the argv contains ``gh api <endpoint>``.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            gh_api("repos/foo/bar/issues")
        call_args = run.call_args[0][0]
        assert call_args[0] == "gh"
        assert call_args[1] == "api"
        assert "repos/foo/bar/issues" in call_args


class TestGhCommandErrorPayload:
    """S10 (#484): GhCommandError carries structured payload."""

    @pytest.mark.unit
    def test_carries_cmd_returncode_stderr_on_non_zero_exit(self):
        """Given gh exits non-zero,
        When GhCommandError is raised,
        Then the exception exposes ``cmd`` (list[str]),
        ``returncode`` (int), and ``stderr`` (str) as attributes for
        programmatic error handling.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(
                3,
                stdout="",
                stderr="auth required",
            )
            with pytest.raises(GhCommandError) as excinfo:
                gh_api("repos/foo/bar")
        err = excinfo.value
        assert err.cmd == ["gh", "api", "repos/foo/bar"]
        assert err.returncode == 3
        assert err.stderr == "auth required"

    @pytest.mark.unit
    def test_carries_cmd_with_returncode_none_on_invalid_json(self):
        """Given gh exits 0 with non-JSON stdout,
        When GhCommandError is raised,
        Then ``returncode`` is None (no failure code), ``cmd`` is the
        argv list, and ``stderr`` is None (no error stream involved).
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="not json")
            with pytest.raises(GhCommandError) as excinfo:
                gh_api("repos/foo/bar")
        err = excinfo.value
        assert err.cmd == ["gh", "api", "repos/foo/bar"]
        assert err.returncode is None
        assert err.stderr is None

    @pytest.mark.unit
    def test_str_message_still_human_readable(self):
        """Backward compat: existing consumers wrap with
        ``raise RuntimeError(str(exc))``. The string message must
        still surface the original failure reason.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(1, stderr="boom")
            with pytest.raises(GhCommandError) as excinfo:
                gh_api("repos/foo/bar")
        assert "boom" in str(excinfo.value)


class TestGhGraphql:
    """Scenarios for gh_graphql()."""

    @pytest.mark.unit
    def test_returns_parsed_json_on_success(self):
        """Given gh exits 0 with JSON,
        When gh_graphql is called,
        Then the parsed payload is returned.
        """
        payload = {"data": {"repository": {"id": "node1"}}}
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout=json.dumps(payload))
            result = gh_graphql("query { repository { id } }")
        assert result == payload

    @pytest.mark.unit
    def test_passes_variables_as_field_args(self):
        """Given variables dict,
        When gh_graphql is called,
        Then each variable is appended as ``-f key=value``.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            gh_graphql("query($x: String) { x }", variables={"x": "hi"})
        argv = run.call_args[0][0]
        # Strings use -f (raw-field), value preserved verbatim.
        assert "-f" in argv
        assert "x=hi" in argv

    @pytest.mark.unit
    def test_int_variable_uses_typed_field(self):
        """S2 (#484): GraphQL Int! variables.
        Given an int value,
        When gh_graphql is called,
        Then the value is passed via ``-F key=<n>`` so ``gh`` parses
        it as a JSON number for the underlying GraphQL Int type.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            gh_graphql("query($n: Int!) { n }", variables={"n": 42})
        argv = run.call_args[0][0]
        assert "-F" in argv
        assert "n=42" in argv

    @pytest.mark.unit
    def test_bool_variable_uses_typed_field_lowercase(self):
        """S2 (#484): GraphQL Boolean! variables.
        Given a Python bool,
        When gh_graphql is called,
        Then the value is rendered as JSON-style ``true``/``false``
        and passed via ``-F`` so ``gh`` parses it as a Boolean.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            gh_graphql(
                "query($v: Boolean!) { v }",
                variables={"v": True, "w": False},
            )
        argv = run.call_args[0][0]
        assert "-F" in argv
        assert "v=true" in argv
        assert "w=false" in argv

    @pytest.mark.unit
    def test_none_variable_uses_typed_field_null(self):
        """S2 (#484): GraphQL nullable variables.
        Given a Python None,
        When gh_graphql is called,
        Then the value is rendered as ``null`` and passed via
        ``-F`` so ``gh`` parses it as a JSON null.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            gh_graphql("query($n: String) { n }", variables={"n": None})
        argv = run.call_args[0][0]
        assert "-F" in argv
        assert "n=null" in argv

    @pytest.mark.unit
    def test_float_variable_uses_typed_field(self):
        """S2 (#484): GraphQL Float variables.
        Given a Python float,
        When gh_graphql is called,
        Then the value is rendered as a numeric string and passed
        via ``-F``.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(0, stdout="{}")
            gh_graphql("query($r: Float!) { r }", variables={"r": 3.14})
        argv = run.call_args[0][0]
        assert "-F" in argv
        assert "r=3.14" in argv

    @pytest.mark.unit
    def test_raises_on_non_zero_exit(self):
        """Given gh exits non-zero,
        When gh_graphql is called,
        Then GhCommandError is raised.
        """
        with patch("subprocess.run") as run:
            run.return_value = _make_completed(2, stderr="bad query")
            with pytest.raises(GhCommandError) as excinfo:
                gh_graphql("query { malformed")
        assert "bad query" in str(excinfo.value)
