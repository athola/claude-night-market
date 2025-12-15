"""Regression tests for cache interception catalog seeding."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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


def test_seed_script_populates_cache_catalog(tmp_path):
    """Test that seed script populates cache catalog."""
    module = _load_seed_module()
    keyword_index = tmp_path / "keyword-index.yaml"

    catalog = module.seed_cache_catalog(
        index_dir=tmp_path,
        fixture_path=FIXTURE_PATH,
        keyword_index=keyword_index,
    )

    cache_meta = catalog["metadata"]["cache_intercept"]
    assert cache_meta["curated_count"] >= MIN_CURATED
    assert len(catalog["entries"]) >= MIN_CURATED
    assert keyword_index.exists()
