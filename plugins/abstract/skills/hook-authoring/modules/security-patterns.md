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

    # Allowed base paths for file operations
    ALLOWED_PATHS = [
        Path.home(),
        Path("/tmp"),
        Path.cwd(),
    ]

    # Maximum input sizes
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

        # Length check
        if len(command) > self.MAX_COMMAND_LENGTH:
            raise ValueError(f"Command too long: {len(command)} > {self.MAX_COMMAND_LENGTH}")

        # Dangerous pattern detection
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r':(){ :|:& };:',  # Fork bomb
            r'dd\s+if=/dev/zero',
            r'chmod\s+777',
            r'curl.*\|\s*bash',  # Pipe to bash
            r'wget.*\|\s*sh',
        ]

        import re
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise ValueError(f"Dangerous command pattern detected: {pattern}")

        return None

    def _validate_read_input(self, tool_input: dict) -> dict | None:
        """Validate Read tool inputs."""
        file_path = tool_input.get("file_path", "")

        # Validate path safety
        if not self._is_safe_path(file_path):
            raise ValueError(f"Path access denied: {file_path}")

        # Check file size
        try:
            path = Path(file_path).resolve()
            if path.is_file() and path.stat().st_size > self.MAX_FILE_SIZE:
                raise ValueError(f"File too large: {path.stat().st_size} bytes")
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot access path: {e}")

        return None

    def _validate_edit_input(self, tool_input: dict) -> dict | None:
        """Validate Edit tool inputs."""
        file_path = tool_input.get("file_path", "")

        # Path safety
        if not self._is_safe_path(file_path):
            raise ValueError(f"Edit access denied: {file_path}")

        # Protected paths
        protected_patterns = [
            r'/etc/',
            r'/sys/',
            r'/proc/',
            r'\.ssh/',
            r'production/',
        ]

        import re
        for pattern in protected_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                raise ValueError(f"Cannot edit protected path: {file_path}")

        return None

    def _is_safe_path(self, path_str: str) -> bool:
        """Validate path is under allowed base directories."""
        try:
            path = Path(path_str).resolve(strict=False)

            # Check against allowed paths
            for allowed in self.ALLOWED_PATHS:
                try:
                    path.relative_to(allowed)
                    return True
                except ValueError:
                    continue

            return False

        except (OSError, ValueError):
            return False
```

### Parameterization vs String Concatenation

Always use parameterized approaches instead of string concatenation:

```python
#  UNSAFE: String concatenation
command = f"grep {user_pattern} {file_path}"  # Injection risk!

#  SAFE: Parameterized execution
import shlex
safe_command = ["grep", user_pattern, file_path]
```

## Secret Protection

### Never Log Secrets

Implement comprehensive secret sanitization:

```python
import re
from typing import Pattern
from claude_agent_sdk import AgentHooks

