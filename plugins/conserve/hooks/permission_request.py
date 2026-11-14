#!/usr/bin/env python3
"""PermissionRequest hook for workflow automation.

This hook implements permission auto-approval for safe operations
and auto-denial for dangerous patterns.

Claude Code 2.0.54+ supports PermissionRequest hooks that can:
- Auto-approve safe operations (bypasses permission dialog)
- Auto-deny dangerous commands with explanations
- Modify inputs before approval (e.g., adding safety flags)

Security Model:
- Allowlist approach with denylist override
- Dangerous patterns ALWAYS checked first
- Safe patterns use conservative matching
- Unknown commands default to showing dialog

Usage:
    Add to .claude/settings.json:
    {
        "hooks": {
            "PermissionRequest": [{
                "command": "python plugins/conserve/hooks/permission_request.py"
            }]
        }
    }
"""

from __future__ import annotations

import json
import logging
import re
import shlex
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PermissionDecision(Enum):
    """Possible permission decisions."""

    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"  # Show dialog (default)


@dataclass
class Decision:
    """Permission decision with optional message."""

    behavior: PermissionDecision
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to hook output format."""
        result: dict[str, Any] = {"behavior": self.behavior.value}
        if self.message:
            result["message"] = self.message
        return result


# ============================================================================
# Pattern Definitions
# ============================================================================

# A reader that opens the next command in the line, not a word inside a
# flag: `\bgrep` alone matched `git log --grep`. `git show` and
# `git cat-file` print a committed file from `<rev>:<path>`.
_READER_START = (
    r"(?:^|[|;&]\s*)(?:cat|head|tail|grep|rg|ag|git\s+(?:show|cat-file))\b[^|;&]*"
)
# A credential file named as a path token: bare, quoted, after a '/', a
# `<` redirect, a `<rev>:` prefix or an `=`. The names are the files
# cat's own rules below deny (`.env` variants, `*credentials*` files)
# plus the netrc, npm and PyPI token files and private SSH keys (`.pub`
# is not one). A bare search word is not a file: `get_credentials` and
# `os.environ` do not match, while `get_credentials.py` does, as it
# does for cat.
_CRED_NAME = (
    r"(?:[\w.-]*\.env(?:\.[\w.-]+)?|\.envrc"
    r"|(?:[\w.-]*[.-])?credentials(?:\.[\w.-]+)?|[\w.-]*credentials\.[\w.-]+"
    r"|[._]netrc|\.npmrc|\.pypirc|id_(?:rsa|dsa|ecdsa|ed25519))"
)
_CRED_PATH = rf"(?:(?<=\s)|(?<=/)|(?<=['\"<:=])){_CRED_NAME}(?=\s|$|['\"])"
# `git diff` and `git log -p` print a file named as a pathspec, with or
# without a `--` before it. The value of a search option (`--grep`, `-S`,
# `-G`) is a pattern, not a path, so it is excluded.
_GIT_PATHSPEC = (
    r"(?:^|[|;&]\s*)git\s+(?:diff|log)\b[^|;&]*"
    r"(?<!--grep )(?<!--grep=)(?<!-S )(?<!-G )"
)

# DANGEROUS patterns - always deny these
# Order matters: more specific patterns should come first
DANGEROUS_PATTERNS: list[tuple[str, str]] = [
    # Destructive file operations
    (r"rm\s+-rf\s+/(?!\S)", "Blocked: recursive delete on root"),
    (r"rm\s+-rf\s+/\*", "Blocked: recursive delete on root"),
    (r"rm\s+-rf\s+~", "Blocked: recursive delete on home"),
    (r"rm\s+-rf\s+\$HOME", "Blocked: recursive delete on home"),
    # Privilege escalation
    (r"^sudo\s+", "Blocked: sudo requires explicit approval"),
    (r"\|\s*sudo\s+", "Blocked: piped sudo is dangerous"),
    # Remote code execution
    (r"curl\s+.*\|\s*(bash|sh|zsh)", "Blocked: pipe-to-shell pattern"),
    (r"wget\s+.*\|\s*(bash|sh|zsh)", "Blocked: pipe-to-shell pattern"),
    (r"curl\s+.*>\s*/", "Blocked: curl to root path"),
    # Fork bombs and resource exhaustion
    (r":\(\)\{.*:\|:.*\}", "Blocked: fork bomb detected"),
    (r"while\s+true\s*;\s*do.*done", "Blocked: infinite loop pattern"),
    # Credential exposure
    (r"cat\s+.*\.env", "Blocked: potential credential exposure"),
    (r"cat\s+.*credentials", "Blocked: potential credential exposure"),
    (r"cat\s+.*/\.ssh/", "Blocked: SSH key exposure"),
    # Every reader, cat included, is denied a credential file by name.
    # cat's two rules above go further and match `.env` or `credentials`
    # anywhere in its arguments, a search word included, which is too
    # broad for grep and rg, whose first operand is a pattern.
    (rf"{_READER_START}{_CRED_PATH}", "Blocked: potential credential exposure"),
    (rf"{_GIT_PATHSPEC}{_CRED_PATH}", "Blocked: potential credential exposure"),
    (rf"{_READER_START}/\.ssh(?=/|\s|$|['\"])", "Blocked: SSH key exposure"),
    # Git dangerous operations
    (r"git\s+push\s+.*--force\s+origin\s+(main|master)", "Blocked: force push to main"),
    (r"git\s+reset\s+--hard\s+origin/", "Blocked: hard reset from remote"),
]

# SAFE patterns - auto-approve these
# These are read-only or low-risk operations
SAFE_PATTERNS: list[str] = [
    # File system inspection (read-only)
    r"^ls(\s|$)",
    r"^pwd$",
    # A device file (`/dev/zero`) or follow mode never returns, so it
    # burns the Bash timeout instead of being approved.
    r"^cat\s+(?!.*\.env|.*credentials|.*\.ssh|.*/dev/)",
    r"^head\s+",
    r"^tail\s+(?!(?:.*\s)?(?:-\w*[fF]|--follow))",
    r"^wc\s+",
    # -C/--compile writes a compiled magic file.
    r"^file\s+(?!(?:.*\s)?-\w*C|.*--compile)",
    r"^stat\s+",
    r"^realpath\s+",
    r"^dirname\s+",
    r"^basename\s+",
    # Search operations (read-only)
    r"^grep\s+",
    r"^rg\s+",
    r"^ag\s+",
    # find is read-only only without an action: -delete, -exec and friends
    # run or remove things, and -fprint/-fls write files.
    r"^find\s+(?!.*\s-(delete|exec|execdir|ok|okdir|fprint|fprint0|fprintf|fls)\b)"
    r".*-(name|type)\s+",
    r"^which\s+",
    r"^whereis\s+",
    r"^type\s+",
    # Git read operations
    r"^git\s+status(\s|$)",
    r"^git\s+log(\s|$)",
    r"^git\s+diff(\s|$)",
    # Listing flags only: -d/-D/-m/-c delete, rename or copy, and a bare
    # name creates a branch.
    r"^git\s+branch(\s+(-a|-r|-v|-vv|--all|--remotes|--list|--verbose"
    r"|--show-current|--merged|--no-merged))*$",
    r"^git\s+show(\s|$)",
    r"^git\s+remote\s+-v$",
    r"^git\s+rev-parse(\s|$)",
    r"^git\s+describe(\s|$)",
    # A manual page, with an optional section and no options: -P/--pager
    # and -H/--html name a program for man to run.
    r"^man\s+(?:\d\w*\s+)?[\w.:+-]+$",
    # Help for a bare command or a known tool's subcommand. A help flag
    # after an operand is not help everywhere: BSD rm takes `--help` in
    # `rm build --help` as a file name and removes `build`.
    r"^[\w.-]+\s+--help$",
    r"^(git|uv|npm|pip|cargo|gh|docker|kubectl|claude|make)\s+[a-z][\w-]*\s+--help$",
    # -h is help only for tools where it means help; `shutdown -h` halts.
    r"^(git|uv|npm|pip|cargo|gh|docker|kubectl|claude|make|pytest|ruff|rg)\s+-h$",
    r"^help\s+",
    # Environment inspection. Only named variables that never hold a
    # secret: `env`, `printenv` and `echo $ANY_KEY` put API keys in the
    # transcript, so they fall through to the dialog.
    r"^echo\s+\$\{?(PATH|HOME|PWD|SHELL|USER|TERM|LANG|TMPDIR|VIRTUAL_ENV)\}?$",
    # Python/Node read operations
    r"^python\s+--version$",
    r"^python3\s+--version$",
    r"^node\s+--version$",
    r"^npm\s+--version$",
    r"^uv\s+--version$",
    r"^pip\s+--version$",
    # Package info (read-only)
    r"^pip\s+show\s+",
    r"^npm\s+list(\s|$)",
    r"^uv\s+pip\s+list(\s|$)",
]


def check_dangerous(command: str) -> Decision | None:
    """Check if command matches dangerous patterns.

    Args:
        command: The command string to check.

    Returns:
        Decision to deny if dangerous, None otherwise.

    """
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            logger.info("Dangerous pattern matched: %s", pattern)
            return Decision(PermissionDecision.DENY, message)
    return None


# Shell metacharacters that indicate command chaining: never auto-approve.
#
# A newline separates commands exactly as a semicolon does, and omitting it
# here was a bypass rather than a gap: ``check_safe`` matches with
# ``re.match``, which anchors only at the start, and ``^ls(\s|$)`` accepts a
# newline through ``\s``. ``ls\nrm -rf ./important_dir`` therefore
# auto-approved on the strength of its first token.
_CHAIN_CHARS = re.compile(r"[;|&`(\n\r>]|\$\(")

# Options that make a read-only command write a file or run a program:
# `git diff --output=FILE` writes, `rg --pre CMD` executes CMD per file,
# `git diff --ext-diff` runs the external diff the repo configures,
# `git diff --no-index` reads any two paths outside the repo,
# `ag --pager CMD` pipes results through CMD, and `rg --hostname-bin CMD`
# runs CMD to fill in hyperlinks.
_WRITE_OR_EXEC_OPTIONS = re.compile(
    r"(^|\s)--(output|pre|ext-diff|no-index|pager|hostname-bin)(=|\s|$)"
)


# The shell rewrites a command before it runs. Quotes and backslashes
# hide a name from the deny list (`cat .e''nv` runs `cat .env`), and a
# glob, brace or variable names a file the text never spells out
# (`cat .e?v`, `cat $F`). Readers and searchers with such an operand
# fall through to the dialog.
_EXPANDING = re.compile(r"[*?\[{$]")
_READERS = frozenset(
    {"cat", "head", "tail", "wc", "file", "stat", "realpath", "dirname", "basename"}
)


@dataclass(frozen=True)
class _SearchSyntax:
    """Which options of one search tool consume the next word.

    The same letter means different things to each tool: `grep -T` and
    `ag -t` take no value, while `rg -T` and `rg -t` do. Counting a flag
    as value-taking when it is not hides the real path behind it. A flag
    is listed only when the tool's own documentation says it requires a
    value.
    """

    value_flags: frozenset[str]
    # Options that supply the pattern, so no positional is the pattern:
    # `grep -e token FILE`, `grep -etoken FILE`, `grep --regexp=token FILE`.
    pattern_flags: frozenset[str]
    # Short value options that end a `-ie` style cluster.
    value_letters: frozenset[str]
    # Short pattern options. Inside a cluster the rest is the pattern.
    pattern_letters: frozenset[str]
    # Short options whose value counts only when it is a number. Any other
    # word, attached or not, is the search pattern instead.
    number_letters: frozenset[str] = frozenset()


# grep: the GNU grep manual and BSD grep(1). `-T` is --initial-tab, and
# --context is left out because both document only `--context=NUM`.
# rg: `rg --help`. ag: the getopt string in ag's src/options.c, where
# `-t` is --all-text, `-f` is --follow, `-g PATTERN` replaces the search
# pattern, and the long --after, --before and --context take a value
# only after `=`. ag's `-A`, `-B` and `-C` keep their value only when it
# parses as a number, and otherwise read it as the search pattern.
_SEARCH_SYNTAX = {
    "grep": _SearchSyntax(
        value_flags=frozenset(
            {
                "-e",
                "--regexp",
                "-f",
                "--file",
                "-m",
                "--max-count",
                "-A",
                "-B",
                "-C",
                "--include",
                "--exclude",
                "--exclude-dir",
            }
        ),
        pattern_flags=frozenset({"-e", "--regexp", "-f", "--file"}),
        value_letters=frozenset("mABC"),
        pattern_letters=frozenset("ef"),
    ),
    "rg": _SearchSyntax(
        value_flags=frozenset(
            {
                "-e",
                "--regexp",
                "-f",
                "--file",
                "-g",
                "--glob",
                "--iglob",
                "-t",
                "--type",
                "-T",
                "--type-not",
                "-m",
                "--max-count",
                "-A",
                "-B",
                "-C",
                "--context",
            }
        ),
        pattern_flags=frozenset({"-e", "--regexp", "-f", "--file"}),
        value_letters=frozenset("gtTmABC"),
        pattern_letters=frozenset("ef"),
    ),
    "ag": _SearchSyntax(
        value_flags=frozenset(
            {
                "-G",
                "--file-search-regex",
                "-g",
                "-m",
                "--max-count",
                "-p",
                "--path-to-ignore",
                "-W",
                "--width",
                "--depth",
                "--ignore",
            }
        ),
        pattern_flags=frozenset({"-g"}),
        value_letters=frozenset("GmpW"),
        pattern_letters=frozenset("g"),
        number_letters=frozenset("ABC"),
    ),
}
_SEARCHERS = frozenset(_SEARCH_SYNTAX)
# Modes that take no pattern at all: `rg --files PATH`.
_PATTERNLESS_MODES = frozenset({"--files", "--type-list"})


def _shell_words(command: str) -> list[str] | None:
    """Split *command* as the shell would, or None when it will not parse."""
    try:
        return shlex.split(command)
    except ValueError:
        return None


def _scan_cluster(cluster: str, syntax: _SearchSyntax) -> tuple[bool, bool, bool]:
    """Read a short option cluster such as `-ie` or `-ietoken`.

    Returns whether it supplies the pattern, whether the next word is its
    value, and whether the next word is its value only if it is a number.
    """
    for index, letter in enumerate(cluster):
        if letter in syntax.value_letters:
            break
        if letter in syntax.number_letters:
            attached = cluster[index + 1 :]
            if not attached:
                return False, False, True
            # `ag -Ctoken`: the whole word is the pattern.
            return not attached.isdigit(), False, False
        if letter in syntax.pattern_letters:
            return True, index == len(cluster) - 1, False
    return False, False, False


def _path_operands(words: list[str]) -> list[str]:
    """Return the operands of a reader or searcher that name files."""
    head, rest = words[0], words[1:]
    if head in _READERS:
        return [word for word in rest if not word.startswith("-")]
    if head not in _SEARCHERS:
        return []
    syntax = _SEARCH_SYNTAX[head]
    positional: list[str] = []
    takes_value = False
    takes_number = False
    pattern_given = False
    for word in rest:
        if takes_value:
            takes_value = False
            continue
        if takes_number:
            takes_number = False
            if word.isdigit():
                continue
        if word in syntax.value_flags:
            takes_value = True
            pattern_given = pattern_given or word in syntax.pattern_flags
        elif word in _PATTERNLESS_MODES:
            pattern_given = True
        elif word.startswith("--"):
            pattern_given = (
                pattern_given or word.split("=", 1)[0] in syntax.pattern_flags
            )
        elif word.startswith("-"):
            supplies, takes_value, takes_number = _scan_cluster(word[1:], syntax)
            pattern_given = pattern_given or supplies
        else:
            positional.append(word)
    # Without a pattern option, the first positional is the pattern.
    return positional if pattern_given else positional[1:]


def check_safe(command: str) -> Decision | None:
    """Check if command matches safe patterns.

    Rejects commands containing shell chaining metacharacters
    (;, |, &&, ``, $(), newline) even if the prefix looks safe, to
    prevent auto-approving ``ls; dangerous_command``.

    Args:
        command: The command string to check.

    Returns:
        Decision to allow if safe, None otherwise.

    """
    # Trailing whitespace is not a chain, so it is removed before the test;
    # a newline anywhere else is treated as the separator it is.
    candidate = command.strip()

    # Commands with chaining, substitution or an output redirect (`>`
    # writes a file) never get auto-approved.
    if _CHAIN_CHARS.search(candidate) or _WRITE_OR_EXEC_OPTIONS.search(candidate):
        return None

    words = _shell_words(candidate)
    if not words or any(_EXPANDING.search(op) for op in _path_operands(words)):
        return None

    for pattern in SAFE_PATTERNS:
        if re.match(pattern, candidate, re.IGNORECASE):
            logger.debug("Safe pattern matched: %s", pattern)
            return Decision(PermissionDecision.ALLOW)
    return None


def evaluate_permission(tool_name: str, tool_input: dict[str, Any]) -> Decision | None:
    """Evaluate permission request and return decision.

    Args:
        tool_name: The Claude Code tool being invoked (e.g., "Bash").
        tool_input: The tool input parameters.

    Returns:
        Decision if determined, None to show dialog.

    """
    # Only process Bash commands for now
    if tool_name != "Bash":
        return None

    command = tool_input.get("command", "")
    if not command:
        return None

    # Dangerous patterns take priority, on the text and on what the shell
    # makes of it once quotes and backslashes are removed.
    dangerous = check_dangerous(command)
    if dangerous:
        return dangerous
    words = _shell_words(command)
    if words and " ".join(words) != command:
        dangerous = check_dangerous(" ".join(words))
        if dangerous:
            return dangerous

    # Then check safe patterns
    safe = check_safe(command)
    if safe:
        return safe

    # Unknown - show dialog
    return None


def format_hook_output(decision: Decision | None) -> dict[str, Any]:
    """Format decision as hook-compatible output.

    Args:
        decision: The permission decision, or None for default behavior.

    Returns:
        Dictionary suitable for hook JSON output.

    """
    output: dict[str, Any] = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
        }
    }

    if decision:
        output["hookSpecificOutput"]["decision"] = decision.to_dict()

    return output


def main() -> int:
    """Execute hook entry point.

    Returns:
        Exit code (0 for success).

    """
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse hook input as JSON: %s", e)
        # Return empty output to show default dialog
        print(json.dumps(format_hook_output(None)))
        return 0

    # Extract tool information
    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Evaluate permission
    decision = evaluate_permission(tool_name, tool_input)

    # Output result
    print(json.dumps(format_hook_output(decision)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
