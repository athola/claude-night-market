#!/usr/bin/env python3
"""Queue research-heavy sessions for knowledge-corpus review.

``knowledge-intake`` documents a queue at ``docs/knowledge-corpus/queue/``
fed by this hook. Until now the hook existed only as a specification, so
the queue the skill told readers to check was never written to. This is
the implementation of that contract.

Fires on SessionEnd. A session qualifies when it ran enough web searches
and its opening prompt reads as research. Both facts come from the
transcript: the SessionEnd payload carries a ``transcript_path`` and no
account of what the session did. The entry is a review stub, not a
verdict: scoring stays with ``Skill(memory-palace:knowledge-intake)``,
which owns the rubric.

Registered with ``async: true``. The SessionEnd batch is bounded by
``max(1500ms, max timeout declared in settings-level hooks)``, a ceiling
this plugin's own ``timeout`` does not raise, and interpreter startup
alone can exceed it. The queue file is the record; nothing this hook
prints reaches a session that has already ended.
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
WEB_TOOLS = {"WebSearch", "WebFetch"}

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


def _message_text(content: object) -> str:
    """Read prompt text from either message shape.

    A plain prompt is a string. A prompt carrying attachments is a list
    of blocks, and only the text ones hold what the user typed.
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return " ".join(part for part in parts if part).strip()
    return ""


def _is_topic(text: str) -> bool:
    """Decide whether a user message names a research subject.

    A message opening with a tag is machinery rather than a prompt:
    resumed sessions start with a caveat block, and shell lines arrive
    as ``bash-input``. Three of eight real transcripts carrying web
    searches begin that way, so reading only the first user record
    would disqualify them all.
    """
    if not text or text.startswith("<"):
        return False
    haystack = text.lower()
    return any(cue in haystack for cue in RESEARCH_CUES)


def _transcript_signal(transcript_path: str) -> tuple[int, str]:
    """Count web searches and find the prompt that reads as research.

    Returns ``(0, "")`` for a transcript that cannot be read, which
    fails closed: no signal means no queue entry.
    """
    searches = 0
    topic = ""
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                # Only user records and tool calls can change the
                # verdict. Skipping the rest on a substring test keeps a
                # 54 MB transcript under 100 ms.
                if '"user"' not in line and '"tool_use"' not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(record, dict):
                    continue
                content = (record.get("message") or {}).get("content")
                kind = record.get("type")
                if kind == "user" and not topic and not record.get("isMeta"):
                    # isMeta marks content the harness injected rather
                    # than content the user typed: an expanded slash
                    # command, a skill body. Those are long enough to
                    # carry a research cue by accident.
                    text = _message_text(content)
                    if _is_topic(text):
                        topic = text
                elif kind == "assistant" and isinstance(content, list):
                    searches += sum(
                        1
                        for block in content
                        if isinstance(block, dict)
                        and block.get("type") == "tool_use"
                        and block.get("name") in WEB_TOOLS
                    )
    except OSError:
        return 0, ""
    return searches, topic


def _already_queued(queue_dir: Path, session_id: str) -> bool:
    """Avoid a second entry when the event fires again."""
    if not session_id or not queue_dir.is_dir():
        return False
    return any(queue_dir.glob(f"*{session_id[:8]}*.yaml"))


def _render(
    session_id: str, prompt: str, searches: int, topic: str, now: datetime
) -> str:
    """Build the review stub. Scoring is deliberately left unfilled.

    *prompt* and *topic* arrive redacted; see the call site.
    """
    return "\n".join(
        [
            "---",
            f"created_at: {now.isoformat()}",
            f"session_id: {session_id or 'unknown'}",
            "session_type: research",
            f"topic: {_yaml_scalar(topic)}",
            "status: pending_review",
            "auto_generated: true",
            f"web_searches: {searches}",
            "---",
            "",
            f"# Research Session: {topic}",
            "",
            "## Context",
            "",
            prompt[:4000] or "No prompt text recorded.",
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
    if not isinstance(payload, dict):
        sys.exit(0)

    searches, subject = _transcript_signal(str(payload.get("transcript_path", "")))
    if searches < MIN_WEB_SEARCHES or not subject:
        sys.exit(0)

    session_id = str(payload.get("session_id", ""))
    queue_dir = Path.cwd() / QUEUE_DIR
    if _already_queued(queue_dir, session_id):
        sys.exit(0)

    now = datetime.now(timezone.utc)
    # Redact once, here: this one value reaches the frontmatter, the
    # heading, the body, and the filename, and the entry outlives the
    # session on disk.
    prompt = SECRET_PATTERN.sub("[redacted]", subject)
    topic = prompt[:120]
    entry = _render(session_id, prompt, searches, topic, now)
    if len(entry.encode("utf-8")) > MAX_ENTRY_BYTES:
        entry = entry[:MAX_ENTRY_BYTES]

    try:
        queue_dir.mkdir(parents=True, exist_ok=True)
        name = f"{now:%Y-%m-%d}_{session_id[:8] or 'nosession'}_{_slug(topic)}.yaml"
        (queue_dir / name).write_text(entry, encoding="utf-8")
    except OSError:
        sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
