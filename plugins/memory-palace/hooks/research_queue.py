#!/usr/bin/env python3
"""Queue research-heavy sessions for knowledge-corpus review.

``knowledge-intake`` documents a queue at ``docs/knowledge-corpus/queue/``
fed by this hook. Until now the hook existed only as a specification, so
the queue the skill told readers to check was never written to. This is
the implementation of that contract.

Fires on SessionEnd. A session qualifies when it ran enough web searches
and its prompt reads as research. The entry is a review stub, not a
verdict: scoring stays with ``Skill(memory-palace:knowledge-intake)``,
which owns the rubric.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MIN_WEB_SEARCHES = 3
QUEUE_DIR = Path("docs") / "knowledge-corpus" / "queue"
MAX_ENTRY_BYTES = 100_000

RESEARCH_CUES = (
    "research",
    "investigate",
    "deep dive",
    "brainstorm",
    "explore",
    "analyze",
    "study",
    "best practices",
    "patterns",
    "techniques",
    "survey",
    "landscape",
    "comparison",
    "evaluation",
    "find tools",
)

# Redaction, not detection: anything shaped like a credential is dropped
# before it can be written to a file that outlives the session.
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"
    r"|api[_-]?key\s*[:=]\s*\S+)",
    re.IGNORECASE,
)


def _yaml_scalar(value: str) -> str:
    """Quote *value* for use as a YAML double-quoted scalar.

    JSON string syntax is a subset of YAML's double-quoted style, so
    ``json.dumps`` escapes the quotes, newlines, and control characters
    that would otherwise close the scalar early and leave the entry
    unparsable by every reader downstream.
    """
    return json.dumps(str(value))


def _slug(text: str, limit: int = 40) -> str:
    """Reduce a topic to a filename-safe slug."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (cleaned[:limit].rstrip("-")) or "session"


def _search_count(payload: dict) -> int:
    """Count web searches, tolerating either payload shape."""
    explicit = payload.get("web_search_count")
    if isinstance(explicit, int):
        return explicit
    tools = payload.get("tools_used") or []
    return sum(1 for t in tools if str(t) in {"WebSearch", "WebFetch"})


def _qualifies(payload: dict) -> bool:
    """Decide whether this session is worth a corpus review."""
    if _search_count(payload) < MIN_WEB_SEARCHES:
        return False
    haystack = " ".join(
        str(payload.get(k, "")) for k in ("prompt", "summary", "topic")
    ).lower()
    return any(cue in haystack for cue in RESEARCH_CUES)


def _already_queued(queue_dir: Path, session_id: str) -> bool:
    """Avoid a second entry when the event fires again."""
    if not session_id or not queue_dir.is_dir():
        return False
    return any(queue_dir.glob(f"*{session_id[:8]}*.yaml"))


def _render(payload: dict, topic: str, now: datetime) -> str:
    """Build the review stub. Scoring is deliberately left unfilled."""
    body = SECRET_PATTERN.sub("[redacted]", str(payload.get("prompt", "")))
    return "\n".join(
        [
            "---",
            f"created_at: {now.isoformat()}",
            f"session_id: {payload.get('session_id', 'unknown')}",
            "session_type: research",
            f"topic: {_yaml_scalar(topic)}",
            "status: pending_review",
            "auto_generated: true",
            f"web_searches: {_search_count(payload)}",
            "---",
            "",
            f"# Research Session: {topic}",
            "",
            "## Context",
            "",
            body[:4000] or "No prompt text recorded.",
            "",
            "## Next Actions",
            "",
            "- [ ] Score with the knowledge-intake rubric",
            "- [ ] Decide storage location or discard",
            "",
        ]
    )


def main() -> None:
    """Write one queue entry when the session qualifies."""
    if os.environ.get("MEMORY_PALACE_AUTO_QUEUE", "").lower() == "false":
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    if not isinstance(payload, dict) or not _qualifies(payload):
        sys.exit(0)

    session_id = str(payload.get("session_id", ""))
    queue_dir = Path.cwd() / QUEUE_DIR
    if _already_queued(queue_dir, session_id):
        sys.exit(0)

    now = datetime.now(timezone.utc)
    # Redact here rather than at render: this one value reaches the
    # frontmatter, the heading, and the filename, and the entry outlives
    # the session on disk.
    topic = SECRET_PATTERN.sub(
        "[redacted]",
        str(payload.get("topic") or payload.get("prompt") or "session"),
    )[:120]
    entry = _render(payload, topic, now)
    if len(entry.encode("utf-8")) > MAX_ENTRY_BYTES:
        entry = entry[:MAX_ENTRY_BYTES]

    try:
        queue_dir.mkdir(parents=True, exist_ok=True)
        name = f"{now:%Y-%m-%d}_{session_id[:8] or 'nosession'}_{_slug(topic)}.yaml"
        (queue_dir / name).write_text(entry, encoding="utf-8")
    except OSError:
        sys.exit(0)

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionEnd",
                    "additionalContext": (
                        f"Memory Palace: research session queued at "
                        f"{QUEUE_DIR}/{name}. Review with "
                        f"Skill(memory-palace:knowledge-intake)."
                    ),
                }
            }
        )
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
