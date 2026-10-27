"""Find a sibling plugin in the repo checkout and in the installed cache.

Scripts found leyline with ``Path(__file__).parents[2] / "leyline"``,
which only exists in the repo (``plugins/<name>``). Claude Code installs
plugins as ``cache/<marketplace>/<plugin>/<version>/``, where that path
names a directory inside the calling plugin, so every leyline-backed
feature turned itself off in real installs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from leyline.sibling_plugins import (
    add_sibling_src_to_path,
    sibling_plugin_dir,
    version_key,
)


def _plugin(root: Path) -> Path:
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "scripts").mkdir()
    script = root / "scripts" / "tool.py"
    script.write_text("")
    return script


@pytest.mark.unit
def test_repo_layout_resolves_to_plugins_sibling(tmp_path: Path) -> None:
    script = _plugin(tmp_path / "plugins" / "abstract")
    (tmp_path / "plugins" / "leyline" / ".claude-plugin").mkdir(parents=True)
    assert sibling_plugin_dir(script, "leyline") == tmp_path / "plugins" / "leyline"


@pytest.mark.unit
def test_cache_layout_resolves_to_newest_installed_version(tmp_path: Path) -> None:
    market = tmp_path / "cache" / "claude-night-market"
    script = _plugin(market / "abstract" / "1.10.0")
    for version in ("1.9.21", "1.10.0", "1.2.0"):
        (market / "leyline" / version / ".claude-plugin").mkdir(parents=True)
    assert sibling_plugin_dir(script, "leyline") == market / "leyline" / "1.10.0"


@pytest.mark.unit
def test_missing_sibling_returns_none(tmp_path: Path) -> None:
    script = _plugin(tmp_path / "plugins" / "abstract")
    assert sibling_plugin_dir(script, "leyline") is None


@pytest.mark.unit
def test_works_from_a_nested_source_file(tmp_path: Path) -> None:
    """src/<pkg>/module.py sits two levels deeper than scripts/tool.py."""
    _plugin(tmp_path / "plugins" / "abstract")
    nested = tmp_path / "plugins" / "abstract" / "src" / "abstract" / "tokens.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("")
    (tmp_path / "plugins" / "leyline" / ".claude-plugin").mkdir(parents=True)
    assert sibling_plugin_dir(nested, "leyline") == tmp_path / "plugins" / "leyline"


@pytest.mark.unit
def test_file_outside_any_plugin_has_no_sibling(tmp_path: Path) -> None:
    stray = tmp_path / "loose" / "tool.py"
    stray.parent.mkdir()
    stray.write_text("")
    assert sibling_plugin_dir(stray, "leyline") is None


@pytest.mark.unit
def test_sibling_absent_from_both_layouts_is_none(tmp_path: Path) -> None:
    script = _plugin(tmp_path / "plugins" / "abstract")
    (tmp_path / "plugins" / "leyline").mkdir()  # no manifest: not a plugin
    assert sibling_plugin_dir(script, "leyline") is None


@pytest.fixture
def isolated_sys_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """The helper mutates sys.path; keep that out of the rest of the suite."""
    monkeypatch.setattr(sys, "path", list(sys.path))


@pytest.mark.unit
@pytest.mark.usefixtures("isolated_sys_path")
def test_add_src_puts_repo_sibling_src_first_on_sys_path(tmp_path: Path) -> None:
    script = _plugin(tmp_path / "plugins" / "abstract")
    (tmp_path / "plugins" / "leyline" / ".claude-plugin").mkdir(parents=True)
    expected = tmp_path / "plugins" / "leyline" / "src"
    assert add_sibling_src_to_path(script, "leyline") == expected
    assert sys.path[0] == str(expected)


@pytest.mark.unit
@pytest.mark.usefixtures("isolated_sys_path")
def test_add_src_uses_newest_cached_version_in_install_layout(tmp_path: Path) -> None:
    market = tmp_path / "cache" / "claude-night-market"
    script = _plugin(market / "abstract" / "1.10.0")
    for version in ("1.9.21", "1.10.0"):
        (market / "leyline" / version / ".claude-plugin").mkdir(parents=True)
    expected = market / "leyline" / "1.10.0" / "src"
    assert add_sibling_src_to_path(script, "leyline") == expected
    assert sys.path[0] == str(expected)


@pytest.mark.unit
@pytest.mark.usefixtures("isolated_sys_path")
def test_add_src_falls_back_to_plugins_dir_at_any_nesting_depth(
    tmp_path: Path,
) -> None:
    """A missing sibling resolves beside the caller's plugin, not parents[N]."""
    _plugin(tmp_path / "plugins" / "abstract")
    nested = tmp_path / "plugins" / "abstract" / "src" / "abstract" / "tokens.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("")
    expected = tmp_path / "plugins" / "leyline" / "src"
    assert add_sibling_src_to_path(nested, "leyline") == expected
    assert sys.path[0] == str(expected)


