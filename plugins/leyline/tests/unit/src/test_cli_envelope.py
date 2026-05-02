"""Tests for leyline.cli_envelope -- standard CLI JSON envelope.

Feature: Standardize the success/error envelope shape used by
night-market CLI scripts (D-13).

As a plugin author writing a CLI script with --output-json
I want one canonical helper that produces the success/error
envelope shape
So that test_generator, quality_checker, safe_replacer (and
future scripts) cannot drift on key names, ordering, or shape.
"""

from __future__ import annotations

import json

import pytest

from leyline.cli_envelope import error_envelope, success_envelope


class TestSuccessEnvelope:
    """Scenarios for success_envelope()."""

    @pytest.mark.unit
    def test_wraps_dict_payload_with_success_true(self):
        """Given a dict payload,
        When success_envelope is called,
        Then it returns {"success": True, "data": payload}.
        """
        payload = {"file": "x.py", "tests_added": 3}
        envelope = success_envelope(payload)
        assert envelope == {"success": True, "data": payload}

    @pytest.mark.unit
    def test_wraps_list_payload(self):
        """Given a list payload,
        When success_envelope is called,
        Then data field carries the list.
        """
        envelope = success_envelope([1, 2, 3])
        assert envelope["success"] is True
        assert envelope["data"] == [1, 2, 3]

    @pytest.mark.unit
    def test_wraps_none_payload(self):
        """Given None,
        When success_envelope is called,
        Then data is None and success is True.
        """
        envelope = success_envelope(None)
        assert envelope == {"success": True, "data": None}

    @pytest.mark.unit
    def test_envelope_is_json_serializable(self):
        """Given a dict-of-primitives payload,
        When the envelope is dumped to JSON,
        Then round-trip preserves the structure.
        """
        envelope = success_envelope({"x": 1})
        round_trip = json.loads(json.dumps(envelope))
        assert round_trip == envelope


class TestErrorEnvelope:
    """Scenarios for error_envelope()."""

    @pytest.mark.unit
    def test_wraps_message_with_success_false(self):
        """Given an error message string,
        When error_envelope is called,
        Then it returns {"success": False, "error": message}.
        """
        envelope = error_envelope("Permission denied: /etc/foo")
        assert envelope == {
            "success": False,
            "error": "Permission denied: /etc/foo",
        }

    @pytest.mark.unit
    def test_envelope_is_json_serializable(self):
        """Given an error envelope,
        When dumped to JSON,
        Then round-trip preserves the structure.
        """
        envelope = error_envelope("oops")
        round_trip = json.loads(json.dumps(envelope))
        assert round_trip == envelope

    @pytest.mark.unit
    def test_success_and_error_envelopes_share_success_key(self):
        """Given one success and one error envelope,
        When inspected,
        Then both expose a 'success' bool key (so downstream tools
        can dispatch with one check).
        """
        ok = success_envelope({})
        err = error_envelope("x")
        assert ok["success"] is True
        assert err["success"] is False
