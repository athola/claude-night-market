# Security Patterns for Hook Development

Comprehensive security guidance for writing safe, secure hooks that protect agents and systems from vulnerabilities.

## Security Principles

### Core Security Rules

1. **Input Validation**: Always validate and sanitize inputs before processing
2. **No Secret Logging**: Never log API keys, tokens, passwords, or credentials
3. **Sandbox Awareness**: Respect sandbox boundaries, don't attempt escapes
4. **Fail-Safe Defaults**: Return None on errors instead of blocking
5. **Rate Limiting**: Prevent hook abuse through resource limits
6. **Injection Prevention**: Sanitize all outputs to prevent injection attacks

## Threat Model

### Hook-Specific Threats

| Threat | Description | Mitigation |
|--------|-------------|------------|
| **Command Injection** | Malicious input executing shell commands | Input validation, parameterization |
| **Secret Leakage** | Credentials in logs or outputs | Sanitization, pattern matching |
| **Path Traversal** | Access files outside allowed directories | Path validation, allowlists |
| **Resource Exhaustion** | Excessive hook execution consuming resources | Timeouts, rate limits |
| **Privilege Escalation** | Hooks gaining unauthorized access | Least privilege, sandboxing |
| **Log Injection** | Malicious data corrupting logs | Output sanitization |

## Input Validation

### Validate All Inputs

Never trust tool inputs without validation:

```python
from pathlib import Path
from claude_agent_sdk import AgentHooks

class SecureValidationHooks(AgentHooks):
    """Secure input validation patterns."""

    ALLOWED_PATHS = [Path.home(), Path("/tmp"), Path.cwd()]
    MAX_COMMAND_LENGTH = 10_000
    MAX_FILE_SIZE = 100_000_000  # 100MB

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Validate all tool inputs."""
        if tool_name == "Bash":
            return self._validate_bash_input(tool_input)
        elif tool_name == "Read":
            return self._validate_read_input(tool_input)
        elif tool_name == "Edit":
            return self._validate_edit_input(tool_input)
        return None

    def _validate_bash_input(self, tool_input: dict) -> dict | None:
        """Validate Bash command inputs."""
        command = tool_input.get("command", "")

        if len(command) > self.MAX_COMMAND_LENGTH:
            raise ValueError(f"Command too long: {len(command)} > {self.MAX_COMMAND_LENGTH}")

        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r':(){ :|:& };:',  # Fork bomb
            r'dd\s+if=/dev/zero',
            r'chmod\s+777',
            r'curl.*\|\s*bash',
            r'wget.*\|\s*sh',
        ]

        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValueError(f"Dangerous command pattern detected: {pattern}")

        return None
```

### Parameterization vs String Concatenation

Always use parameterized approaches:

```python
# UNSAFE: String concatenation
command = f"grep {user_pattern} {file_path}"  # Injection risk!

# SAFE: Parameterized execution
import shlex
safe_command = ["grep", user_pattern, file_path]
```

## Secret Protection

### Never Log Secrets

Implement comprehensive secret sanitization:

```python
import re
from claude_agent_sdk import AgentHooks

class SecretProtectionHooks(AgentHooks):
    """Protect secrets in logs and outputs."""

    SECRET_PATTERNS = [
        re.compile(r'(api[_-]?key["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(AKIA[0-9A-Z]{16})'),  # AWS access key
        re.compile(r'(token["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(bearer\s+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(ghp_[a-zA-Z0-9]{36})'),  # GitHub token
        re.compile(r'(password["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----'),
        re.compile(r'(postgresql://[^:]+:)([^@]+)(@)', re.IGNORECASE),
        re.compile(r'(secret["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
    ]

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Sanitize secrets from output before logging."""
        safe_output = self._sanitize_secrets(tool_output)
        await self._log_operation(tool_name, safe_output)
        return None

    def _sanitize_secrets(self, text: str) -> str:
        """Remove secrets from text."""
        sanitized = text
        for pattern in self.SECRET_PATTERNS:
            if pattern.groups >= 2:
                sanitized = pattern.sub(r'\1***REDACTED***', sanitized)
            else:
                sanitized = pattern.sub('***REDACTED***', sanitized)
        return sanitized
```

### Environment Variable Protection