class SecretProtectionHooks(AgentHooks):
    """Protect secrets in logs and outputs."""

    # Comprehensive secret patterns
    SECRET_PATTERNS: list[Pattern[str]] = [
        # API Keys
        re.compile(r'(api[_-]?key["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(AKIA[0-9A-Z]{16})'),  # AWS access key

        # Tokens
        re.compile(r'(token["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(bearer\s+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(ghp_[a-zA-Z0-9]{36})'),  # GitHub token

        # Passwords
        re.compile(r'(password["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(passwd["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),

        # Private Keys
        re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----'),

        # Database URLs
        re.compile(r'(postgresql://[^:]+:)([^@]+)(@)', re.IGNORECASE),
        re.compile(r'(mysql://[^:]+:)([^@]+)(@)', re.IGNORECASE),

        # Generic secrets
        re.compile(r'(secret["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
        re.compile(r'(credential[s]?["\s:=]+)([^\s,}"\n]+)', re.IGNORECASE),
    ]

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Sanitize secrets from output before logging."""
        # Sanitize output
        safe_output = self._sanitize_secrets(tool_output)

        # Log with sanitized content
        await self._log_operation(tool_name, safe_output)

        # Don't modify actual output
        return None

    def _sanitize_secrets(self, text: str) -> str:
        """Remove secrets from text."""
        sanitized = text

        for pattern in self.SECRET_PATTERNS:
            if pattern.groups >= 2:
                # Pattern with capture groups (preserve prefix)
                sanitized = pattern.sub(r'\1***REDACTED***', sanitized)
            else:
                # Pattern without groups (full match)
                sanitized = pattern.sub('***REDACTED***', sanitized)

        return sanitized

    async def _log_operation(self, tool_name: str, output: str) -> None:
        """Log operation with sanitized output."""
        # Log safely...
        pass
```

### Environment Variable Protection

```python
import os
from claude_agent_sdk import AgentHooks

class EnvProtectionHooks(AgentHooks):
    """Protect sensitive environment variables."""

    # Environment variables that should never be logged
    SENSITIVE_ENV_VARS = {
        'AWS_SECRET_ACCESS_KEY',
        'AWS_SESSION_TOKEN',
        'GITHUB_TOKEN',
        'API_KEY',
        'PASSWORD',
        'SECRET',
        'PRIVATE_KEY',
    }

    async def on_post_tool_use(
        self, tool_name: str, tool_input: dict, tool_output: str
    ) -> str | None:
        """Redact sensitive environment variables from output."""
        if tool_name == "Bash" and "env" in tool_input.get("command", ""):
            sanitized = self._redact_env_vars(tool_output)
            return sanitized

        return None

    def _redact_env_vars(self, env_output: str) -> str:
        """Redact sensitive environment variables."""
        lines = env_output.split('\n')
        sanitized_lines = []

        for line in lines:
            if '=' in line:
                var_name = line.split('=')[0]
                if any(sensitive in var_name.upper() for sensitive in self.SENSITIVE_ENV_VARS):
                    sanitized_lines.append(f"{var_name}=***REDACTED***")
                    continue

            sanitized_lines.append(line)

        return '\n'.join(sanitized_lines)
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
            # Resolve to absolute path (handles .., symlinks, etc.)
            path = Path(path_str).resolve(strict=False)

            # Check if under any allowed root
            for allowed_root in self.allowed_roots:
                try:
                    # Will raise ValueError if not relative to root
                    path.relative_to(allowed_root)
                    return True
                except ValueError:
                    continue

            return False

        except (OSError, ValueError, RuntimeError):
            # Any error in path resolution = deny
            return False

    def _normalize_path(self, path_str: str) -> Path:
        """Safely normalize a path."""
        # Remove null bytes (used in some attacks)
        cleaned = path_str.replace('\0', '')

        # Resolve to absolute path
        return Path(cleaned).resolve()
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
        self._call_history: defaultdict[str, list[float]] = defaultdict(list)

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Enforce rate limits on tool usage."""
        now = time.time()
        minute_ago = now - 60

        # Clean old entries
        self._call_history[tool_name] = [
            ts for ts in self._call_history[tool_name]
            if ts > minute_ago
        ]

        # Check rate limit
        if len(self._call_history[tool_name]) >= self.max_calls:
            raise ValueError(
                f"Rate limit exceeded for {tool_name}: "
                f"{len(self._call_history[tool_name])} calls/minute"
            )

        # Record this call
        self._call_history[tool_name].append(now)

        return None
```

### Timeout Enforcement

```python
import asyncio
from claude_agent_sdk import AgentHooks

class TimeoutHooks(AgentHooks):
    """Enforce timeouts on hook operations."""

    VALIDATION_TIMEOUT = 5.0  # seconds
    LOGGING_TIMEOUT = 10.0

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Validate with timeout."""
        try:
            return await asyncio.wait_for(
                self._validate(tool_input),
                timeout=self.VALIDATION_TIMEOUT
            )

        except asyncio.TimeoutError:
            # Log timeout but don't block
            logger.warning(f"Validation timeout for {tool_name}")
            return None

    async def _validate(self, tool_input: dict) -> dict | None:
        """Validation logic with timeout protection."""
        # Validation code...
        return None
```

## Injection Prevention

### Log Injection Prevention

```python
from claude_agent_sdk import AgentHooks

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
        # Remove control characters
        sanitized = ''.join(char for char in content if char.isprintable() or char in '\n\r\t')

        # Escape log injection patterns
        sanitized = sanitized.replace('\n', '\\n')
        sanitized = sanitized.replace('\r', '\\r')

        # Limit length to prevent log flooding
        max_log_length = 10_000
        if len(sanitized) > max_log_length:
            sanitized = sanitized[:max_log_length] + f"... (truncated {len(sanitized) - max_log_length} chars)"

        return sanitized

    async def _safe_log(self, tool_name: str, content: str) -> None:
        """Write sanitized content to log."""
        # Safe logging implementation...
        pass
```

### Command Injection Prevention

```python
import shlex
from claude_agent_sdk import AgentHooks

class CommandSanitizationHooks(AgentHooks):
    """Prevent command injection in hooks."""

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Sanitize command inputs."""
        if tool_name == "Bash":
            command = tool_input.get("command", "")

            # Check for shell injection attempts
            if self._has_injection_risk(command):
                raise ValueError("Potential command injection detected")

        return None

    def _has_injection_risk(self, command: str) -> bool:
        """Detect potential injection patterns."""
        risky_patterns = [
            ';',      # Command chaining
            '&&',     # Conditional execution
            '||',     # Conditional execution
            '`',      # Command substitution
            '$(',     # Command substitution
            '>',      # Output redirection
            '<',      # Input redirection
            '|',      # Piping
        ]

        # More sophisticated check needed for production
        return any(pattern in command for pattern in risky_patterns)
```

## Sandbox Awareness

### Respect Sandbox Boundaries

```python
from claude_agent_sdk import AgentHooks

class SandboxAwareHooks(AgentHooks):
    """Respect sandbox restrictions."""

    async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
        """Enforce sandbox boundaries."""
        if tool_name == "Bash":
            command = tool_input.get("command", "")

            # Block sandbox escape attempts
            escape_patterns = [
                'chroot',
                'docker',
                'kubectl',
                'ssh',
                'sudo',
                'su ',
            ]

            if any(pattern in command.lower() for pattern in escape_patterns):
                raise ValueError(f"Sandbox escape attempt blocked")

        return None
```

## Security Checklist

Before deploying hooks, verify:

- [ ] **Input Validation**: All inputs validated and sanitized
- [ ] **Secret Protection**: No secrets in logs or outputs
- [ ] **Path Validation**: Paths restricted to allowed directories
- [ ] **Rate Limiting**: Resource usage limits enforced
- [ ] **Timeout Protection**: All operations have timeouts
- [ ] **Error Handling**: Errors fail safe (allow operation)
- [ ] **Injection Prevention**: All outputs sanitized
- [ ] **Sandbox Respect**: No escape attempts
- [ ] **Least Privilege**: Minimal permissions required
- [ ] **Audit Logging**: Security events logged

## Common Vulnerabilities

### Vulnerability: Secret in Logs

```python
#  VULNERABLE
async def on_post_tool_use(self, tool_name: str, tool_input: dict, tool_output: str) -> str | None:
    print(f"Tool output: {tool_output}")  # May contain secrets!
    return None

#  SECURE
async def on_post_tool_use(self, tool_name: str, tool_input: dict, tool_output: str) -> str | None:
    safe_output = self._sanitize_secrets(tool_output)
    print(f"Tool output: {safe_output}")
    return None
```

### Vulnerability: Path Traversal

```python
#  VULNERABLE
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    file_path = tool_input.get("file_path")
    if "/etc" in file_path:  # Insufficient check!
        raise ValueError("Cannot access /etc")
    return None

#  SECURE
async def on_pre_tool_use(self, tool_name: str, tool_input: dict) -> dict | None:
    file_path = Path(tool_input.get("file_path")).resolve()
    if not self._is_path_allowed(file_path):
        raise ValueError(f"Path access denied")
    return None
```

### Vulnerability: Command Injection

```python
#  VULNERABLE
command = f"grep {user_input} file.txt"  # Injection risk!

#  SECURE
import shlex
command = ["grep", user_input, "file.txt"]
```

## Related Modules

- **hook-types.md**: Event types and signatures
- **sdk-callbacks.md**: SDK implementation patterns
- **performance-guidelines.md**: Performance optimization
- **testing-hooks.md**: Security testing strategies
