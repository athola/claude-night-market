"""Recognize a git commit inside a Bash command string.

The hook `if` gate tests each shell segment on its own, so a check on
the start of the whole command misses `git add -A && git commit`.
"""

from __future__ import annotations

import re

# git, then any global options (-C <dir>, -c <k=v>, --no-pager, ...),
# then the commit subcommand.
_GIT_COMMIT_RE = re.compile(r"git(?:\s+(?:-[Cc]\s+\S+|-\S+))*\s+commit\b")
_SEGMENT_SPLIT_RE = re.compile(r"&&|\|\||[;|\n]")


def is_git_commit(command: str) -> bool:
    """Return True if any shell segment of *command* runs git commit."""
    return any(
        _GIT_COMMIT_RE.match(segment.strip())
        for segment in _SEGMENT_SPLIT_RE.split(command)
    )
