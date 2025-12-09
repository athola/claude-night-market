#!/usr/bin/env python3
"""Consolidated token estimation for Abstract.

Single source of truth for all token-related calculations.
Uses ~4 characters per token as the base estimation ratio.

This module consolidates token estimation logic previously scattered across:
- src/abstract/utils.py (estimate_tokens, count_tokens_detailed,
  analyze_token_components, TokenAnalyzer class)
- Various scripts that did ad-hoc token calculations

Key principles:
- Standard ratio: 4 characters per token (based on OpenAI's guidance)
- Content-type multipliers: YAML is denser (1.2x), code has more symbols (1.5x)
- Component-based analysis: Separate tokens for frontmatter, body, and code
"""

import re

from .frontmatter import FrontmatterProcessor

# Constants for token estimation
CHARS_PER_TOKEN = 4
FRONTMATTER_MULTIPLIER = 1.2  # YAML tends to be denser
CODE_MULTIPLIER = 1.5  # Code has more symbols/special chars


def estimate_tokens(text: str) -> int:
    """Estimate token count for text using standard ratio.

    Simple token estimation without content-type adjustments.
    Use this for quick estimates or when content type doesn't matter.

    Args:
        text: The text to estimate tokens for.

    Returns:
        Estimated token count.

    Example:
        >>> estimate_tokens("Hello, world!")
        3  # 13 characters / 4 = ~3 tokens

    """
    if not text:
        return 0
    return len(text) // CHARS_PER_TOKEN


def extract_code_blocks(content: str) -> list[str]:
    r"""Extract code blocks from markdown content.

    Args:
        content: Markdown content.

    Returns:
        List of code block contents (without the backtick delimiters).

    Example:
        >>> content = "Some text\n```python\nprint('hello')\n```\nMore text"
        >>> extract_code_blocks(content)
        ["print('hello')"]

    """
    pattern = r"```[^`\n]*\n(.*?)\n```"
    return re.findall(pattern, content, re.DOTALL)


