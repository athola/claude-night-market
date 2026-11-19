"""Recognize a git commit inside a Bash command string.

Standard library only and Python 3.9 compatible: hooks import a copy under
the operator's bare ``python3``. gauntlet and imbue carry copies generated
by ``scripts/sync_vendored.py``; edit this file, never a copy. The two
hand-kept detectors this replaces had drifted and disagreed on which
commands commit.

The harness ``if`` gate admits ``git add . && git commit`` segment by
segment, so each shell segment is tested on its own. A quoted string is one
token, so a separator inside it splits nothing.
"""

from __future__ import annotations

import re

# Optional subshell parens, variable assignments and wrappers, then git
# (bare or path-qualified), then global options with their values, then
# exactly the commit subcommand (`commit-tree` is not a commit).
_GIT_COMMIT_RE = re.compile(
    r"(?:\(\s*)*"
    r"(?:(?:[A-Za-z_][A-Za-z0-9_]*=\S*|env|command|exec|nohup|sudo)\s+)*"
    r"(?:\S*/)?git"
    r"(?:\s+(?:-[Cc]\s+\S+|--(?:git-dir|work-tree|namespace)\s+\S+|-\S+))*"
    r"\s+commit(?![\w-])"
)
_SHELL_TOKEN_RE = re.compile(
    r"""'[^']*'?|"(?:\\.|[^"\\])*"?|&&|\|\||[;|\n]|[^'"&|;\n]+|&"""
)
_SEPARATORS = ("&&", "||", ";", "|", "\n")


def git_commit_offset(command: str) -> int | None:
    """Return where the first git commit segment starts, or None.

    The commit's message, heredoc included, follows this offset, and an
    earlier command in the chain precedes it.
    """
    start = 0
    for token in _SHELL_TOKEN_RE.finditer(command + "\n"):
        if token.group(0) not in _SEPARATORS:
            continue
        segment = command[start : token.start()]
        stripped = segment.lstrip()
        if _GIT_COMMIT_RE.match(stripped):
            return start + len(segment) - len(stripped)
        start = token.end()
    return None


def git_commit_end(command: str) -> int | None:
    """Return where the first git commit segment ends, or None.

    The end is the next unquoted ``&&``, ``||``, ``;`` or ``|``, so a
    chained command is not read as the message. A newline does not end it:
    a heredoc message spans lines.
    """
    start = git_commit_offset(command)
    if start is None:
        return None
    for token in _SHELL_TOKEN_RE.finditer(command, start):
        if token.group(0) in ("&&", "||", ";", "|"):
            return token.start()
    return len(command)


def is_git_commit(command: str) -> bool:
    """Return True if any segment of the Bash command runs git commit."""
    return git_commit_offset(command) is not None
