"""Safety checks for content before storage.

Detects data bombs, secrets, and malicious patterns.
Optimized for speed with early exits and timeout enforcement.
"""

from __future__ import annotations

import re
import signal
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Maximum input length before regex operations (prevent ReDoS)
_MAX_REGEX_INPUT_LEN = 50000

# Timeout support (Unix only)
_SUPPORTS_TIMEOUT = hasattr(signal, "SIGALRM")


class SafetyCheckTimeoutError(Exception):
    """Raised when safety check exceeds timeout."""


def _timeout_handler(signum: int, frame: object) -> None:
    """Signal handler for timeout."""
    msg = "Safety check timeout exceeded"
    raise SafetyCheckTimeoutError(msg)


# Pre-compiled patterns for speed
_SECRET_PATTERNS = [
    re.compile(
        r'(?i)(api[_-]?key|secret|password|token|credential)\s*[=:]\s*["\']?[a-zA-Z0-9+/=_-]{8,}',
    ),
    re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"),
    re.compile(r"(?i)(aws|gcp|azure)[_-]?(access|secret|api)[_-]?key"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),  # GitHub token
    re.compile(r"sk-[a-zA-Z0-9]{48}"),  # OpenAI key
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
]

_BIDI_OVERRIDES = frozenset(
    [
        "\u202a",
        "\u202b",
        "\u202c",
        "\u202d",
        "\u202e",  # LRE, RLE, PDF, LRO, RLO
        "\u2066",
        "\u2067",
        "\u2068",
        "\u2069",  # LRI, RLI, FSI, PDI
    ],
)

_PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions?"),
    re.compile(r"(?i)disregard\s+(the\s+)?above"),
    re.compile(r"(?i)new\s+instructions?\s*:"),
    re.compile(r"(?i)system\s*:\s*you\s+are"),
]


@dataclass
class SafetyCheckResult:
    """Result of safety check."""

    is_safe: bool
    reason: str = ""
    should_sanitize: bool = False
    sanitized_content: str | None = None


def quick_size_check(content: str | bytes, config: dict[str, Any]) -> SafetyCheckResult | None:
    """Fast size check - returns result if fails, None if passes."""
    safety = config.get("safety", {})
    max_size = safety.get("max_content_size_kb", 500) * 1024

    size = (
        len(content)
        if isinstance(content, bytes)
        else len(content.encode("utf-8", errors="ignore"))
    )

    if size > max_size:
        return SafetyCheckResult(False, f"Content exceeds {max_size // 1024}KB limit")

    return None


def check_secrets(content: str) -> SafetyCheckResult | None:
    """Check for secrets in content. Returns result if found, None if clean."""
    # Only check first 10KB for speed, capped for regex safety
    sample = content[: min(10240, _MAX_REGEX_INPUT_LEN)]

    for pattern in _SECRET_PATTERNS:
        if pattern.search(sample):
            return SafetyCheckResult(False, "Potential secret/credential detected")

    return None


