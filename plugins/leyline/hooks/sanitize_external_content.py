#!/usr/bin/env python3
"""PostToolUse hook: sanitize external content.

Scans tool outputs from external sources (WebFetch,
WebSearch, gh CLI) for prompt injection and code execution
patterns. High-severity patterns are blocked (fail-closed).
Medium-severity patterns are escaped (fail-open).

Crash-proof: entire hook wrapped in try/except. On any
unhandled error, content passes through unchanged.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

# --- Pattern compilation (module load time) ---

_MAX_SCAN_SIZE = 100 * 1024  # 100KB

_HIGH_SEVERITY = [
    re.compile(p)
    for p in [
        r"(?i)<system[^>]*>",
        r"(?i)<assistant[^>]*>",
        r"(?i)<human[^>]*>",
        r"(?i)<IMPORTANT[^>]*>",
        # A closing tag alone can end a real role block in the prompt.
        # Self-closing forms already match the opening patterns above.
        r"(?i)</\s*(?:system|assistant|human|IMPORTANT)\b[^>]*>",
        r"(?i)system-reminder",
        r"(?i)you\s+are\s+now\b",
        r"(?i)ignore\s+(all\s+)?previous",
        r"(?i)disregard\s+(all\s+)?prior",
        r"(?i)override\s+(your|the)\s+instructions",
        r"(?i)new\s+instructions\s*:",
        r"!!python/",
        r"__import__\s*\(",
        r"(?<![`])eval\s*\(",
        r"(?<![`])exec\s*\(",
        r"__globals__",
        r"__builtins__",
    ]
]

# --- Invisible text injection patterns (high severity) ---

_INVISIBLE_TEXT = [
    re.compile(p)
    for p in [
        r'style\s*=\s*["\'][^"\']*display:\s*none',
        r'style\s*=\s*["\'][^"\']*visibility:\s*hidden',
        r'style\s*=\s*["\'][^"\']*color:\s*(?:white|#fff(?:fff)?)\b',
        r'style\s*=\s*["\'][^"\']*color:\s*rgb\(\s*255',
        r'style\s*=\s*["\'][^"\']*font-size:\s*0\b',
        r'style\s*=\s*["\'][^"\']*opacity:\s*0\b',
        r'style\s*=\s*["\'][^"\']*height:\s*0[^0-9].*overflow:\s*hidden',
    ]
]

_COMMENT_INSTRUCTION = re.compile(r"ignore|override|forget|you are", re.IGNORECASE)


def _instruction_comment_spans(text: str) -> list[tuple[int, int]]:
    """Return ``(start, end)`` of each comment carrying an instruction word.

    Same matches as ``<!--[^>]*(ignore|...)[^>]*-->``, found in one pass.
    That regex retried from every ``<!--`` to the end of the text: a
    100 KB run of ``<!--`` with no ``>`` took 35 seconds. A match cannot
    cross a ``>``, so from each opener the only candidate ends at the
    first ``>`` after it, and every later opener before that ``>`` sees
    a subset of the same text.
    """
    spans = []
    start = text.find("<!--")
    while start != -1:
        close = text.find(">", start + 4)
        if close == -1:
            break
        body_end = close - 2
        if (
            body_end >= start + 4
            and text[body_end : close + 1] == "-->"
            and _COMMENT_INSTRUCTION.search(text, start + 4, body_end)
        ):
            spans.append((start, close + 1))
        start = text.find("<!--", close + 1)
    return spans


# Every Unicode format (Cf) character, as of Unicode 15. None renders,
# so any of them can split "ignore previous" for the scanner while the
# model still reads the phrase: zero-width marks, the word joiner, the
# soft hyphen, bidi controls and the tag block. Spelled out because
# building the class from ``unicodedata`` costs about 0.1s per hook run.
# A test checks it covers the running interpreter's whole Cf category.
# U+FE0F is a variation selector (Mn), not Cf, so emoji keep it.
_INVISIBLE_FORMAT_CHARS = re.compile(
    "[\u00ad\u0600-\u0605\u061c\u06dd\u070f\u0890\u0891\u08e2\u180e"
    "\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u206f\ufeff"
    "\ufff9-\ufffb\U000110bd\U000110cd\U00013430-\U0001343f"
    "\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0001"
    "\U000e0020-\U000e007f]"
)

# What the output loses: the class above minus the joiners. U+200D builds
# emoji sequences and U+200C is required in Persian and several Indic
# scripts, so text with no injection keeps them. Detection still strips
# them, so a joiner cannot split a phrase either.
_HIDDEN_CHARS = re.compile(
    _INVISIBLE_FORMAT_CHARS.pattern.replace("\u200b-\u200f", "\u200b\u200e\u200f")
)

_WHITESPACE_RUN = re.compile(r"\s+")
_SPACE_BEFORE_PAREN = re.compile(r" \(")

_CLOSING_TAG_GAP = re.compile(r"</\s+")

_MEDIUM_SEVERITY = [
    re.compile(p)
    for p in [
        r"(?<![`])IMPORTANT:",
        r"(?<![`])CRITICAL:",
        r"(?i)(?<![`])act\s+as\b",
        r"(?i)(?<![`])pretend\s+you\s+are\b",
    ]
]

_EXTERNAL_BASH_PATTERNS = [
    "gh api",
    "gh issue",
    "gh pr",
    "gh run",
    "gh release",
    "curl ",
    "wget ",
]


def is_external_tool(tool_name: str, tool_input: dict[str, Any]) -> bool:
    """Check if a tool invocation fetches external content."""
    if tool_name in ("WebFetch", "WebSearch"):
        return True
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        return any(pat in cmd for pat in _EXTERNAL_BASH_PATTERNS)
    return False


_FAST_CHECKS = [
    "<system",
    "<assistant",
    "<human",
    "<important",
    "</system",
    "</assistant",
    "</human",
    "</important",
    "!!python",
    "__import__",
    "__globals__",
    "__builtins__",
    "system-reminder",
    "you are now",
    "ignore previous",
    "ignore all previous",
    "disregard",
    "override",
    "new instructions",
    "eval(",
    "exec(",
    'style="display:none',
    "style='display:none",
    'style="display: none',
    "style='display: none",
    'style="visibility:hidden',
    "style='visibility:hidden",
    'style="visibility: hidden',
    "style='visibility: hidden",
    'style="opacity:0',
    "style='opacity:0",
    'style="opacity: 0',
    "style='opacity: 0",
    'style="font-size:0',
    "style='font-size:0",
    'style="font-size: 0',
    "style='font-size: 0",
]

_BLOCKED_LARGE_CONTENT_MESSAGE = (
    "[CONTENT BLOCKED: injection pattern detected in large output]"
)


def _sanitize_large_content(content: str) -> str:
    """Scan oversized content, blocking the whole payload on any match.

    The hidden-text regexes run once over the whole text. Each starts at
    a literal anchor (``<!--`` or ``style``) and can run any length past
    it, which no fixed chunk overlap covers: a comment opening before a
    chunk boundary and closing 2KB after it was never wholly inside one
    chunk. The unanchored role and phrase patterns are too slow at this
    size and become substring checks over overlapping chunks.
    """
    stripped = _INVISIBLE_FORMAT_CHARS.sub("", content)
    # The hidden-text rules have no substring form (any property may
    # precede display:none, any word may sit inside a comment).
    if _instruction_comment_spans(stripped) or any(
        pattern.search(stripped) for pattern in _INVISIBLE_TEXT
    ):
        return _BLOCKED_LARGE_CONTENT_MESSAGE
    chunk_size = _MAX_SCAN_SIZE
    # Longer than every _FAST_CHECKS entry. A whitespace run wider than
    # this between two words of a phrase can still straddle a boundary.
    overlap = 1024
    pos = 0
    while pos < len(stripped):
        end = min(pos + chunk_size, len(stripped))
        raw = stripped[pos:end]
        chunk = raw.lower()
        # The regex patterns accept any whitespace run ("ignore\n
        # previous", "eval (", "</ system>"). Normalize it so the
        # substring checks block the same text.
        chunk = _WHITESPACE_RUN.sub(" ", chunk)
        chunk = _SPACE_BEFORE_PAREN.sub("(", chunk)
        chunk = _CLOSING_TAG_GAP.sub("</", chunk)
        if any(check in chunk for check in _FAST_CHECKS):
            return _BLOCKED_LARGE_CONTENT_MESSAGE
        pos += chunk_size - overlap
    return _HIDDEN_CHARS.sub("", content)


def _sanitize_regular_content(content: str) -> str:
    """Run the full regex-based sanitization pipeline on normal-sized content.

    High-severity and invisible-text patterns are stripped
    (fail-closed). Instruction-bearing HTML comments are
    stripped. Invisible format characters are removed silently.
    Medium-severity patterns are escaped with backticks.
    """
    # Strip first: a format character inside "ignore previous" hides it
    # from every pattern below, then the strip would reassemble the phrase
    # in the output this hook hands to the model.
    stripped = _INVISIBLE_FORMAT_CHARS.sub("", content)
    modified = stripped

    for pattern in _HIGH_SEVERITY:
        modified = pattern.sub("[BLOCKED]", modified)

    for pattern in _INVISIBLE_TEXT:
        modified = pattern.sub("[BLOCKED]", modified)

    for start, end in reversed(_instruction_comment_spans(modified)):
        modified = modified[:start] + "[BLOCKED]" + modified[end:]

    for pattern in _MEDIUM_SEVERITY:
        modified = pattern.sub(lambda m: f"`{m.group(0)}`", modified)

    if modified == stripped:
        return _HIDDEN_CHARS.sub("", content)
    return modified


def sanitize_output(content: str | None) -> str:
    """Sanitize external content for injection patterns.

    High-severity patterns are replaced with [BLOCKED].
    Medium-severity patterns are escaped with backticks.
    Returns empty string for None or non-string input.
    For content over _MAX_SCAN_SIZE, the role and phrase checks
    become fast substring checks, and any match blocks the payload.
    """
    if not content or not isinstance(content, str):
        return ""

    if len(content) > _MAX_SCAN_SIZE:
        return _sanitize_large_content(content)

    return _sanitize_regular_content(content)


def _nested_strings(node: Any) -> list[str]:
    """Every string in ``node``, depth first, without recursion.

    A response nested past the interpreter's recursion limit would
    otherwise raise, and ``main`` fails open on an exception.
    """
    found: list[str] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, str):
            if current:
                found.append(current)
        elif isinstance(current, dict):
            # Keys too: nested API JSON can carry attacker-chosen keys.
            stack.extend(reversed([part for pair in current.items() for part in pair]))
        elif isinstance(current, list):
            stack.extend(reversed(current))
    return found


def _sanitized_like(node: Any) -> Any:
    """Copy ``node`` with each string value sanitized and its shape kept.

    Claude Code ignores an ``updatedToolOutput`` that does not match the
    tool's output schema, so keys and non-string values are left alone.
    """
    if isinstance(node, str):
        return sanitize_output(node) if node else node
    if isinstance(node, dict):
        return {key: _sanitized_like(value) for key, value in node.items()}
    if isinstance(node, list):
        return [_sanitized_like(child) for child in node]
    return node


def _response_text(tool_response: Any) -> str:
    """Flatten a PostToolUse ``tool_response`` (str, dict or list) to text.

    Every string in a dict, key or value, is kept: an injection in Bash
    ``stderr`` or any other field reaches the model as surely as one in
    ``stdout``.
    """
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, (dict, list)):
        return "\n".join(_nested_strings(tool_response))
    return ""


def process_hook(payload: dict[str, Any]) -> dict[str, Any]:
    """Process a PostToolUse hook payload.

    Returns ALLOW for all tools. For external tools with
    detected injection patterns, returns the sanitized result
    as ``updatedToolOutput``, which replaces the raw one, and
    repeats it as additionalContext.
    """
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})

    if not is_external_tool(tool_name, tool_input):
        return {}

    tool_output = _response_text(payload.get("tool_response", ""))
    if not tool_output:
        return {}

    sanitized = sanitize_output(tool_output)

    if sanitized != tool_output:
        sys.stderr.write(f"[sanitize] Modified output from {tool_name}\n")
        hook_output: dict[str, Any] = {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "--- SANITIZED EXTERNAL CONTENT "
                f"[source: {tool_name}] ---\n"
                f"{sanitized}\n"
                "--- END SANITIZED CONTENT ---"
            ),
        }
        response = payload.get("tool_response", "")
        try:
            replacement = _sanitized_like(response)
        except RecursionError:
            # Nesting this deep is not a real tool result. The context
            # above still carries the block, so only the swap is lost.
            replacement = response
        if replacement != response:
            hook_output["updatedToolOutput"] = replacement
        return {"hookSpecificOutput": hook_output}

    return {}


def main() -> None:
    """Hook entry point. On errors, allows content with a safety warning."""
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError) as e:
        # Parse errors: allow content through (can't process)
        sys.stderr.write(f"[sanitize] Input parse error: {e}\n")
        print(json.dumps({}))
        return

    try:
        result = process_hook(payload)
        print(json.dumps(result))
    except Exception as e:
        # Processing errors: allow with caution warning
        sys.stderr.write(f"[sanitize] Processing error: {e}\n")
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            "[SANITIZE HOOK ERROR] Content could not be "
                            "verified as safe. Treat with caution."
                        ),
                    },
                }
            )
        )


if __name__ == "__main__":
    main()
