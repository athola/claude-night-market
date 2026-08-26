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


def test_a_relative_plugins_root_does_not_condemn_every_live_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Scenario: The root is given as a relative path
    Given a manifest whose installPath entries are absolute
    When the same root is passed in relative form
    Then the live version is still recognized as live

    ``referenced_paths`` stores the manifest's own strings while
    ``unreferenced_versions`` builds its strings from ``iterdir()`` on
    whatever root it was handed. Neither side was resolved, so the two
    forms of one path never compared equal and every live version was
    classified unreferenced. Without ``--dry-run`` that is an rmtree of
    a live plugin, printed as "removed 1 unreferenced version(s)".
    """
    root = _make_root(tmp_path, live=["alpha/1.0.0"], stale=[])
    monkeypatch.chdir(tmp_path)

    assert prune_plugin_cache.unreferenced_versions(Path("plugins")) == []


def test_a_manifest_without_a_plugins_key_stops_the_prune(tmp_path: Path) -> None:
    """
    Scenario: The manifest parses but carries no "plugins" key
    Given schema drift or a partial write
    When the pruner reads it
    Then it raises rather than reporting that nothing is referenced

    ``data.get("plugins", {})`` made an unreadable authority into an
    authority saying nothing, so every cached version became deletable.
    The docstring calls this file "the only authority on what is in
    use"; a malformed one should stop the prune, not authorize a total
    one. The stakes are the 14GB the module docstring cites, restored
    only by reinstalling everything.
    """
    root = _make_root(tmp_path, live=["alpha/1.0.0"], stale=[])
    (root / "installed_plugins.json").write_text(json.dumps({"version": 2}))

    with pytest.raises(KeyError, match="plugins"):
        prune_plugin_cache.referenced_paths(root)


def test_the_mid_run_recheck_also_compares_canonical_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Scenario: A version becomes live mid-run under a relative root
    Given the pruner listed it as stale before the manifest changed
    When the per-delete re-read runs
    Then it is skipped rather than deleted

    The re-read is the guard against an update landing mid-run, and it
    compared a raw ``str(version)`` against manifest paths. That is the
    same unresolved comparison as the listing walk, so under a relative
    root the guard silently stopped guarding: the directory it was meant
    to rescue would be removed.
    """
    root = _make_root(tmp_path, live=["beta/1.0.0"], stale=["alpha/1.0.0"])
    monkeypatch.chdir(tmp_path)
    relative = Path("plugins")
    version = (root / "cache" / "mk" / "alpha" / "1.0.0").resolve()

    original = prune_plugin_cache.referenced_paths

    def _goes_live(plugins_root: Path) -> set[str]:
        # First call (the listing walk) sees nothing live; the per-delete
        # re-read sees the install that landed in between.
        calls.append(1)
        if len(calls) == 1:
            return original(plugins_root)
        return original(plugins_root) | {str(version)}

    calls: list[int] = []
    monkeypatch.setattr(prune_plugin_cache, "referenced_paths", _goes_live)

    removed, skipped = prune_plugin_cache.prune(relative, dry_run=False)

    assert removed == []
    assert skipped == [Path("plugins/cache/mk/alpha/1.0.0")]
    assert version.is_dir()


def test_a_manifest_pointing_somewhere_else_stops_the_prune(tmp_path: Path) -> None:
    """
    Scenario: The manifest names installs, none under this cache
    Given a root that is not the one the manifest was written for
    When versions are listed
    Then it raises rather than reporting every version stale

    The reading the pruner would otherwise take -- "nothing here is
    referenced, so delete all of it" -- is the most destructive one
    available, and a mismatched ``--plugins-root`` produces it silently.
    """
    root = _make_root(tmp_path, live=["alpha/1.0.0"], stale=[])
    manifest = json.loads((root / "installed_plugins.json").read_text())
    manifest["plugins"] = {"alpha@mk": [{"installPath": str(tmp_path / "elsewhere")}]}
    (root / "installed_plugins.json").write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match="Refusing to treat that as"):
        prune_plugin_cache.unreferenced_versions(root)


def test_an_empty_manifest_still_prunes(tmp_path: Path) -> None:
    """
    Scenario: Every plugin has been uninstalled
    Given a manifest naming no installs at all
    When versions are listed
    Then the leftover directories are reported stale

    The counterpart to the test above, and the reason the refusal keys
    on "names installs, none of them here" rather than on an empty
    intersection. An operator who uninstalled everything has exactly
    this manifest, and pruning is what they came for.
    """
    root = _make_root(tmp_path, live=[], stale=["alpha/1.0.0"])

    stale = prune_plugin_cache.unreferenced_versions(root)

    assert [p.name for p in stale] == ["1.0.0"]