def check_data_bombs(content: str, config: dict[str, Any]) -> SafetyCheckResult | None:
    """Check for various data bomb patterns."""
    safety = config.get("safety", {})

    # 1. Line length bomb
    max_line = safety.get("max_line_length", 10000)
    for i, line in enumerate(content.split("\n")[:1000]):  # Check first 1000 lines
        if len(line) > max_line:
            return SafetyCheckResult(False, f"Line {i + 1} exceeds {max_line} char limit")

    # 2. Repetition bomb - check entropy
    if safety.get("detect_repetition_bombs", True):
        threshold = safety.get("repetition_threshold", 0.95)
        if len(content) > 1000:
            # Sample-based check for speed
            sample = content[:5000]
            unique_chars = len(set(sample))
            if unique_chars < 20:  # Very low entropy
                char_counts = {}
                for c in sample:
                    char_counts[c] = char_counts.get(c, 0) + 1
                max_freq = max(char_counts.values()) / len(sample)
                if max_freq > threshold:
                    return SafetyCheckResult(
                        False,
                        "Repetition bomb detected - low entropy content",
                    )

    # 3. Unicode bomb - excessive combining characters
    if safety.get("detect_unicode_bombs", True):
        max_combining = safety.get("max_combining_chars", 10)
        combining_count = 0
        base_count = 0
        for char in content[:5000]:  # Sample
            # Combining characters are in range 0x0300-0x036F and others
            if "\u0300" <= char <= "\u036f" or "\u1ab0" <= char <= "\u1aff":
                combining_count += 1
            else:
                if combining_count > max_combining:
                    return SafetyCheckResult(False, "Unicode combining character bomb detected")
                combining_count = 0
                base_count += 1

    # 4. BiDi override attack
    if safety.get("block_bidi_override", True):
        for char in content[:5000]:
            if char in _BIDI_OVERRIDES:
                return SafetyCheckResult(False, "Bidirectional text override detected")

    # 5. Null byte injection (in text content)
    if "\x00" in content:
        return SafetyCheckResult(False, "Null byte injection detected")

    # 6. Excessive control characters
    control_count = sum(1 for c in content[:5000] if ord(c) < 32 and c not in "\n\r\t")
    if control_count > len(content[:5000]) * 0.1:
        return SafetyCheckResult(False, "Excessive control characters detected")

    return None


def check_prompt_injection(content: str) -> SafetyCheckResult | None:
    """Check for prompt injection attempts - sanitize rather than block."""
    # Cap sample size for regex safety
    sample = content[: min(10240, _MAX_REGEX_INPUT_LEN)]

    for pattern in _PROMPT_INJECTION_PATTERNS:
        match = pattern.search(sample)
        if match:
            # Sanitize by removing the injection attempt (cap content for safety)
            sanitize_content = content[: _MAX_REGEX_INPUT_LEN * 10]  # Allow larger for sanitization
            sanitized = pattern.sub("[REMOVED]", sanitize_content)
            if len(content) > len(sanitize_content):
                sanitized += content[len(sanitize_content) :]  # Append remainder unchanged
            return SafetyCheckResult(
                is_safe=True,  # Safe after sanitization
                reason="Prompt injection pattern sanitized",
                should_sanitize=True,
                sanitized_content=sanitized,
            )

    return None


def is_safe_content(content: str | bytes, config: dict[str, Any]) -> SafetyCheckResult:
    """Main safety check function.

    Runs checks in order of speed (fast checks first).
    Returns immediately on first failure.
    Enforces timeout from config (Unix only).
    """
    # Get timeout from config (default 5 seconds)
    safety = config.get("safety", {})
    timeout_ms = safety.get("parsing_timeout_ms", 5000)
    timeout_sec = max(1, timeout_ms // 1000)

    # Set up timeout handler (Unix only)
    old_handler = None
    if _SUPPORTS_TIMEOUT:
        old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_sec)

    try:
        return _is_safe_content_impl(content, config)
    except SafetyCheckTimeoutError:
        return SafetyCheckResult(False, f"Safety check timeout ({timeout_sec}s)")
    finally:
        # Always clean up alarm and restore handler
        if _SUPPORTS_TIMEOUT:
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)


def _is_safe_content_impl(content: str | bytes, config: dict[str, Any]) -> SafetyCheckResult:
    """Internal implementation of safety checks."""
    # Convert bytes to string if needed
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8")
        except UnicodeDecodeError:
            return SafetyCheckResult(False, "Binary or non-UTF8 content")

    # 1. Size check (instant)
    result = quick_size_check(content, config)
    if result:
        return result

    # 2. Secrets check (fast - only samples)
    result = check_secrets(content)
    if result:
        return result

    # 3. Data bomb checks (medium - samples with early exit)
    result = check_data_bombs(content, config)
    if result:
        return result

    # 4. Prompt injection (sanitize, don't block)
    result = check_prompt_injection(content)
    if result and result.should_sanitize:
        return result  # Returns with sanitized content

    return SafetyCheckResult(True)
