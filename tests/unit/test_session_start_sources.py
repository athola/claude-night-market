"""Gate: an exhaustive SessionStart matcher must name every known source.

Claude Code filters ``SessionStart`` hooks with a regex over the session
``source``. A matcher that enumerates the sources is asserting "every
way a session can begin", and when a release adds one, that assertion
quietly becomes false: the hook stops firing for the new case and
nothing reports it.

This is the Fable failure in a different place. ``VALID_MODELS`` froze a
set, a tier shipped, the set was never widened, and the guard that
existed to prevent rot had itself rotted. 2.1.212 added ``fork`` and
every exhaustive matcher in this repo silently narrowed.

A *selective* matcher is a different thing and is left alone. Naming two
of five sources is a choice about when the hook should run, not a claim
to completeness, so this gate only holds matchers that already name most
of the set.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Every value Claude Code can report as a SessionStart source.
# ``fork`` arrived in 2.1.212; see docs/knowledge-corpus/
# claude-code-harness-deltas.md.
KNOWN_SOURCES = frozenset({"startup", "resume", "clear", "compact", "fork"})

# At or above this share of KNOWN_SOURCES, a matcher reads as a claim to
# cover every source rather than a deliberate subset.
EXHAUSTIVE_THRESHOLD = 0.6


def _session_start_entries() -> list:
    """Every registered SessionStart entry, as (path, matcher) pairs."""
    entries = []
    for manifest in sorted(REPO_ROOT.glob("plugins/*/hooks/hooks.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for entry in data.get("hooks", {}).get("SessionStart", []):
            matcher = entry.get("matcher")
            if matcher:
                entries.append((manifest.relative_to(REPO_ROOT), matcher))
    return entries


def test_there_is_something_to_check() -> None:
    """A gate that silently matches nothing is not a gate."""
    assert _session_start_entries(), "no SessionStart matcher found to check"


def test_exhaustive_matchers_name_every_known_source() -> None:
    """A matcher claiming completeness must actually be complete."""
    incomplete = []
    for path, matcher in _session_start_entries():
        named = {part.strip() for part in matcher.split("|")}
        if len(named & KNOWN_SOURCES) < EXHAUSTIVE_THRESHOLD * len(KNOWN_SOURCES):
            continue  # a selective matcher, deliberately partial
        missing = KNOWN_SOURCES - named
        if missing:
            incomplete.append(f"{path}: {matcher!r} omits {sorted(missing)}")
    assert not incomplete, "exhaustive matcher missing a source:\n" + "\n".join(
        incomplete
    )


def test_matchers_name_only_real_sources() -> None:
    """A typo in a matcher disables the hook with no error anywhere."""
    unknown = []
    for path, matcher in _session_start_entries():
        for part in matcher.split("|"):
            if part.strip() not in KNOWN_SOURCES:
                unknown.append(f"{path}: {matcher!r} names unknown {part.strip()!r}")
    assert not unknown, "matcher names a source that cannot occur:\n" + "\n".join(
        unknown
    )