class TokenAnalyzer:
    """Unified token analysis and efficiency checking.

    Consolidates all token-related analysis logic into a single interface.
    Uses a standard ratio of ~4 characters per token for estimation.

    This class provides:
    - Content analysis with component breakdown (frontmatter, body, code)
    - Efficiency checking against configurable thresholds
    - Consistent token counting across all Abstract tools

    Example:
        >>> analyzer = TokenAnalyzer()
        >>> result = analyzer.analyze_content(skill_content)
        >>> print(f"Total tokens: {result['total_tokens']}")
        >>> efficiency = analyzer.check_efficiency(result['total_tokens'])
        >>> print(f"Status: {efficiency['status']}")

    """

    # Standard token estimation ratio (characters per token)
    CHARS_PER_TOKEN = CHARS_PER_TOKEN

    # Multipliers for different content types
    FRONTMATTER_MULTIPLIER = FRONTMATTER_MULTIPLIER
    CODE_MULTIPLIER = CODE_MULTIPLIER

    @staticmethod
    def analyze_content(content: str) -> dict[str, int]:
        """Analyze content and return token breakdown by component type.

        This method provides detailed token analysis including:
        - Total tokens (with content-type adjustments)
        - Character and word counts
        - Separate counts for frontmatter, body, and code blocks

        Args:
            content: The text content to analyze.

        Returns:
            Dictionary containing:
                - total_tokens: Estimated total token count
                - char_count: Character count
                - word_count: Word count
                - frontmatter_tokens: Tokens in frontmatter (if present)
                - body_tokens: Tokens in body content (excluding code)
                - code_tokens: Tokens in code blocks

        Example:
            >>> result = TokenAnalyzer.analyze_content(skill_content)
            >>> print(f"Frontmatter: {result['frontmatter_tokens']} tokens")
            >>> print(f"Body: {result['body_tokens']} tokens")
            >>> print(f"Code: {result['code_tokens']} tokens")
            >>> print(f"Total: {result['total_tokens']} tokens")

        """
        if not content:
            return {
                "total_tokens": 0,
                "char_count": 0,
                "word_count": 0,
                "frontmatter_tokens": 0,
                "body_tokens": 0,
                "code_tokens": 0,
            }

        char_count = len(content)
        word_count = len(content.split())

        # Extract components using FrontmatterProcessor
        frontmatter, body = FrontmatterProcessor.extract_raw(content)
        code_blocks = extract_code_blocks(body)
        code_content = "".join(code_blocks)

        # Calculate tokens for each component with appropriate multipliers
        frontmatter_tokens = TokenAnalyzer._estimate_tokens(
            frontmatter,
            TokenAnalyzer.FRONTMATTER_MULTIPLIER,
        )
        code_tokens = TokenAnalyzer._estimate_tokens(
            code_content,
            TokenAnalyzer.CODE_MULTIPLIER,
        )

        # Body tokens exclude code blocks to avoid double counting
        body_without_code = body
        for block in code_blocks:
            body_without_code = body_without_code.replace(block, "", 1)
        body_tokens = TokenAnalyzer._estimate_tokens(body_without_code, 1.0)

        total_tokens = frontmatter_tokens + body_tokens + code_tokens

        return {
            "total_tokens": total_tokens,
            "char_count": char_count,
            "word_count": word_count,
            "frontmatter_tokens": frontmatter_tokens,
            "body_tokens": body_tokens,
            "code_tokens": code_tokens,
        }

    @staticmethod
    def check_efficiency(
        token_count: int,
        optimal: int = 2000,
        max_acceptable: int = 4000,
    ) -> dict:
        """Check token efficiency against thresholds.

        Evaluates token count and provides status, rating, and actionable feedback.
        The rating system:
        - OPTIMAL: <= optimal threshold (rating 1.0)
        - GOOD: Between optimal and midpoint (rating 0.9-0.7)
        - WARNING: Between midpoint and max (rating 0.7-0.5)
        - EXCESSIVE: Above max threshold (rating < 0.5)

        Args:
            token_count: Number of tokens to evaluate.
            optimal: Optimal token count threshold (default 2000).
            max_acceptable: Maximum acceptable token count (default 4000).

        Returns:
            Dictionary containing:
                - status: One of OPTIMAL, GOOD, WARNING, EXCESSIVE
                - rating: Float between 0.0 and 1.0
                - is_efficient: Boolean indicating if within acceptable range
                - message: Human-readable description
                - optimal_threshold: The optimal threshold used
                - max_threshold: The max acceptable threshold used

        Example:
            >>> efficiency = TokenAnalyzer.check_efficiency(1800)
            >>> if not efficiency['is_efficient']:
            ...     print(efficiency['message'])

        """
        if token_count <= optimal:
            status = "OPTIMAL"
            rating = 1.0
            is_efficient = True
            message = f"Token count ({token_count}) is within optimal range"
        elif token_count <= optimal + (max_acceptable - optimal) * 0.5:
            status = "GOOD"
            # Rating scales from 0.9 to 0.7 in this range
            progress = (token_count - optimal) / ((max_acceptable - optimal) * 0.5)
            rating = 0.9 - (progress * 0.2)
            is_efficient = True
            message = f"Token count ({token_count}) is over optimal but acceptable"
        elif token_count <= max_acceptable:
            status = "WARNING"
            # Rating scales from 0.7 to 0.5 in this range
            progress = (token_count - optimal - (max_acceptable - optimal) * 0.5) / (
                (max_acceptable - optimal) * 0.5
            )
            rating = 0.7 - (progress * 0.2)
            is_efficient = True
            message = f"Token count ({token_count}) approaching max ({max_acceptable})"
        else:
            status = "EXCESSIVE"
            # Rating decreases below 0.5 for excessive tokens
            overage_ratio = token_count / max_acceptable
            rating = max(0.0, 0.5 / overage_ratio)
            is_efficient = False
            message = f"Token count ({token_count}) exceeds max ({max_acceptable})"

        return {
            "status": status,
            "rating": rating,
            "is_efficient": is_efficient,
            "message": message,
            "optimal_threshold": optimal,
            "max_threshold": max_acceptable,
        }

    @staticmethod
    def _estimate_tokens(text: str, multiplier: float = 1.0) -> int:
        """Estimate token count for text with optional multiplier.

        Internal method for token estimation with content-type adjustments.

        Args:
            text: Text to estimate tokens for.
            multiplier: Multiplier for content type adjustment.

        Returns:
            Estimated token count.

        """
        if not text:
            return 0
        return int((len(text) / TokenAnalyzer.CHARS_PER_TOKEN) * multiplier)


# Module-level convenience functions for common use cases


def analyze_content(content: str) -> dict[str, int]:
    """Analyze content and return detailed token breakdown.

    Convenience function that delegates to TokenAnalyzer.analyze_content().

    Args:
        content: The text content to analyze.

    Returns:
        Dictionary with token breakdown by component type.

    """
    return TokenAnalyzer.analyze_content(content)


def check_efficiency(
    token_count: int,
    optimal: int = 2000,
    max_acceptable: int = 4000,
) -> dict:
    """Check token efficiency against thresholds.

    Convenience function that delegates to TokenAnalyzer.check_efficiency().

    Args:
        token_count: Number of tokens to evaluate.
        optimal: Optimal token count threshold.
        max_acceptable: Maximum acceptable token count.

    Returns:
        Dictionary with efficiency metrics.

    """
    return TokenAnalyzer.check_efficiency(token_count, optimal, max_acceptable)
