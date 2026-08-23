#!/usr/bin/env python3
"""Delete plugin cache versions that nothing installed points at.

Claude Code installs a marketplace plugin by copying it into
``~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`` and
records the chosen directory in ``installed_plugins.json``. Updating a
plugin writes a new version directory and leaves the previous one on
disk, referenced by nothing.

For a marketplace whose source is a local directory the copy is a plain
one, not a git checkout, so it carries whatever the working tree holds.
In this repository that means each plugin ships its ``.venv`` and
``.mypy_cache`` along with its skills. Measured on 2026-08-23 that made
one cached plugin 217MB against roughly 10MB of actual content, and
three retained versions of twenty-two plugins came to 14GB. The plugin
format has no exclusion mechanism, no ``files`` field and no
``.claudeignore``, so nothing stops the copy. Pruning is what bounds it.

``installed_plugins.json`` is the only authority on what is in use. A
version directory absent from it is unreferenced and can be removed;
reinstalling from the marketplace restores it. The manifest is re-read
immediately before each delete rather than once at listing time,
because an update landing mid-run would otherwise make a live directory
look stale.

Run with ``--dry-run`` to list without deleting.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

DEFAULT_ROOT = Path.home() / ".claude" / "plugins"


def referenced_paths(plugins_root: Path) -> set[str]:
    """Every install path the manifest currently points at."""
    manifest = plugins_root / "installed_plugins.json"
    data = json.loads(manifest.read_text())
    paths: set[str] = set()
    for entries in data.get("plugins", {}).values():
        for entry in entries if isinstance(entries, list) else [entries]:
            path = entry.get("installPath")
            if path:
                paths.add(str(Path(path)))
    return paths


def unreferenced_versions(plugins_root: Path) -> list[Path]:
    """Version directories under the cache that nothing points at."""
    cache = plugins_root / "cache"
    if not cache.is_dir():
        return []
    live = referenced_paths(plugins_root)
    stale = [
        version
        for marketplace in sorted(cache.iterdir())
        if marketplace.is_dir()
        for plugin in sorted(marketplace.iterdir())
        if plugin.is_dir()
        for version in sorted(plugin.iterdir())
        if version.is_dir() and str(version) not in live
    ]
    return stale


def prune(plugins_root: Path, dry_run: bool = False) -> tuple[list[Path], list[Path]]:
    """Remove unreferenced versions. Returns (removed, skipped)."""
    removed: list[Path] = []
    skipped: list[Path] = []
    for version in unreferenced_versions(plugins_root):
        # Re-read the manifest per delete: an update landing mid-run
        # would otherwise let a now-live directory be removed.
        if str(version) in referenced_paths(plugins_root):
            skipped.append(version)
            continue
        if not dry_run:
            shutil.rmtree(version)
        removed.append(version)
    return removed, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="list without deleting")
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=DEFAULT_ROOT,
        help=f"plugin directory to prune (default: {DEFAULT_ROOT})",
    )
    args = parser.parse_args(argv)

    if not (args.plugins_root / "installed_plugins.json").is_file():
        print(f"no installed_plugins.json under {args.plugins_root}", file=sys.stderr)
        return 1

    removed, skipped = prune(args.plugins_root, dry_run=args.dry_run)
    verb = "would remove" if args.dry_run else "removed"
    for path in removed:
        print(f"{verb}: {path}")
    for path in skipped:
        print(f"skipped, became live mid-run: {path}")
    print(f"{verb} {len(removed)} unreferenced version(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
