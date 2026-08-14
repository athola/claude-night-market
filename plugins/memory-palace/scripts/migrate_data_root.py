#!/usr/bin/env python3
"""Merge version-stranded palace data into the persistent root.

Hooks used to resolve their data directory from ``__file__``, which in an
install means ``~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/``.
Every update started a fresh tree and abandoned the previous one in
place. Issue #661 measured it twice: 200 staged captures under 1.9.16 on
the machine that filed the report, 1,470 under 1.9.17 and 2,491 under
1.9.18 on the machine that fixed it. Nothing was corrupted or deleted.
The files simply stopped having an address anyone held.

``memory_palace.paths`` fixes new writes. It cannot fix the trees already
written, and it deliberately does not try. Every stranded capture carries
``status: pending_review``, so merging one tree into another decides what
a person will be asked to curate. That is an operator's call, so it lives
in a script they run rather than in a hook that runs itself.

Three properties make the merge safe to attempt:

- It reports by default. ``--apply`` is required to write anything.
- It copies. The source tree is never deleted, so a merge judged wrong
  afterwards can be walked back by hand.
- It never overwrites. A destination file that already exists wins, and
  the source is reported as a conflict rather than resolved silently.

The capture index is excluded on purpose. Two indexes that disagree about
an entry cannot be reconciled by choosing bytes, and picking one loses
whatever the other knew. ``build_indexes.py`` regenerates the index from
the captures on disk, which is the answer that cannot be wrong, so the
plan asks for that instead.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPT_DIR.parent

if str(PLUGIN_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT / "src"))

from memory_palace.paths import user_data_dir  # noqa: E402 - needs sys.path above

DEFAULT_PLUGINS_DIR = Path.home() / ".claude" / "plugins"
DEFAULT_PLUGIN = "memory-palace"

#: Regenerated from the captures rather than merged. See module docstring.
_EXCLUDED_NAMES = frozenset({"memory-palace-index.yaml"})

#: Conflicts listed before the report truncates. A plan over the trees on
#: the machine this was written on reports six; a pathological one should
#: not bury the rebuild instruction under its own output.
MAX_LISTED_CONFLICTS = 10


@dataclass(frozen=True)
class Copy:
    """One file to copy, and the version tree it was found in."""

    source: Path
    relative: Path
    version: str


@dataclass(frozen=True)
class Conflict:
    """A file that was not copied, and why an operator should look."""

    source: Path
    relative: Path
    reason: str


@dataclass
class Plan:
    """What a migration would do, before it does any of it."""

    destination: Path
    copies: list[Copy] = field(default_factory=list)
    conflicts: list[Conflict] = field(default_factory=list)
    rebuild_index: bool = False

    def render(self) -> str:
        """Return a report an operator can check before applying."""
        if not self.copies and not self.conflicts:
            return "Nothing stranded: no version-scoped data found."

        lines = [
            f"Destination: {self.destination}",
            f"Files to copy: {len(self.copies)}",
        ]
        by_version: dict[str, int] = {}
        for item in self.copies:
            by_version[item.version] = by_version.get(item.version, 0) + 1
        for version in sorted(by_version, key=_version_key):
            lines.append(f"  from {version}: {by_version[version]}")

        if self.conflicts:
            lines.append(
                f"Conflicts (left in place, not copied): {len(self.conflicts)}"
            )
            for conflict in self.conflicts[:MAX_LISTED_CONFLICTS]:
                lines.append(f"  {conflict.relative}: {conflict.reason}")
            if len(self.conflicts) > MAX_LISTED_CONFLICTS:
                remaining = len(self.conflicts) - MAX_LISTED_CONFLICTS
                lines.append(f"  ... and {remaining} more")

        if self.rebuild_index:
            lines.append(
                "After applying, rebuild the capture index: "
                "python3 scripts/build_indexes.py"
            )
        return "\n".join(lines)


def _version_key(version: str) -> tuple[int, ...]:
    """Sort versions numerically so 1.9.9 ranks below 1.9.17.

    Non-numeric segments sort as -1, which keeps a pre-release below the
    release it precedes and keeps the comparison total either way.
    """
    return tuple(int(part) if part.isdigit() else -1 for part in version.split("."))


def _file_hash(path: Path) -> str:
    """Return a content digest, used only to tell a duplicate from a clash."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _version_trees(plugins_dir: Path, plugin: str) -> list[tuple[str, Path]]:
    """Return ``(version, data_dir)`` for every install tree with data.

    Newest first, so the highest version is the one that claims a
    relative path when two trees disagree about its contents.
    """
    cache = plugins_dir / "cache"
    if not cache.is_dir():
        return []

    trees: list[tuple[str, Path]] = []
    for marketplace in sorted(cache.iterdir()):
        version_root = marketplace / plugin
        if not version_root.is_dir():
            continue
        for version_dir in sorted(version_root.iterdir()):
            data_dir = version_dir / "data"
            if data_dir.is_dir():
                trees.append((version_dir.name, data_dir))
    trees.sort(key=lambda pair: _version_key(pair[0]), reverse=True)
    return trees


