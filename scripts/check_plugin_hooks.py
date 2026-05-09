#!/usr/bin/env python3
"""Pre-commit hook: reject explicit hooks/hooks.json in plugin manifests.

Claude Code auto-loads ``hooks/hooks.json`` from each plugin directory.
Listing it explicitly in ``plugin.json`` causes a "Duplicate hooks file"
error at session start.  The ``hooks`` array should only contain paths
to *additional* hook files beyond the auto-loaded default.

Exit codes:
    0 - no issues found
    1 - duplicate hooks references detected (commit blocked)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# The default hooks file that Claude Code auto-loads.
_AUTO_LOADED = "./hooks/hooks.json"


def check_file(path: Path) -> list[str]:
    """Return error messages for a single plugin.json."""
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"  {path}: failed to parse: {exc}")
        return errors

    hooks = data.get("hooks", [])
    if _AUTO_LOADED in hooks:
        errors.append(
            f"  {path}: hooks array contains '{_AUTO_LOADED}' which is "
            f"auto-loaded by Claude Code. Remove it to avoid duplicate "
            f"hook registration."
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    paths = [Path(p) for p in args] if args else []

    if not paths:
        repo_root = Path(__file__).resolve().parent.parent
        paths = sorted(repo_root.glob("plugins/*/.claude-plugin/plugin.json"))

    errors: list[str] = []
    for path in paths:
        if path.name == "plugin.json":
            errors.extend(check_file(path))

    if errors:
        print("Duplicate hooks/hooks.json detected in plugin manifests:\n")
        print("\n".join(errors))
        print(
            "\nClaude Code auto-loads hooks/hooks.json from each plugin."
            "\nThe hooks array should only list additional hook files."
            '\nSet "hooks": [] if the plugin has no extra hook files.'
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
