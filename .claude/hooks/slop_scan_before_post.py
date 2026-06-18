#!/usr/bin/env python3
"""PreToolUse hook: block AI-slop in content posted to public channels.

The repo already scans markdown docs for slop before merge (see
`.claude/rules/slop-scan-for-docs.md`) and sanctum strips slop from git
output (`plugins/sanctum/commands/shared/output-hygiene.md`). This hook
closes the remaining gap: content crafted and posted straight to GitHub
issues, PR/MR comments, and discussions by workflows like
`minister:create-issue`, `attune:war-room`, `abstract:insight-engine`,
`egregore:summon`, and `tome:synthesize`.

It intercepts `gh` content-posting commands, extracts the body payload
(inline `--body`, `gh api -f body=`, or a resolved `--body-file`), and
blocks (exit 2) when the payload carries slop markers. Anything it cannot
parse is allowed through: a hook must never wedge legitimate work.
"""

import json
import re
import shlex
import sys
from pathlib import Path

# A `gh` invocation that writes prose to a public channel. View/list/clone
# read-only forms are deliberately excluded.
_POSTING_RE = re.compile(
    r"""\bgh\s+
        (?:
            (?:issue|pr)\s+(?:create|comment|edit|review)\b
          | discussion\s+(?:create|comment|edit)\b
          | api\b[^\n]*\b(?:discussions|comments|issues|pulls)\b
        )
    """,
    re.VERBOSE,
)

# Unambiguous markers: characters that never legitimately appear in a `gh`
# command except inside the prose body. Safe to match against the whole
# command string when the body cannot be isolated.
_UNAMBIGUOUS = {
    "em-dash": re.compile(r"—"),
    "smart quote": re.compile(r"[“”‘’]"),
    "unicode arrow": re.compile(r"→"),
}

# Fuller marker set, applied only to an extracted body where high-confidence
# prose context keeps false positives low.
_TIER1_WORDS = (
    "comprehensive",
    "seamless",
    "actionable",
    "robust",
    "leverage",
    "delve",
    "myriad",
    "streamline",
    "empower",
    "cutting-edge",
)
_BODY_MARKERS = {
    **_UNAMBIGUOUS,
    "ascii arrow connector": re.compile(r"[^`]\s(?:->)\s[^`]"),
    "double-dash in prose": re.compile(r"\S\s--\s\S"),
    "'+' as conjunction": re.compile(r"[A-Za-z]\s\+\s[A-Za-z]"),
    "tier-1 slop word": re.compile(
        r"\b(?:" + "|".join(_TIER1_WORDS) + r")\b", re.IGNORECASE
    ),
}

# Flags whose value is the prose body of the post.
_INLINE_BODY_FLAGS = {"--body", "-b", "--message", "-m", "--notes"}
_FILE_BODY_FLAGS = {"--body-file", "-F", "--notes-file"}


def is_posting_command(command: str) -> bool:
    """True when the command posts prose to a public channel."""
    return bool(_POSTING_RE.search(command))


def _iter_tokens(command: str):
    try:
        return shlex.split(command)
    except ValueError:
        # Unbalanced quotes / heredocs: caller falls back to raw scanning.
        return None


def extract_body(command: str, repo_root: Path | None = None) -> str | None:
    """Return the post body, or None if it cannot be isolated.

    Handles inline `--body "..."`, `gh api -f body=...` / `--field body=...`,
    and `--body-file PATH` (the file is read relative to repo_root or cwd).
    """
    tokens = _iter_tokens(command)
    if tokens is None:
        return None

    parts: list[str] = []
    root = Path(repo_root) if repo_root else Path.cwd()

    i = 0
    while i < len(tokens):
        tok = tokens[i]
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None

        if tok in _INLINE_BODY_FLAGS and nxt is not None:
            parts.append(nxt)
            i += 2
            continue
        if tok.startswith("--body=") or tok.startswith("--message="):
            parts.append(tok.split("=", 1)[1])
            i += 1
            continue
        if tok in _FILE_BODY_FLAGS and nxt is not None:
            text = _read_body_file(nxt, root)
            if text is not None:
                parts.append(text)
            i += 2
            continue
        # gh api: `-f body=...` / `--field body=...` / `--raw-field body=...`
        if tok in ("-f", "-F", "--field", "--raw-field") and nxt is not None:
            key, _, val = nxt.partition("=")
            if key.strip() in ("body", "body[text]") and val:
                parts.append(val)
            i += 2
            continue
        i += 1

    return "\n".join(parts) if parts else None


def _read_body_file(path_str: str, root: Path) -> str | None:
    try:
        path = Path(path_str)
        if not path.is_absolute():
            path = root / path
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _scan(text: str, markers: dict) -> list[str]:
    return [name for name, pat in markers.items() if pat.search(text)]


def scan_command(command: str, repo_root: Path | None = None) -> list[str]:
    """Return slop-marker names found in a posting command's payload.

    Two-tier: an extracted body is scanned with the full marker set; when
    extraction fails, only unambiguous unicode markers are matched against
    the whole command. Non-posting commands are never scanned.
    """
    if not is_posting_command(command):
        return []

    body = extract_body(command, repo_root)
    if body is not None:
        return _scan(body, _BODY_MARKERS)
    return _scan(command, _UNAMBIGUOUS)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # fail open: never wedge the agent on a broken payload

    if payload.get("tool_name") != "Bash":
        return 0
    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    try:
        findings = scan_command(command)
    except Exception:
        return 0  # fail open on any internal error

    if not findings:
        return 0

    markers = ", ".join(sorted(set(findings)))
    sys.stderr.write(
        "Blocked: content destined for a public channel carries AI-slop "
        f"markers ({markers}).\n"
        "Fix the post body, then retry. Run Skill(scribe:slop-detector) on "
        "the text, or apply the rules in .claude/rules/slop-scan-for-docs.md "
        "(replace em-dashes/arrows, straighten smart quotes, cut tier-1 "
        "filler words). This guard mirrors sanctum's output-hygiene contract "
        "for git output.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