def _has_stranded_index(plugins_dir: Path, plugin: str) -> bool:
    """Report whether any install tree carries a capture index."""
    cache = plugins_dir / "cache"
    if not cache.is_dir():
        return False
    for name in _EXCLUDED_NAMES:
        if any(cache.glob(f"*/{plugin}/*/hooks/{name}")):
            return True
    return False


def plan_migration(plugins_dir: Path, plugin: str = DEFAULT_PLUGIN) -> Plan:
    """Return what a migration would copy, without copying anything.

    Trees are read newest first. The first tree to claim a relative path
    supplies the copy; a later tree holding the same bytes is a duplicate
    and is dropped, while one holding different bytes is a conflict and
    is reported. A path that already exists in the destination is always
    a conflict: the persistent root is the live palace, and overwriting
    it would be this bug pointed the other way.
    """
    trees = _version_trees(plugins_dir, plugin)
    if not trees:
        return Plan(destination=plugins_dir / "data")

    # Resolved from a tree that actually exists rather than assembled
    # from parts. The marketplace name is part of the destination
    # directory, and only the discovered path knows it.
    destination = user_data_dir(trees[0][1].parent)
    plan = Plan(
        destination=destination,
        rebuild_index=_has_stranded_index(plugins_dir, plugin),
    )

    claimed: dict[Path, Copy] = {}
    for version, data_dir in trees:
        for source in sorted(p for p in data_dir.rglob("*") if p.is_file()):
            if source.name in _EXCLUDED_NAMES:
                continue
            relative = source.relative_to(data_dir)

            existing = destination / relative
            if existing.exists():
                plan.conflicts.append(
                    Conflict(source, relative, "already present in the live palace")
                )
                continue

            claim = claimed.get(relative)
            if claim is None:
                claim = Copy(source, relative, version)
                claimed[relative] = claim
                plan.copies.append(claim)
                continue

            if _file_hash(source) != _file_hash(claim.source):
                plan.conflicts.append(
                    Conflict(
                        source,
                        relative,
                        f"differs from the copy taken from {claim.version}",
                    )
                )

    return plan


def apply_plan(plan: Plan) -> int:
    """Copy every file the plan claimed. Returns the number written."""
    written = 0
    for item in plan.copies:
        target = plan.destination / item.relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            continue
        shutil.copy2(item.source, target)
        written += 1
    return written


def main(argv: list[str] | None = None) -> int:
    """Report the plan, and apply it only when asked."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        default=DEFAULT_PLUGINS_DIR,
        help=f"Claude Code plugins directory (default: {DEFAULT_PLUGINS_DIR})",
    )
    parser.add_argument(
        "--plugin",
        default=DEFAULT_PLUGIN,
        help=f"Plugin name to migrate (default: {DEFAULT_PLUGIN})",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Copy the files. Without this the plan is only reported.",
    )
    args = parser.parse_args(argv)

    plan = plan_migration(args.plugins_dir, args.plugin)
    print(plan.render())

    if not plan.copies:
        return 0
    if not args.apply:
        print("\nDry run. Re-run with --apply to copy.")
        return 0

    written = apply_plan(plan)
    print(f"\nCopied {written} file(s). Source trees left in place.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
