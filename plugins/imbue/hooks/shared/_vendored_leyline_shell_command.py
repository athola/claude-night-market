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

import bisect
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
_KEYWORDS = frozenset(("{", "!", "if", "then", "elif", "else", "do", "while", "until"))
# Wrapper to the options that take the next word as their value, and the
# number of operands it reads before the command (`timeout 60`).
_WRAPPERS: dict[str, tuple[frozenset[str], int]] = {
    "env": (frozenset(("-u", "-C", "--unset", "--chdir")), 0),
    "command": (frozenset(), 0),
    "exec": (frozenset(("-a",)), 0),
    "nohup": (frozenset(), 0),
    "time": (frozenset(("-f", "-o")), 0),
    "nice": (frozenset(("-n", "--adjustment")), 0),
    "timeout": (frozenset(("-s", "-k", "--signal", "--kill-after")), 1),
    "xargs": (frozenset(("-a", "-d", "-E", "-I", "-L", "-n", "-P", "-s")), 0),
    "sudo": (
        frozenset(
            ("-u", "-g", "-C", "-D", "-h", "-p", "-r", "-t", "-U", "-T", "-R")
            + ("--user", "--group", "--chdir", "--host", "--prompt", "--role")
            + ("--type", "--other-user", "--close-from", "--command-timeout")
        ),
        0,
    ),
}
_GIT_VALUE_OPTIONS = frozenset(("-C", "-c", "--git-dir", "--work-tree", "--namespace"))
_SHELLS = frozenset(("sh", "bash", "zsh", "dash", "ksh"))
_SHELL_VALUE_OPTIONS = frozenset(("-o", "+o", "-O", "+O", "--rcfile", "--init-file"))
_UNQUOTE_RE = re.compile(r"""'([^']*)'|"((?:\\.|[^"\\])*)"|\\(.)|(.)""", re.DOTALL)
# `bash -c "bash -c '...'"` nests; deeper than this is not a real command.
_MAX_SCRIPT_DEPTH = 3


def _strip_opener(word: str) -> str:
    """Drop a leading `(`, `$(`, backtick or `out=$(` that opens a command.

    A substitution that closes inside the word (`X=$(pwd)`) is a value,
    not an opener, and the word stays whole for the assignment check.
    """
    opener = _OPENER_RE.match(word)
    if opener is None or any(closer in word[opener.end() :] for closer in ")`"):
        return word
    return word[opener.end() :]


def _unquote(word: str) -> str:
    """Return the text the shell passes for this word."""
    parts = []
    for single, double, escaped, plain in _UNQUOTE_RE.findall(word):
        if double:
            parts.append(re.sub(r'\\(["\\$`])', r"\1", double))
        else:
            parts.append(single or escaped or plain)
    return "".join(parts)


def _shell_script(words: list[str], index: int) -> str | None:
    """Return the `-c` script of the shell invoked at words[index], or None."""
    index += 1
    while index < len(words) and words[index][:1] in ("-", "+"):
        word = words[index]
        if word in _SHELL_VALUE_OPTIONS:
            index += 2
        elif word[0] == "-" and not word.startswith("--") and "c" in word:
            return _unquote(words[index + 1]) if index + 1 < len(words) else None
        else:
            index += 1
    return None


def _segment_commits(segment: str, depth: int = 0) -> bool:
    """Return True if this one shell segment runs git commit.

    A script passed to ``sh -c``, ``bash -c`` or ``eval`` is read as a
    command of its own, but only when the shell is the segment's command:
    ``echo "bash -c 'git commit'"`` prints, it does not commit.
    """
    # A backslash-newline joins two lines into one command.
    words = _WORD_RE.findall(segment.replace("\\\n", " "))
    index = 0
    while index < len(words):
        word = _strip_opener(words[index])
        if not word or word in _KEYWORDS or _ASSIGNMENT_RE.match(word):
            index += 1
            continue
        wrapper = word.rsplit("/", 1)[-1]  # /usr/bin/env is env
        if wrapper not in _WRAPPERS:
            break
        value_options, operands = _WRAPPERS[wrapper]
        index += 1
        while index < len(words) and words[index].startswith("-"):
            index += 2 if words[index] in value_options else 1
        index += operands
    else:
        return False
    head = _strip_opener(words[index])
    if head in ("eval", *_SHELLS) or head.rsplit("/", 1)[-1] in _SHELLS:
        if depth >= _MAX_SCRIPT_DEPTH:
            return False
        script = (
            " ".join(_unquote(word) for word in words[index + 1 :])
            if head == "eval"
            else _shell_script(words, index)
        )
        return script is not None and _commits_anywhere(script, depth + 1)
    if not _GIT_RE.fullmatch(head):
        return False
    index += 1
    while index < len(words) and words[index].startswith("-"):
        index += 2 if words[index] in _GIT_VALUE_OPTIONS else 1
    return index < len(words) and bool(_COMMIT_RE.match(words[index]))


