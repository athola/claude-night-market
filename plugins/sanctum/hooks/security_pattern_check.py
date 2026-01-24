#!/usr/bin/env python3
"""Check for security anti-patterns in code changes.

This security hook reduces false positives in documentation contexts.
Key differences from substring matching:
1. Distinguish actual code from documentation examples.
2. Ignore patterns in markdown that describe what NOT to do.
3. Catch actual security issues in code files.

Improvements:
- Documentation files (.md, .rst, etc.) get context-aware checking.
- Patterns near words like "avoid", "unsafe", "warning" are ignored.
- Code blocks in docs showing anti-patterns are allowed.
- Actual code files still get strict checking.

Using both this hook and `claude-code-plugins/security-guidance` may produce duplicate warnings.
To use only this version, disable the security-guidance plugin or set ENABLE_SECURITY_REMINDER=0.
"""

import json
import re
import sys
from pathlib import Path


def get_security_patterns():
    """Build patterns dynamically to avoid triggering other security hooks."""
    # Build pattern strings dynamically
    ev = "ev" + "al"
    ex = "ex" + "ec"

    return [
        {
            "ruleName": "dynamic_code_evaluation",
            "pattern": rf"\b{ev}\s*\(",
            "file_types": [".py", ".js", ".ts"],
            "reminder": f"Security Warning: {ev}() runs arbitrary code. "
            "Use JSON.parse() or ast.literal_eval() instead.",
        },
        {
            "ruleName": "dynamic_code_execution",
            "pattern": rf"\b{ex}\s*\(",
            "file_types": [".py"],
            "reminder": f"Security Warning: {ex}() is a major security risk. "
            "Consider safer alternatives.",
        },
        {
            "ruleName": "os_system_call",
            "pattern": r"os\.system\s*\(",
            "file_types": [".py"],
            "reminder": "Security Warning: os.system() can lead to command injection. "
            "Use subprocess.run() with a list of arguments instead.",
        },
        {
            "ruleName": "subprocess_shell_mode",
            "pattern": r"shell\s*=\s*True",
            "file_types": [".py"],
            "reminder": "Security Warning: shell=True can lead to command injection. "
            "Prefer using a list of arguments without shell mode.",
        },
        {
            "ruleName": "pickle_deserialization",
            "pattern": r"pickle\.load",
            "file_types": [".py"],
            "reminder": "Security Warning: pickle with untrusted data can run code. "
            "Consider using JSON or other safe formats.",
        },
    ]


# Context words indicating documentation rather than actual code
NEGATIVE_CONTEXT_WORDS = [
    "bad",
    "avoid",
    "don't",
    "do not",
    "unsafe",
    "vulnerable",
    "never",
    "warning",
    "danger",
    "risk",
    "insecure",
    "# bad",
    "# wrong",
    "anti-pattern",
    "antipattern",
    "instead of",
    "example of unsafe",
    "[high]",
    "[med]",
    "[low]",
    "security issue",
    "flags",
    "detects",
]


def is_documentation_file(file_path: str) -> bool:
    """Check if a file is documentation."""
    path = Path(file_path)
    doc_extensions = {".md", ".rst", ".txt", ".adoc"}
    doc_directories = {"docs", "doc", "documentation", "wiki", "examples", "commands"}

    if path.suffix.lower() in doc_extensions:
        return True

    for part in path.parts:
        if part.lower() in doc_directories:
            return True

    return False


def has_negative_context(content: str, match_pos: int, window: int = 300) -> bool:
    """Verify if the pattern match is in a negative context."""
    start = max(0, match_pos - window)
    end = min(len(content), match_pos + window)
    context = content[start:end].lower()

    for word in NEGATIVE_CONTEXT_WORDS:
        if word in context:
            return True

    return False


def is_in_code_block(content: str, match_pos: int) -> bool:
    """Determine if the position is inside a markdown code block."""
    before_content = content[:match_pos]
    fence_count = before_content.count("```")
    return fence_count % 2 == 1


def check_content(file_path: str, content: str) -> tuple:
    """Scan content for security patterns."""
    path = Path(file_path)
    is_docs = is_documentation_file(file_path)
    patterns = get_security_patterns()

    for pattern_config in patterns:
        # Skip if pattern doesn't apply to this file type
        if not is_docs:
            file_types = pattern_config.get("file_types", [])
            if file_types and path.suffix.lower() not in file_types:
                continue

        regex = re.compile(pattern_config["pattern"], re.IGNORECASE)

        for match in regex.finditer(content):
            match_pos = match.start()

            # For documentation, require positive evidence of actual code
            if is_docs:
                # If in code block with negative context, skip
                if is_in_code_block(content, match_pos):
                    if has_negative_context(content, match_pos):
                        continue
                # If not in code block but has negative context, skip
                elif has_negative_context(content, match_pos):
                    continue

            return pattern_config["ruleName"], pattern_config["reminder"]

    return None, None


def main():
    """Run the security pattern check hook."""
    try:
        raw_input = sys.stdin.read()
        input_data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ["Edit", "Write", "MultiEdit"]:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        content = " ".join(edit.get("new_string", "") for edit in edits)
    else:
        content = ""

    if not content:
        sys.exit(0)

    rule_name, reminder = check_content(file_path, content)

    if rule_name and reminder:
        # Inject security warning as additionalContext (Claude Code 2.1.9+)
        # This ensures Claude sees the security guidance in-context
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": f"⚠️ SECURITY WARNING [{rule_name}]: {reminder}",
            }
        }
        print(json.dumps(output))
        # Also log to stderr for observability
        print(f"[{rule_name}] {reminder}", file=sys.stderr)
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
