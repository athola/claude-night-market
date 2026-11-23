"""Read ``.gauntlet/config.yaml`` or ``config.json`` the same way in every hook.

The hooks run on the first python3 on PATH, which may have no PyYAML and
no gauntlet dependencies, so this module imports the standard library only
and PyYAML lazily.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _read_yaml(path: Path) -> Any:
    try:
        from yaml import YAMLError, safe_load
    except ImportError:
        print(
            f"warning: PyYAML is not installed for {sys.executable}; {path} is ignored",
            file=sys.stderr,
        )
        raise
    try:
        return safe_load(path.read_text())
    except YAMLError as exc:
        raise ValueError(str(exc)) from exc


def load_config(gauntlet_dir: Path) -> dict[str, Any] | None:
    """Return the config mapping, ``{}`` when absent, None when unreadable.

    config.yaml is preferred and config.json is the fallback. A file that
    parses to something other than a mapping holds no settings, so it reads
    as ``{}``. None tells a caller that a config exists but could not be
    read, which a caller that needs consent (a multi-minute rebuild) treats
    differently from no config at all.
    """
    unreadable = False
    readers = (("config.yaml", _read_yaml), ("config.json", _read_json))
    for name, reader in readers:
        path = gauntlet_dir / name
        if not path.exists():
            continue
        try:
            parsed = reader(path)
        except ImportError:
            unreadable = True
            continue
        except (OSError, ValueError) as exc:
            # A typo must not read the same as having no config.
            print(f"warning: could not read {path}: {exc}", file=sys.stderr)
            unreadable = True
            continue
        return parsed if isinstance(parsed, dict) else {}
    return None if unreadable else {}


def _read_json(path: Path) -> Any:
    # JSONDecodeError is a ValueError.
    return json.loads(path.read_text())