@pytest.mark.unit
@pytest.mark.usefixtures("isolated_sys_path")
def test_add_src_without_manifest_falls_back_to_plugins_ancestor(
    tmp_path: Path,
) -> None:
    script = tmp_path / "plugins" / "abstract" / "scripts" / "tool.py"
    script.parent.mkdir(parents=True)
    script.write_text("")
    expected = tmp_path / "plugins" / "leyline" / "src"
    assert add_sibling_src_to_path(script, "leyline") == expected
    assert sys.path[0] == str(expected)


@pytest.mark.unit
@pytest.mark.usefixtures("isolated_sys_path")
def test_add_src_outside_any_plugin_inserts_path_beside_the_file(
    tmp_path: Path,
) -> None:
    """Nothing resolves; the caller's ImportError branch then degrades."""
    stray = tmp_path / "loose" / "tool.py"
    stray.parent.mkdir()
    stray.write_text("")
    expected = tmp_path / "loose" / "leyline" / "src"
    assert add_sibling_src_to_path(stray, "leyline") == expected
    assert sys.path[0] == str(expected)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("installed", "expected"),
    [
        (("1.9.21", "2.0.0-rc1"), "2.0.0-rc1"),
        (("2.0.0-rc1", "2.0.0"), "2.0.0"),
        (("1.10.0", "latest", "a1b2c3d"), "1.10.0"),
        (("latest", "a1b2c3d"), "latest"),
    ],
    ids=[
        "prerelease-beats-older-release",
        "release-beats-its-prerelease",
        "numeric-beats-named",
        "all-named-sort-by-name",
    ],
)
def test_cache_pick_orders_prereleases_and_named_versions(
    tmp_path: Path, installed: tuple[str, ...], expected: str
) -> None:
    market = tmp_path / "cache" / "claude-night-market"
    script = _plugin(market / "abstract" / "1.10.0")
    for version in installed:
        (market / "leyline" / version / ".claude-plugin").mkdir(parents=True)
    assert sibling_plugin_dir(script, "leyline") == market / "leyline" / expected


def test_version_key_orders_every_shape_of_cache_directory_name() -> None:
    """version_key is public because minister and memory-palace vendor it.

    GIVEN cache directory names that are releases, a pre-release and a
    name with no version
    WHEN they are sorted by version_key
    THEN the unversioned name sorts first, 1.10.0 follows 1.9.21, and
    1.10.1-rc1 sits between 1.10.0 and 1.10.1.
    """
    names = ["1.10.1", "latest", "1.10.1-rc1", "1.9.21", "1.10.0"]

    ordered = [p.name for p in sorted((Path(n) for n in names), key=version_key)]

    assert ordered == ["latest", "1.9.21", "1.10.0", "1.10.1-rc1", "1.10.1"]


def test_a_post_release_sorts_after_its_release() -> None:
    """version_key follows PEP 440 for post-releases.

    GIVEN a release and its post-release
    WHEN they are sorted by version_key
    THEN the post-release comes after the release and before the next
    release, as packaging.version orders them.
    """
    names = ["1.10.1", "1.10.0.post1", "1.10.0", "1.10.0-post2"]

    ordered = [p.name for p in sorted((Path(n) for n in names), key=version_key)]

    assert ordered == ["1.10.0", "1.10.0.post1", "1.10.0-post2", "1.10.1"]
