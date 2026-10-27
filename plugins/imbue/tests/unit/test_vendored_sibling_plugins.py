"""imbue's vendored copy of leyline.sibling_plugins finds leyline.

deferred_capture.py resolves leyline through this copy. The canonical
module is tested in leyline, but the copy imbue ships is the code that
runs here, and a sync that broke it would turn deferred capture off in
an installed plugin without any test noticing.
"""

from __future__ import annotations

from pathlib import Path

from scripts._vendored_leyline_sibling_plugins import sibling_plugin_dir


def _plugin(path: Path) -> Path:
    (path / ".claude-plugin").mkdir(parents=True)
    return path


def test_repository_layout_finds_the_sibling_beside_this_plugin(tmp_path):
    imbue = _plugin(tmp_path / "plugins" / "imbue")
    leyline = _plugin(tmp_path / "plugins" / "leyline")
    caller = imbue / "scripts" / "deferred_capture.py"
    caller.parent.mkdir()
    caller.write_text("")
    assert sibling_plugin_dir(caller, "leyline") == leyline


def test_install_cache_layout_picks_the_newest_version(tmp_path):
    """A prerelease of a newer version outranks an older release, as in leyline."""
    cache = tmp_path / "cache" / "night-market"
    imbue = _plugin(cache / "imbue" / "1.10.0")
    for version in ("1.9.21", "1.10.0", "2.0.0-rc1"):
        _plugin(cache / "leyline" / version)
    (cache / "leyline" / "3.0.0").mkdir()  # no manifest: not an install
    assert sibling_plugin_dir(imbue / "x.py", "leyline") == (
        cache / "leyline" / "2.0.0-rc1"
    )


def test_missing_sibling_returns_none(tmp_path):
    imbue = _plugin(tmp_path / "plugins" / "imbue")
    assert sibling_plugin_dir(imbue / "x.py", "leyline") is None


def test_file_outside_any_plugin_returns_none(tmp_path):
    assert sibling_plugin_dir(tmp_path / "loose.py", "leyline") is None
