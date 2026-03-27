"""Tests for add_model_hints script."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))

from add_model_hints import get_model_hint


class TestModelHintMapping:
    """
    Feature: Model hint derivation from skill complexity

    As a plugin developer
    I want skills routed to appropriate models by complexity
    So that simple tasks don't waste tokens on expensive models
    """

    @pytest.mark.unit
    def test_low_complexity_maps_to_fast(self):
        """
        Scenario: Low complexity skill gets fast hint
        Given a skill with complexity "low"
        When model_hint is derived
        Then it should be "fast"
        """
        assert get_model_hint("some-skill", "low") == "fast"

    @pytest.mark.unit
    def test_basic_complexity_maps_to_fast(self):
        assert get_model_hint("some-skill", "basic") == "fast"

    @pytest.mark.unit
    def test_intermediate_maps_to_standard(self):
        assert get_model_hint("some-skill", "intermediate") == "standard"

    @pytest.mark.unit
    def test_advanced_maps_to_deep(self):
        assert get_model_hint("some-skill", "advanced") == "deep"

    @pytest.mark.unit
    def test_unknown_complexity_defaults_to_standard(self):
        assert get_model_hint("some-skill", "unknown-value") == "standard"

    @pytest.mark.unit
    def test_force_fast_overrides_complexity(self):
        """
        Scenario: commit-messages skill forced to fast
        Given a skill named "commit-messages" with complexity "intermediate"
        When model_hint is derived
        Then it should be "fast" (overridden)
        """
        assert get_model_hint("commit-messages", "intermediate") == "fast"

    @pytest.mark.unit
    def test_force_deep_overrides_complexity(self):
        assert get_model_hint("war-room", "intermediate") == "deep"
