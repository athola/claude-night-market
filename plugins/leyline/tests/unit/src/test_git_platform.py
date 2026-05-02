"""Tests for leyline.git_platform Python wrapper (AR-30).

Feature: One Python module exposing the contract of the
``leyline:git-platform`` skill so plugin scripts no longer
reinvent ``["gh", "api", ...]`` argv plus error handling plus
JSON parsing in seven places.

As a plugin script
I want ``gh_api()`` and ``gh_graphql()`` helpers
So that gh-cli interactions are routed through one tested
shim (and a future GitLab/Bitbucket switch lives in one place).
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
        # Look for the -f x=hi pair
        joined = " ".join(argv)
        assert "-f x=hi" in joined or "x=hi" in argv

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
