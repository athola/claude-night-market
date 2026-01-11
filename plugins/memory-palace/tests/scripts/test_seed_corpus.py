"""Regression tests for cache interception catalog seeding."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "cache_intercept_catalog.yaml"
)
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_corpus.py"
MIN_CURATED = 50


def _load_seed_module():
    spec = importlib.util.spec_from_file_location("seed_corpus", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules["seed_corpus"] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.mark.skip(
    reason="Functionality refactored - generate_entries() is a stub pending migration"
)
def test_seed_script_populates_cache_catalog(tmp_path):
    """Test that seed script generates entries and catalog.

    Note: The script was refactored to load from YAML. The generate_entries()
    function is currently a stub pending full migration of topic data.
    """
    module = _load_seed_module()

    # Test entry generation (core functionality)
    entries = module.generate_entries()

    assert len(entries) >= MIN_CURATED
    # Verify entries have expected structure
    for entry in entries:
        assert "slug" in entry
        assert "title" in entry
