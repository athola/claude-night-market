"""Advanced pattern matching utilities."""

from __future__ import annotations

import re


class PatternMatcher:
    """Advanced pattern matching for rule evaluation."""

    # Common dangerous command patterns
    DANGEROUS_PATTERNS = {
        "rm_recursive": r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive.*--force|-rf|-fr)",
        "dd_device": r"dd\s+(if|of)=/dev/",
        "chmod_777": r"chmod\s+(777|-R\s+777|--recursive\s+777)",
        "sudo": r"sudo\s+",
        "mkfs": r"mkfs\.",
        "format": r"format\s+[A-Za-z]:",
    }

    # Common security anti-patterns in code
    SECURITY_PATTERNS = {
        "eval_pattern": r"(eval|exec)\s*\(",
        "innerHTML": r"innerHTML\s*=",
        "setInnerHTML": r"dangerouslySetInnerHTML",
        "sql_injection": r"(execute|exec)\s*\(\s*['\"].*?\+",
        "hardcoded_secret": r"(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
    }

    # Debug code patterns
    DEBUG_PATTERNS = {
        "console_log": r"console\.log\s*\(",
        "print_debug": r"(print|println!?)\s*\(",
        "debugger": r"debugger\s*;",
        "var_dump": r"var_dump\s*\(",
        "dd_laravel": r"\bdd\s*\(",
    }

    @classmethod
    def get_pattern(cls, pattern_name: str) -> str | None:
        """Get a predefined pattern by name.

        Args:
            pattern_name: Name of the pattern

        Returns:
            Regex pattern string or None if not found
        """
        all_patterns = {
            **cls.DANGEROUS_PATTERNS,
            **cls.SECURITY_PATTERNS,
            **cls.DEBUG_PATTERNS,
        }
        return all_patterns.get(pattern_name)

    @classmethod
    def list_patterns(cls) -> dict[str, str]:
        """List all available predefined patterns.

        Returns:
            Dictionary of pattern names to regex strings
        """
        return {
            **cls.DANGEROUS_PATTERNS,
            **cls.SECURITY_PATTERNS,
            **cls.DEBUG_PATTERNS,
        }

    @staticmethod
    def test_pattern(pattern: str, text: str) -> bool:
        """Test if a pattern matches text.

        Args:
            pattern: Regex pattern
            text: Text to test against

        Returns:
            True if pattern matches
        """
        try:
            return bool(re.search(pattern, text, re.MULTILINE))
        except re.error:
            return False

    @staticmethod
    def extract_matches(pattern: str, text: str) -> list[str]:
        """Extract all matches of a pattern from text.

        Args:
            pattern: Regex pattern
            text: Text to search

        Returns:
            List of matched strings
        """
        try:
            return re.findall(pattern, text, re.MULTILINE)
        except re.error:
            return []

    @staticmethod
    def validate_pattern(pattern: str) -> tuple[bool, str]:
        """Validate that a pattern is a valid regex.

        Args:
            pattern: Regex pattern to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, str(e)

    @staticmethod
    def escape_pattern(text: str) -> str:
        """Escape special regex characters in text.

        Args:
            text: Text to escape

        Returns:
            Escaped pattern string
        """
        return re.escape(text)

    @classmethod
    def suggest_pattern(cls, text: str) -> list[str]:
        """Suggest predefined patterns that match the given text.

        Args:
            text: Text to analyze

        Returns:
            List of pattern names that match
        """
        matches = []
        for name, pattern in cls.list_patterns().items():
            if cls.test_pattern(pattern, text):
                matches.append(name)
        return matches
