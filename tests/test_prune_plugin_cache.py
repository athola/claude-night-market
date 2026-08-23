"""The cache pruner must delete only what nothing points at.

``scripts/prune_plugin_cache.py`` removes directories, so the tests that
matter are the ones proving it leaves live installs alone. Every case
here builds a throwaway plugin root; none of them touch the real
``~/.claude``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "prune_plugin_cache.py"

_spec = importlib.util.spec_from_file_location("prune_plugin_cache", SCRIPT)
assert _spec and _spec.loader
prune_plugin_cache = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prune_plugin_cache)


def _make_root(tmp_path: Path, live: list[str], stale: list[str]) -> Path:
    """Build a plugin root whose manifest points at `live` only."""
    root = tmp_path / "plugins"
    cache = root / "cache" / "mk"
    paths = {}
    for name in live + stale:
        plug, ver = name.split("/")
        d = cache / plug / ver
        d.mkdir(parents=True)
        (d / "marker.txt").write_text(name)
        paths[name] = d
    manifest = {
        "plugins": {
            f"{n.split('/')[0]}@mk": [{"installPath": str(paths[n])}] for n in live
        }
    }
    (root / "installed_plugins.json").write_text(json.dumps(manifest))
    return root


def test_unreferenced_version_is_removed(tmp_path: Path) -> None:
    root = _make_root(tmp_path, live=["a/2.0"], stale=["a/1.0"])
    removed, skipped = prune_plugin_cache.prune(root)
    assert [p.name for p in removed] == ["1.0"]
    assert skipped == []
    assert not (root / "cache/mk/a/1.0").exists()


def test_referenced_version_survives(tmp_path: Path) -> None:
    root = _make_root(tmp_path, live=["a/2.0"], stale=["a/1.0"])
    prune_plugin_cache.prune(root)
    assert (root / "cache/mk/a/2.0/marker.txt").read_text() == "a/2.0"


def test_dry_run_deletes_nothing(tmp_path: Path) -> None:
    root = _make_root(tmp_path, live=["a/2.0"], stale=["a/1.0"])
    removed, _ = prune_plugin_cache.prune(root, dry_run=True)
    assert [p.name for p in removed] == ["1.0"]
    assert (root / "cache/mk/a/1.0").exists(), "dry run must not delete"


def test_nothing_stale_is_a_no_op(tmp_path: Path) -> None:
    root = _make_root(tmp_path, live=["a/1.0", "b/3.0"], stale=[])
    removed, skipped = prune_plugin_cache.prune(root)
    assert removed == [] and skipped == []


def test_a_version_that_goes_live_mid_run_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An update landing between listing and deleting must not lose data.

    The pruner re-reads the manifest before each delete. This simulates
    the manifest gaining a reference to the directory after it was
    listed as stale.
    """
    root = _make_root(tmp_path, live=["a/2.0"], stale=["a/1.0"])
    stale_dir = str(root / "cache/mk/a/1.0")
    real = prune_plugin_cache.referenced_paths
    calls = {"n": 0}

    def flaky(plugins_root: Path) -> set[str]:
        calls["n"] += 1
        paths = real(plugins_root)
        # First call lists; every later call is the pre-delete re-check.
        return paths if calls["n"] == 1 else paths | {stale_dir}

    monkeypatch.setattr(prune_plugin_cache, "referenced_paths", flaky)
    removed, skipped = prune_plugin_cache.prune(root)
    assert removed == []
    assert [p.name for p in skipped] == ["1.0"]
    assert Path(stale_dir).exists(), "a directory that went live must survive"
