"""A shipped doc that runs another plugin's script says what to do without it.

``python3 plugins/<other>/scripts/x.py`` resolves only inside a checkout of
this repository. A marketplace install has no ``plugins/`` tree under the
user's cwd, so the step fails. ADR-0001 asks every cross-plugin
integration to degrade, so each such call is followed by its fallback.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CALL = re.compile(r"python3? plugins/([a-z-]+)/scripts/")
FALLBACK_WINDOW = 15


def _calls_without_fallback() -> tuple[int, list[str]]:
    found, missing = 0, []
    for doc in sorted((REPO_ROOT / "plugins").glob("*/*/**/*.md")):
        parts = doc.relative_to(REPO_ROOT / "plugins").parts
        if parts[1] not in {"skills", "commands", "agents"}:
            continue
        lines = doc.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines):
            for match in CALL.finditer(line):
                if match.group(1) == parts[0]:
                    continue
                found += 1
                window = " ".join(lines[number : number + FALLBACK_WINDOW])
                if "not a checkout" not in window:
                    rel = doc.relative_to(REPO_ROOT).as_posix()
                    missing.append(f"{rel}:{number + 1}")
    return found, missing


def test_every_cross_plugin_script_call_states_its_fallback() -> None:
    found, missing = _calls_without_fallback()
    assert found, "no cross-plugin calls found; the sweep is vacuous"
    assert missing == []
