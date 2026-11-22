# Generated from plugins/leyline/src/leyline/shell_command.py by scripts/sync_vendored.py.
# Edit the canonical file and run `python3 scripts/sync_vendored.py`.
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

# A segment is read as shell words, left to right, so every word has one
# reading. It may open with subshell parens, a brace group, a command
# substitution (`$(`, a backtick, or `out=$(`), shell keywords (`then`,
# `do`, `!`, `time`), variable assignments and wrappers with their
# options. Then git, bare or path-qualified, then global options with
# their values, quoted or not, then exactly the commit subcommand
# (`commit-tree` is not a commit). A substitution after another word
# (`echo $(git commit)`) is not recognized. An earlier regex had two
# parses per repeated flag and backtracked exponentially: 38 repeated
# `-C` took 46 seconds, past the hook timeout the harness treats as allow.
_WORD_RE = re.compile(r"""(?:'[^']*'|"(?:\\.|[^"\\])*"|\\.|\S)+""")
_OPENER_RE = re.compile(r"(?:\$?\(|`|[A-Za-z_][A-Za-z0-9_]*=(?=\$\(|`))+")
_ASSIGNMENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
_GIT_RE = re.compile(r"(?:\S*/)?git")
_COMMIT_RE = re.compile(r"commit(?![\w-])")
_KEYWORDS = frozenset(
    ("{", "!", "if", "then", "elif", "else", "do", "while", "until", "time")
)
# Wrapper to the options that take the next word as their value.
_WRAPPERS = {
    "env": frozenset(),
    "command": frozenset(),
    "exec": frozenset(),
    "nohup": frozenset(),
    "sudo": frozenset(
        ("-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U", "-T", "-R")
    ),
}
_GIT_VALUE_OPTIONS = frozenset(("-C", "-c", "--git-dir", "--work-tree", "--namespace"))


def _segment_commits(segment: str) -> bool:
    """Return True if this one shell segment runs git commit."""
    words = _WORD_RE.findall(segment)
    index = 0
    while index < len(words):
        word = _OPENER_RE.sub("", words[index], count=1)
        if not word or word in _KEYWORDS or _ASSIGNMENT_RE.match(word):
            index += 1
            continue
        if word not in _WRAPPERS:
            break
        value_options = _WRAPPERS[word]
        index += 1
        while index < len(words) and words[index].startswith("-"):
            index += 2 if words[index] in value_options else 1
    else:
        return False
    if not _GIT_RE.fullmatch(_OPENER_RE.sub("", words[index], count=1)):
        return False
    index += 1
    while index < len(words) and words[index].startswith("-"):
        index += 2 if words[index] in _GIT_VALUE_OPTIONS else 1
    return index < len(words) and bool(_COMMIT_RE.match(words[index]))


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
        if _segment_commits(stripped):
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


# `-F -`, `-qF-`, `--file=-` or `--file -`: the message is read from stdin.
_STDIN_MESSAGE_RE = re.compile(r"\s(?:-[A-Za-z]*F\s*|--file(?:=|\s+))-(?=\s|$)")


def git_commit_message_offset(command: str) -> int | None:
    """Return where the first git commit's message text can start, or None.

    That is the commit segment itself, unless the commit reads its message
    from stdin with ``-F -``. Then the message comes from the commands piped
    into it, and the offset is the first command of that pipeline.
    """
    start = git_commit_offset(command)
    if start is None:
        return None
    if not _STDIN_MESSAGE_RE.search(command[start : git_commit_end(command)]):
        return start
    pipeline = 0
    for token in _SHELL_TOKEN_RE.finditer(command[:start]):
        if token.group(0) in ("&&", "||", ";", "\n"):
            pipeline = token.end()
    feeders = command[pipeline:start]
    return pipeline + len(feeders) - len(feeders.lstrip())


def is_git_commit(command: str) -> bool:
    """Return True if any segment of the Bash command runs git commit."""
    return git_commit_offset(command) is not None