```python
class EnvProtectionHooks(AgentHooks):
    """Protect sensitive environment variables."""

    SENSITIVE_ENV_VARS = {
        'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'GITHUB_TOKEN',
        'API_KEY', 'PASSWORD', 'SECRET', 'PRIVATE_KEY',
    }

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Redact sensitive environment variables from output."""
        if tool_name == "Bash" and "env" in tool_input.get("command", ""):
            return self._redact_env_vars(tool_output)
        return None

    def _redact_env_vars(self, env_output: str) -> str:
        """Redact sensitive environment variables."""
        lines = []
        for line in env_output.split('\n'):
            if '=' in line:
                var_name = line.split('=')[0]
                if any(sensitive in var_name.upper() for sensitive in self.SENSITIVE_ENV_VARS):
                    lines.append(f"{var_name}=***REDACTED***")
                    continue
            lines.append(line)
        return '\n'.join(lines)
```

## Path Traversal Prevention

### Safe Path Validation

```python
from pathlib import Path
from claude_agent_sdk import AgentHooks

class PathSecurityHooks(AgentHooks):
    """Prevent path traversal attacks."""

    def __init__(self, allowed_roots: list[Path]):
        self.allowed_roots = [p.resolve() for p in allowed_roots]

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Validate paths are within allowed directories."""
        if tool_name in ["Read", "Edit", "Write"]:
            file_path = tool_input.get("file_path", "")
            if not self._is_path_allowed(file_path):
                raise ValueError(f"Path access denied: {file_path}")
        return None

    def _is_path_allowed(self, path_str: str) -> bool:
        """Check if path is within allowed roots."""
        try:
            path = Path(path_str).resolve(strict=False)
            for allowed_root in self.allowed_roots:
                try:
                    path.relative_to(allowed_root)
                    return True
                except ValueError:
                    continue
            return False
        except (OSError, ValueError, RuntimeError):
            return False
```

## Resource Limits

### Rate Limiting

```python
import time
from collections import defaultdict
from claude_agent_sdk import AgentHooks

class RateLimitHooks(AgentHooks):
    """Implement rate limiting for hook operations."""

    def __init__(self, max_calls_per_minute: int = 100):
        self.max_calls = max_calls_per_minute
        self._call_history = defaultdict(list)

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Enforce rate limits on tool usage."""
        now = time.time()
        minute_ago = now - 60

        self._call_history[tool_name] = [
            ts for ts in self._call_history[tool_name] if ts > minute_ago
        ]

        if len(self._call_history[tool_name]) >= self.max_calls:
            raise ValueError(
                f"Rate limit exceeded for {tool_name}: "
                f"{len(self._call_history[tool_name])} calls/minute"
            )

        self._call_history[tool_name].append(now)
        return None
```

### Timeout Enforcement

```python
import asyncio
from claude_agent_sdk import AgentHooks

class TimeoutHooks(AgentHooks):
    """Enforce timeouts on hook operations."""

    VALIDATION_TIMEOUT = 5.0
    LOGGING_TIMEOUT = 10.0

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Validate with timeout."""
        try:
            return await asyncio.wait_for(
                self._validate(tool_input),
                timeout=self.VALIDATION_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning(f"Validation timeout for {tool_name}")
            return None
```

## Injection Prevention

### Log Injection Prevention

```python
class LogSanitizationHooks(AgentHooks):
    """Prevent log injection attacks."""

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Sanitize output before logging."""
        safe_output = self._sanitize_log_content(tool_output)
        await self._safe_log(tool_name, safe_output)
        return None

    def _sanitize_log_content(self, content: str) -> str:
        """Sanitize content for safe logging."""
        sanitized = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')
        sanitized = sanitized.replace('\n', '\\n').replace('\r', '\\r')

        max_log_length = 10_000
        if len(sanitized) > max_log_length:
            sanitized = sanitized[:max_log_length] + f"... (truncated {len(sanitized) - max_log_length} chars)"

        return sanitized
```

## Bash Glob Pattern Validation (2.0.71+)

### Permission System Improvements

Claude Code 2.0.71 fixed permission rules to correctly handle valid bash glob patterns (`*.txt`, `*.png`, etc.).

**What Changed**:
- Shell glob patterns like `ls *.txt` now work without permission prompts
- Permission system distinguishes between safe glob patterns and dangerous wildcards
- Standard file operations with pattern matching no longer require workarounds

### Glob Pattern Security

Even with native glob support, hooks should validate glob usage for dangerous patterns:

```python
from claude_agent_sdk import AgentHooks
import re

class GlobValidationHooks(AgentHooks):
    """Validate glob patterns for security concerns."""

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Validate glob patterns in bash commands."""
        if tool_name != "Bash":
            return None

        command = tool_input.get("command", "")

        # DANGEROUS: Destructive operations with unconstrained globs
        dangerous_glob_patterns = [
            r'rm\s+-rf\s+/?\*',
            r'chmod\s+.*\s+/?\*',
            r'chown\s+.*\s+/?\*',
            r'mv\s+\*\s+/',
            r'for\s+\w+\s+in\s+/?\*;\s*do\s+rm',
        ]

        for pattern in dangerous_glob_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValueError(
                    f"Dangerous glob operation detected. Pattern: {pattern}"
                )

        return None
```

### Safe Glob Usage Examples

```bash
# File operations (natively supported, no permission dialogs)
ls *.txt
cat src/*.py
cp config/*.yaml backup/

# Iteration
for f in *.log; do gzip "$f"; done
for img in images/*.jpg; do convert "$img" -resize 50%; done

# Cleanup operations
rm *.tmp
rm -f build/*.o
find . -name "*.pyc" -delete
```

### Dangerous Glob Patterns to Block

```bash
# BLOCK: Root-level destructive operations
rm -rf /*
rm -rf /var/*
chmod 777 /*

# BLOCK: Unconstrained recursive operations
find / -name "*" -delete
chown -R user:group /*

# BLOCK: Blind glob deletions
rm -rf *
for f in /*; do rm -rf "$f"; done
```

## PermissionRequest Security

### Safe Auto-Approval Patterns

When using PermissionRequest hooks to auto-approve operations:

```python
#!/usr/bin/env python3
import json
import re
import sys

# Allowlist patterns for safe auto-approval
SAFE_READ_COMMANDS = re.compile(r'^(ls|pwd|cat|head|tail|wc|file|stat|which|type)\b')
SAFE_GREP_COMMANDS = re.compile(r'^(grep|rg|ag|ack)\s+.*(?!-[^-]*r)')
SAFE_GIT_COMMANDS = re.compile(r'^git\s+(status|log|diff|branch|show|blame)\b')

# Denylist patterns - ALWAYS block
DANGEROUS_PATTERNS = [
    r'rm\s+-rf\s+/',
    r':(){ :|:& };:',
    r'dd\s+if=/dev/zero',
    r'chmod\s+-R\s+777',
    r'curl.*\|\s*(bash|sh)',
    r'wget.*\|\s*(bash|sh)',
    r'sudo\s+',
    r'su\s+',
]

def is_safe_command(command: str) -> bool:
    """Check if command is safe to auto-approve."""
    # Check denylist first
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False

    # Check allowlist
    if SAFE_READ_COMMANDS.match(command):
        return True
    if SAFE_GREP_COMMANDS.match(command):
        return True
    if SAFE_GIT_COMMANDS.match(command):
        return True

    return False

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "")

        # Check for dangerous patterns first
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PermissionRequest",
                        "decision": {
                            "behavior": "deny",
                            "message": "Blocked: dangerous pattern detected",
                            "interrupt": True
                        }
                    }
                }))
                sys.exit(0)

        # Auto-approve safe commands
        if is_safe_command(command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "decision": {"behavior": "allow"}
                }
            }))
            sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
```

### PermissionRequest Security Principles

1. **Denylist Before Allowlist**: Always check dangerous patterns before safe patterns
2. **Default to Dialog**: If uncertain, let the permission dialog appear
3. **No Regex Bypass**: Use anchored patterns (`^`) to prevent command injection
4. **Audit Auto-Approvals**: Log all automatic approvals for security review
5. **Minimize Scope**: Only auto-approve truly safe, read-only operations
6. **Never Auto-Approve**: Commands with pipes to shells, privilege escalation, system modifications, unconstrained wildcards

## Shell Environment Troubleshooting

Use `CLAUDE_CODE_SHELL` environment variable if hooks fail due to shell detection (added in 2.0.65):

```bash
export CLAUDE_CODE_SHELL=/bin/bash  # or /bin/zsh
```

| Symptom | Solution |
|---------|----------|
| "No suitable shell found" | Set `CLAUDE_CODE_SHELL` |
| Hooks fail on Windows/WSL | Use Unix-style paths |
| Shebang not found | Explicitly set shell path |

For cross-platform compatibility: use `#!/usr/bin/env bash`, stick to POSIX syntax, handle missing commands gracefully.

## Security Checklist

Before deploying: validate inputs, protect secrets, restrict paths, enforce rate limits/timeouts, fail safe on errors, sanitize outputs, respect sandbox, use least privilege, log security events.

## Related Modules

- **hook-types.md**: Event types and signatures
- **sdk-callbacks.md**: SDK implementation patterns
- **testing-hooks.md**: Security testing strategies
