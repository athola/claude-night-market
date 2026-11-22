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


# `<<EOF`, `<<-EOF`, `<<'EOF'` or `<<"EOF"`, but not a `<<<` here-string.
_HEREDOC_RE = re.compile(
    r"""<<(-?)[ \t]*(?:'([^'\n]+)'|"([^"\n]+)"|([A-Za-z_][\w.-]*))"""
)
_BODY_SEPARATOR_RE = re.compile(r"&&|\|\||[;|&]")
_COMMENT_START_AFTER = frozenset(" \t\n;&|()")
# A separator outside a heredoc body that ends a commit segment.
_CHAIN = "chain"
# A newline outside a heredoc body. A heredoc message spans lines, so it
# separates segments without ending a commit.
_NEWLINE = "newline"
# A separator inside a heredoc body. A body fed to `bash <<EOF` runs, so
# its lines are scanned as segments, but it never ends a commit message.
_BODY = "body"


def _double_quote_end(command: str, start: int) -> int | None:
    """Return the index after the closing double quote, or None."""
    index = start + 1
    while index < len(command):
        if command[index] == "\\":
            index += 2
        elif command[index] == '"':
            return index + 1
        else:
            index += 1
    return None


def _skip_quoted(command: str, index: int) -> int:
    """Return the index after the escape or quoted string starting at index."""
    char = command[index]
    if char == "\\":
        return index + 2
    if char == "'":
        quote_end = command.find("'", index + 1)
        return index + 1 if quote_end == -1 else quote_end + 1
    double_end = _double_quote_end(command, index)
    return index + 1 if double_end is None else double_end


def _heredoc_body_end(
    command: str, start: int, delimiter: str, separators: list[tuple[int, int, str]]
) -> int:
    """Record the body's separators and return the index after its end line.

    Quotes and comments mean nothing in a body, so an apostrophe there
    cannot swallow the commands that follow it.
    """
    index = start
    while index < len(command):
        line_end = command.find("\n", index)
        if line_end == -1:
            line_end = len(command)
        if command[index:line_end].strip() == delimiter:
            return line_end
        for match in _BODY_SEPARATOR_RE.finditer(command, index, line_end):
            separators.append((match.start(), match.end(), _BODY))
        if line_end < len(command):
            separators.append((line_end, line_end + 1, _BODY))
        index = line_end + 1
    return len(command)


def _separators(command: str) -> list[tuple[int, int, str]]:
    """Return (start, end, kind) for every separator the shell acts on.

    One left-to-right pass: a separator inside quotes, a comment or a
    heredoc body is not a code separator. A quote with no closing quote is
    read as a plain character, so the separators after it still split.
    """
    separators: list[tuple[int, int, str]] = []
    pending: list[str] = []
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if char in "\\'\"":
            index = _skip_quoted(command, index)
        elif char == "#" and (index == 0 or command[index - 1] in _COMMENT_START_AFTER):
            line_end = command.find("\n", index)
            index = length if line_end == -1 else line_end
        elif char == "<" and command.startswith("<<", index):
            heredoc = _HEREDOC_RE.match(command, index)
            if heredoc and not command.startswith("<<<", index):
                pending.append(heredoc.group(2) or heredoc.group(3) or heredoc.group(4))
                index = heredoc.end()
            else:
                index += 3 if command.startswith("<<<", index) else 2
        elif char == "\n":
            separators.append((index, index + 1, _NEWLINE))
            index += 1
            for delimiter in pending:
                index = _heredoc_body_end(command, index, delimiter, separators)
                if index < length:
                    separators.append((index, index + 1, _NEWLINE))
                    index += 1
            pending = []
        elif command.startswith(("&&", "||"), index):
            separators.append((index, index + 2, _CHAIN))
            index += 2
        elif char in ";|":
            separators.append((index, index + 1, _CHAIN))
            index += 1
        else:
            index += 1
    return separators


def _segments(command: str) -> list[tuple[int, int]]:
    """Return (start, end) of every segment, leading whitespace skipped."""
    segments = []
    start = 0
    for sep_start, sep_end, _kind in [*_separators(command), (len(command), 0, "")]:
        segment = command[start:sep_start]
        segments.append((start + len(segment) - len(segment.lstrip()), sep_start))
        start = sep_end
    return segments


def git_commit_offset(command: str) -> int | None:
    """Return where the first git commit segment starts, or None.

    The commit's message, heredoc included, follows this offset, and an
    earlier command in the chain precedes it.
    """
    for start, end in _segments(command):
        if _segment_commits(command[start:end]):
            return start
    return None


def git_commit_end(command: str) -> int | None:
    """Return where the first git commit segment ends, or None.

    The end is the next unquoted ``&&``, ``||``, ``;`` or ``|``, so a
    chained command is not read as the message. A newline does not end it,
    nor does a separator inside a heredoc body: a heredoc message spans
    lines.
    """
    start = git_commit_offset(command)
    if start is None:
        return None
    for sep_start, _sep_end, kind in _separators(command):
        if sep_start >= start and kind == _CHAIN:
            return sep_start
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
    for sep_start, sep_end, _kind in _separators(command):
        if sep_start < start and command[sep_start:sep_end] != "|":
            pipeline = sep_end
    feeders = command[pipeline:start]
    return pipeline + len(feeders) - len(feeders.lstrip())


def is_git_commit(command: str) -> bool:
    """Return True if any segment of the Bash command runs git commit."""
    return git_commit_offset(command) is not None