def _commits_anywhere(command: str, depth: int) -> bool:
    """Return True if any segment of command runs git commit."""
    return any(
        _segment_commits(command[start:end], depth) for start, end in _segments(command)
    )


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


def _is_redirection(command: str, index: int) -> bool:
    """Return True if the `&` at index is part of `>&`, `<&` or `&>`."""
    return (index > 0 and command[index - 1] in "<>") or command.startswith(
        ">", index + 1
    )


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
        elif command.startswith(("&&", "||", "|&"), index):
            separators.append((index, index + 2, _CHAIN))
            index += 2
        elif char in ";|" or (char == "&" and not _is_redirection(command, index)):
            separators.append((index, index + 1, _CHAIN))
            index += 1
        else:
            index += 1
    return separators


def _segments(
    command: str, separators: list[tuple[int, int, str]] | None = None
) -> list[tuple[int, int]]:
    """Return (start, end) of every segment, leading whitespace skipped."""
    if separators is None:
        separators = _separators(command)
    segments = []
    start = 0
    for sep_start, sep_end, _kind in [*separators, (len(command), 0, "")]:
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


# `-F -`, `-qF-`, `--file=-` or `--file -`: the message is read from stdin.
_STDIN_MESSAGE_RE = re.compile(r"\s(?:-[A-Za-z]*F\s*|--file(?:=|\s+))-(?=\s|$)")


def git_commit_spans(command: str) -> list[tuple[int, int]]:
    """Return (message start, end) for every git commit segment.

    The end is the next unquoted ``&&``, ``||``, ``;``, ``|`` or ``&``, so
    a chained command is not read as the message. A newline does not end
    it, nor does a separator inside a heredoc body: a heredoc message spans
    lines. The start is the commit segment, unless the commit reads its
    message from stdin with ``-F -``. Then the message comes from the
    commands piped into it, and the start is the first command of that
    pipeline.
    """
    separators = _separators(command)
    chain_starts = [start for start, _end, kind in separators if kind == _CHAIN]
    pipeline_starts = [
        (start, end) for start, end, _kind in separators if command[start:end] != "|"
    ]
    spans = []
    for start, end in _segments(command, separators):
        if not _segment_commits(command[start:end]):
            continue
        chain = bisect.bisect_left(chain_starts, start)
        stop = chain_starts[chain] if chain < len(chain_starts) else len(command)
        message_start = start
        if _STDIN_MESSAGE_RE.search(command[start:stop]):
            before = bisect.bisect_left(pipeline_starts, (start, -1))
            pipeline = pipeline_starts[before - 1][1] if before else 0
            feeders = command[pipeline:start]
            message_start = pipeline + len(feeders) - len(feeders.lstrip())
        spans.append((message_start, stop))
    return spans


def git_commit_end(command: str) -> int | None:
    """Return where the first git commit segment ends, or None."""
    spans = git_commit_spans(command)
    return spans[0][1] if spans else None


def git_commit_message_offset(command: str) -> int | None:
    """Return where the first git commit's message text can start, or None."""
    spans = git_commit_spans(command)
    return spans[0][0] if spans else None


def is_git_commit(command: str) -> bool:
    """Return True if any segment of the Bash command runs git commit."""
    return git_commit_offset(command) is not None
