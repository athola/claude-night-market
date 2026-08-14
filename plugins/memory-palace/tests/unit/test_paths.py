"""Runtime data must outlive the plugin version that wrote it.

Hooks execute from ``~/.claude/plugins/cache/<marketplace>/<plugin>/
<version>/``, so a data root derived from ``__file__`` is version
scoped. Installing a new version creates a new tree and everything the
previous one accumulated stops being reachable. Issue #661 measured it:
1,470 staged captures stranded under 1.9.17 while the version-
independent directory Claude Code provisions for exactly this purpose
sat empty. The filing machine reported 200 under 1.9.16; the counts
differ per machine, the defect does not.

The captures carry ``status: pending_review``, so they were awaiting
curation at the moment they were orphaned. That is the whole defect:
not corruption, not deletion, just an address nobody holds any more.

Feature: user data resolves to a location that survives an update.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory_palace.paths import persistent_root, user_data_dir


def _cache_tree(root: Path, version: str = "1.9.18") -> Path:
    """Build the directory shape a real plugin install has."""
    plugin_root = (
        root
        / ".claude"
        / "plugins"
        / "cache"
        / "claude-night-market"
        / "memory-palace"
        / version
    )
    plugin_root.mkdir(parents=True)
    return plugin_root


class TestInstalledPlugin:
    """A plugin running from the versioned cache tree."""

    def test_data_root_is_outside_the_version_directory(self, tmp_path: Path) -> None:
        """GIVEN a hook running from cache/<marketplace>/<plugin>/<version>
        WHEN the user data root is resolved
        THEN it is not under the version directory
        AND so an update cannot strand what was written there.
        """
        plugin_root = _cache_tree(tmp_path)

        resolved = user_data_dir(plugin_root)

        assert plugin_root not in resolved.parents
        assert "1.9.18" not in resolved.parts

    def test_data_root_is_the_directory_claude_code_provisions(
        self, tmp_path: Path
    ) -> None:
        """GIVEN the same install
        WHEN the root is resolved
        THEN it is ``plugins/data/<plugin>-<marketplace>/``, the location
        Claude Code already creates, rather than a path of our own.
        """
        plugin_root = _cache_tree(tmp_path)

        resolved = persistent_root(plugin_root)

        expected = (
            tmp_path
            / ".claude"
            / "plugins"
            / "data"
            / "memory-palace-claude-night-market"
        )
        assert resolved == expected

    def test_two_versions_resolve_to_one_root(self, tmp_path: Path) -> None:
        """GIVEN two installed versions of the same plugin
        WHEN each resolves its data root
        THEN both name the same directory, which is the property the
        whole change exists to establish.
        """
        old = _cache_tree(tmp_path, "1.9.17")
        new = _cache_tree(tmp_path, "1.9.18")

        assert persistent_root(old) == persistent_root(new)


class TestSourceCheckout:
    """A developer or CI running from the repository itself."""

    def test_checkout_keeps_its_own_data_directory(self, tmp_path: Path) -> None:
        """GIVEN a plugin root that is not inside a plugins/cache tree
        WHEN the root is resolved
        THEN it stays ``<plugin_root>/data``.

        Tests and local development read fixtures from the checkout. If
        this redirected to the user's real palace, a test run would read
        and write the operator's captures.
        """
        plugin_root = tmp_path / "repo" / "plugins" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert persistent_root(plugin_root) == plugin_root
        assert user_data_dir(plugin_root) == plugin_root / "data"

    def test_cache_lookalike_without_a_marketplace_is_not_treated_as_installed(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a path containing 'cache' but not the install shape
        WHEN the root is resolved
        THEN it falls back to the local data directory rather than
        inventing a marketplace name from whatever sits above it.
        """
        plugin_root = tmp_path / "cache" / "memory-palace"
        plugin_root.mkdir(parents=True)

        assert user_data_dir(plugin_root) == plugin_root / "data"


class TestOverride:
    """An explicit environment override wins over both branches."""

    def test_env_var_overrides_resolution(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GIVEN MEMORY_PALACE_DATA_DIR is set
        WHEN the root is resolved
        THEN that value is used verbatim.

        The migration tool and any operator moving a palace need one
        lever that does not depend on where the code happens to live.
        """
        plugin_root = _cache_tree(tmp_path)
        override = tmp_path / "elsewhere"
        monkeypatch.setenv("MEMORY_PALACE_DATA_DIR", str(override))

        assert persistent_root(plugin_root) == override


class TestStoredAtCompatibility:
    """The index records paths relative to the root this module returns."""

    def test_relative_stored_at_keeps_its_shape_in_both_layouts(
        self, tmp_path: Path
    ) -> None:
        """GIVEN a capture written under the data directory
        WHEN its path is expressed relative to the persistent root
        THEN it reads ``data/staging/<file>`` in an install exactly as it
        does in a checkout.

        Index entries are resolved as ``root / stored_at``. If the two
        layouts disagreed on that string, every pre-existing entry would
        report as an orphan the first time a migrated palace was read.
        """
        installed = _cache_tree(tmp_path)
        checkout = tmp_path / "repo" / "plugins" / "memory-palace"
        checkout.mkdir(parents=True)

        shapes = {
            str(
                (user_data_dir(root) / "staging" / "x.md").relative_to(
                    persistent_root(root)
                )
            )
            for root in (installed, checkout)
        }

        assert shapes == {"data/staging/x.md"}
