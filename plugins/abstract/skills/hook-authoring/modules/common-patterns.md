# Common Hook Patterns

## Validation Hook

Block dangerous operations before execution:

```python
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Block dangerous patterns
        if any(pattern in command for pattern in ["rm -rf /", ":(){ :|:& };:"]):
            raise ValueError(f"Dangerous command blocked: {command}")

        # Block production access
        if "production" in command and not self._has_approval():
            raise ValueError("Production access requires approval")

    return None
```
**Verification:** Run the command with `--help` flag to verify availability.

## Logging Hook

Audit all tool operations:

```python
async def on_post_tool_use(
    self, tool_name: str, tool_input: dict, tool_output: str
) -> str | None:
    await self._log_entry(
        {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "input_size": len(str(tool_input)),
            "output_size": len(tool_output),
            "success": True,
        }
    )
    return None
```
**Verification:** Run the command with `--help` flag to verify availability.

## Context Injection Hook

Add relevant context before user prompts:

```python
async def on_user_prompt_submit(self, message: str) -> str | None:
    # Inject project-specific context
    context = await self._load_project_context()
    enhanced_message = f"{context}\n\n{message}"
    return enhanced_message
```

## PreToolUse Context Injection (Claude Code 2.1.9+)

Inject context before a tool executes using `additionalContext`:

```python
#!/usr/bin/env python3
"""PreToolUse hook that injects context before WebFetch."""

import json
import sys


def main():
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name", "")

    if tool_name == "WebFetch":
        url = payload.get("tool_input", {}).get("url", "")
        # Check cache or knowledge base
        cached = lookup_knowledge_base(url)
        if cached:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": f"Relevant cached info: {cached}",
                        }
                    }
                )
            )
    sys.exit(0)


if __name__ == "__main__":
    main()
```

This pattern is useful for: cache hints before web requests, security warnings before risky operations, and injecting relevant project context before file operations.
