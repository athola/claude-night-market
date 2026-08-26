#!/usr/bin/env python3
"""On-demand recall for the UserPromptSubmit event.

Append ``+recall`` to a prompt to have past-session handoff units injected
alongside it; ``+recall?`` also shows what was retrieved.

Recall is opt-in rather than automatic on purpose. Fixed-cost memory
injection on every turn spends the context window it was meant to extend,
and retrieved units are frequently stale, so surfacing them unbidden
trades one failure mode for a worse one. The token is the consent.

Performance contract: the token is absent from nearly every prompt, so the
quiet path must not import the memory_palace package at all. Every heavy
import below is deliberately function-local; ``tests/hooks/
test_recall_hook.py`` asserts this and fails if one migrates to module
scope.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent

# Hooks run as standalone scripts, so the package is not on the path.
# Without this the memory_palace imports below fail and every weighting
# and staleness check silently degrades to neutral. Adding the path is
# cheap; it is a string operation, not an import.
_SRC = str(PLUGIN_ROOT / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Matches the token only as a standalone word, so prose such as "can you
# recall what we decided" does not trigger retrieval.
RECALL_TOKEN = re.compile(r"(?:^|\s)\+recall(\?)?(?=\s|$)", re.IGNORECASE)

MAX_SESSIONS_SCANNED = 60
MAX_UNITS_RETURNED = 6
_STOPWORDS = frozenset(
    "a an and are as at be but by for from how in into is it of on or that the "  # noqa: SIM905 - a stopword list reads as prose; 34 literals do not
    "then there these this to was what when where which who why with we you i".split()
)


def _tokenize(text: str) -> set[str]:
    """Reduce text to lowercase content words for overlap scoring."""
    return {
        w for w in re.findall(r"[a-z0-9_.-]{3,}", text.lower()) if w not in _STOPWORDS
    }


def _sessions_dir() -> Path:
    """Return the directory holding session records.

    Resolved on call, not at import. PLUGIN_ROOT is version scoped --
    hooks run from ``cache/<marketplace>/<plugin>/<version>/`` -- so
    session records written under it are stranded by the next update
    (issue #661). The persistent root fixes that, but importing it at
    module level would break the contract this hook is built on: recall
    is opt-in and runs on every prompt, so nothing from
    ``memory_palace`` may load until a prompt actually asks for it.
    ``test_heavy_imports_are_deferred`` enforces that.
    """
    from memory_palace.paths import user_data_dir

    return user_data_dir(PLUGIN_ROOT) / "sessions"


def _recent_session_files() -> list[Path]:
    """Return the newest session records, newest first."""
    sessions_dir = _sessions_dir()
    if not sessions_dir.is_dir():
        return []
    files = [p for p in sessions_dir.glob("*.json") if p.name != "session_index.json"]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:MAX_SESSIONS_SCANNED]


def _supersede(units: list[dict]) -> list[dict]:
    """Keep only the newest unit for each (thread, type).

    ``merge_handoff_units`` already applies this rule inside a single
    record. Recall reads across records, where the invariant does not
    hold on its own: a state unit and the correction written three
    sessions later both survive and compete on keyword overlap. This
    finishes the merge design rather than introducing a second one.

    Superseding by thread alone would be a correctness bug. A durable
    finding and the transient state that produced it are deliberately
    kept on separate decay curves, so the key is the pair.

    The older unit is dropped rather than flagged. Flagging is the right
    treatment for a fallible signal such as a content digest, which
    reformatting can trip; supersession is not fallible in that way,
    because the newer unit is the replacement by construction. With
    ``MAX_UNITS_RETURNED`` at 6, keeping a known-superseded duplicate
    would crowd out a distinct unit.

    First seen wins, because ``_recent_session_files`` sorts newest
    first. That same mtime ordering already decides which records are
    scanned at all, so relying on it to order two units adds no new
    assumption. Session records are runtime data that is never cloned,
    checked out, or rebased, so the argument against mtime in
    ``staleness_signals`` does not reach this case.
    """
    seen: set[tuple[str, str]] = set()
    kept: list[dict] = []
    for unit in units:
        key = (str(unit.get("thread", "")), str(unit.get("type", "")))
        if key in seen:
            continue
        seen.add(key)
        kept.append(unit)
    return kept


def _load_units() -> list[dict]:
    """Collect handoff units from recent session records, newest first.

    Reads untrusted on-disk JSON, so a malformed or unreadable record is
    skipped rather than allowed to break the prompt path.
    """
    units: list[dict] = []
    for path in _recent_session_files():
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for unit in record.get("handoff_units") or []:
            if isinstance(unit, dict) and unit.get("thread"):
                units.append(unit)
    return _supersede(units)


def _weight_for(unit: dict) -> float:
    """Score a unit by how fast its type goes stale.

    Falls back to a neutral weight when the decay model is unavailable so
    that recall degrades to pure keyword matching instead of failing.
    """
    from datetime import datetime, timezone

    try:
        from memory_palace.corpus.decay_model import DecayModel
    except ImportError:
        return 1.0
    try:
        written = datetime.fromisoformat(unit.get("date", "")).replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return 1.0
    state = DecayModel().calculate_decay(
        entry_id=unit.get("thread", ""),
        maturity="growing",
        last_validated=written,
        unit_type=unit.get("type"),
    )
    return state.decay_factor


def _rank(query: str, units: list[dict]) -> list[tuple[dict, float]]:
    """Rank units by keyword overlap scaled by type-aware decay."""
    query_terms = _tokenize(query)
    scored: list[tuple[dict, float]] = []
    for unit in units:
        haystack = " ".join(
            str(unit.get(k, "")) for k in ("thread", "state", "why", "open")
        )
        overlap = len(query_terms & _tokenize(haystack))
        if not overlap:
            continue
        scored.append((unit, overlap * _weight_for(unit)))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:MAX_UNITS_RETURNED]


def _changed_dependencies(units: list[dict], root: Path) -> dict[str, list[str]]:
    """Map each unit's thread to the dependencies that have moved.

    Returns an empty map when the signal module is unavailable, so
    recall degrades to decay-only ranking rather than failing.
    """
    try:
        from memory_palace.corpus.staleness_signals import (
            changed_paths,
            check_dependencies,
        )
    except ImportError:
        return {}
    flagged: dict[str, list[str]] = {}
    for unit in units:
        digests = unit.get("file_digests") or {}
        if not digests:
            continue
        moved = changed_paths(check_dependencies(digests, root=root))
        if moved:
            flagged[str(unit.get("thread", ""))] = moved
    return flagged


def _render(
    ranked: list[tuple[dict, float]],
    visible: bool,
    changed: dict[str, list[str]] | None = None,
) -> str:
    """Format retrieved units for injection.

    A unit whose dependencies moved is flagged rather than dropped. The
    reader needs to know the topic has history even when the ground
    under it shifted; suppressing it hides both facts at once.
    """
    if not ranked:
        body = (
            "Memory Palace recall: no past-session units matched this prompt. "
            "Units are captured by Skill(memory-palace:session-handoff)."
        )
        return f"[+recall? visible] {body}" if visible else body

    lines = ["Memory Palace recall: prior units matching this prompt."]
    if visible:
        lines[0] = "[+recall? visible] " + lines[0]
    changed = changed or {}
    for unit, score in ranked:
        lines.append(
            f"- ({unit.get('type', '?')}, {unit.get('date', '?')}) "
            f"{unit.get('thread', '')}: {unit.get('state', '')}"
        )
        moved = changed.get(str(unit.get("thread", "")))
        if moved:
            lines.append(
                f"    STALE SIGNAL: changed since this was written: "
                f"{', '.join(moved)}. Verify before relying on it."
            )
        if unit.get("open"):
            lines.append(f"    still open: {unit['open']}")
        if visible:
            lines.append(f"    score: {score:.3f}  ref: {unit.get('ref', 'n/a')}")
    lines.append(
        "Treat 'state' units older than a few days as suspect; verify before "
        "relying on them."
    )
    return "\n".join(lines)


def main() -> None:
    """Inject past-session units when the prompt opts in."""
    if os.environ.get("MEMORY_PALACE_RECALL") == "off":
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    prompt = payload.get("prompt", "") if isinstance(payload, dict) else ""
    match = RECALL_TOKEN.search(prompt)
    if not match:
        sys.exit(0)

    visible = match.group(1) == "?"
    query = RECALL_TOKEN.sub(" ", prompt)
    units = _load_units()
    ranked = _rank(query, units)
    root = Path(payload.get("cwd") or Path.cwd())
    context = _render(
        ranked, visible, _changed_dependencies([u for u, _ in ranked], root)
    )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
