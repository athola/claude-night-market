# Security Essentials for Hooks

## Critical Security Rules

1. **Input Validation**: Always validate tool inputs before processing
2. **No Secret Logging**: Never log API keys, tokens, passwords, or credentials
3. **Sandbox Awareness**: Respect sandbox boundaries, don't escape. Note: `.claude/skills/` is read-only in sandbox mode (2.1.38+)
4. **Fail-Safe Defaults**: Return None on error instead of blocking the agent
5. **Rate Limiting**: Prevent hook abuse from malicious or buggy code
6. **Injection Prevention**: Sanitize all logged content to prevent log injection

## Example: Secure Logging Hook

```python
import re
from claude_agent_sdk import AgentHooks


class SecureLoggingHooks(AgentHooks):
    # Patterns that might contain secrets
    SECRET_PATTERNS = [
        r"api[_-]?key",
        r"password",
        r"token",
        r"secret",
        r"credential",
        r"auth",
    ]

    def _sanitize_output(self, text: str) -> str:
        """Remove potential secrets from log output."""
        for pattern in self.SECRET_PATTERNS:
            text = re.sub(
                rf'({pattern}["\s:=]+)([^\s,}}]+)',
                r"\1***REDACTED***",
                text,
                flags=re.IGNORECASE,
            )
        return text

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Log tool use with sanitization."""
        safe_output = self._sanitize_output(tool_output)
        # Log safe_output...
        return None  # Don't modify output
```
**Verification:** Run the command with `--help` flag to verify availability.
