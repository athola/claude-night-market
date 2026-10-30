#!/usr/bin/env python3
"""Copy stdlib-only shared modules into plugins that cannot import them.

Plugin isolation forbids a cross-plugin import, so a plugin that must
work without leyline (or abstract) installed carries a copy. Some
consumers try the canonical module first and use the copy as a
fallback. The ``atomic_file`` and ``sibling_plugins`` consumers import
the copy unconditionally: adding a canonical-first import there would
add the cross-plugin import the copy exists to avoid. Copies kept by hand
drifted, so each one is generated from its canonical source here and
``--check`` fails CI when a copy is stale. Only modules whose imports
are stdlib (or optional, like leyline's guarded ``yaml``) belong in
``VENDORED``: a copy that imports ``leyline.*`` would fail in exactly
the case it exists for.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_FRONTMATTER = "plugins/leyline/src/leyline/frontmatter.py"
_SQLITE_GRAPH_BASE = "plugins/leyline/src/leyline/sqlite_graph_base.py"
_SIBLING_PLUGINS = "plugins/leyline/src/leyline/sibling_plugins.py"
_FS = "plugins/leyline/src/leyline/fs.py"
_TOKENS = "plugins/leyline/src/leyline/tokens.py"
_SESSION_STORE = "plugins/leyline/src/leyline/session_store.py"
_REPORT_FORMATTER = "plugins/abstract/src/abstract/report_formatter.py"
_ATOMIC_FILE = "plugins/leyline/src/leyline/atomic_file.py"

#: Canonical source path to the copies generated from it, repo-relative.
VENDORED: dict[str, list[str]] = {
    _FRONTMATTER: [
        "plugins/sanctum/src/sanctum/_vendored_leyline_frontmatter.py",
        "plugins/memory-palace/scripts/_vendored_leyline_frontmatter.py",
    ],
    _SQLITE_GRAPH_BASE: [
        "plugins/gauntlet/src/gauntlet/_vendored_leyline_sqlite_graph_base.py",
        "plugins/memory-palace/src/memory_palace/"
        "_vendored_leyline_sqlite_graph_base.py",
    ],
    # tokens.py loads its sibling fs copy by name, so the two go together.
    _FS: [
        "plugins/abstract/src/abstract/_vendored_leyline_fs.py",
        "plugins/conjure/scripts/_vendored_leyline_fs.py",
    ],
    # abstract, not leyline: imbue's validator falls back on its report shape.
    _REPORT_FORMATTER: ["plugins/imbue/scripts/_vendored_abstract_report_formatter.py"],
    _TOKENS: ["plugins/abstract/src/abstract/_vendored_leyline_tokens.py"],
    _SESSION_STORE: [
        "plugins/tome/src/tome/_vendored_leyline_session_store.py",
        "plugins/memory-palace/src/memory_palace/_vendored_leyline_session_store.py",
    ],
    _SIBLING_PLUGINS: [
        "plugins/abstract/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/attune/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/conjure/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/conserve/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/egregore/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/imbue/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/pensive/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/sanctum/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/spec-kit/scripts/_vendored_leyline_sibling_plugins.py",
        "plugins/abstract/src/abstract/_vendored_leyline_sibling_plugins.py",
        "plugins/cartograph/hooks/_vendored_leyline_sibling_plugins.py",
        "plugins/pensive/hooks/_vendored_leyline_sibling_plugins.py",
        "plugins/minister/src/minister/_vendored_leyline_sibling_plugins.py",
        "plugins/memory-palace/src/memory_palace/_vendored_leyline_sibling_plugins.py",
    ],
    _ATOMIC_FILE: [
        "plugins/abstract/src/abstract/_vendored_leyline_atomic_file.py",
        "plugins/conserve/hooks/shared/_vendored_leyline_atomic_file.py",
        "plugins/egregore/scripts/_vendored_leyline_atomic_file.py",
        "plugins/herald/hooks/_vendored_leyline_atomic_file.py",
        "plugins/memory-palace/src/memory_palace/_vendored_leyline_atomic_file.py",
        "plugins/minister/src/minister/_vendored_leyline_atomic_file.py",
        "plugins/spec-kit/src/speckit/_vendored_leyline_atomic_file.py",
    ],
}


def _render(root: Path, source: str) -> str:
    banner = (
        f"# Generated from {source} by scripts/sync_vendored.py.\n"
        "# Edit the canonical file and run `python3 scripts/sync_vendored.py`.\n"
    )
    return banner + (root / source).read_text(encoding="utf-8")


def stale_targets(root: Path) -> list[str]:
    """Return every copy under *root* that is missing or differs."""
    stale = []
    for source, targets in VENDORED.items():
        expected = _render(root, source)
        for target in targets:
            path = root / target
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                stale.append(target)
    return stale


def write_targets(root: Path) -> None:
    for source, targets in VENDORED.items():
        rendered = _render(root, source)
        for target in targets:
            path = root / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 listing stale copies instead of rewriting them",
    )
    args = parser.parse_args(argv)
    if args.check:
        stale = stale_targets(REPO_ROOT)
        for target in stale:
            print(f"stale vendored copy: {target}", file=sys.stderr)
        return 1 if stale else 0
    write_targets(REPO_ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
