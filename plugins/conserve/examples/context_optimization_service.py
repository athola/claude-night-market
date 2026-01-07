"""Example: Conservation plugin providing context optimization service.

This example demonstrates how the Conservation plugin can:
1. Provide context optimization as a service to other plugins
2. Be detected and used by any plugin that needs context optimization
3. Offer various optimization strategies (token reduction, prioritization,
   summarization)
4. Work as a drop-in enhancement for any plugin
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# Constants
HIGH_PRIORITY_THRESHOLD = 0.7
TOKEN_BUFFER_MULTIPLIER = 0.9
HIGH_SCORE_THRESHOLD = 0.8
LOW_TOKEN_MULTIPLIER = 0.8

# Note: These imports are for example usage only
# from conservation.context_optimization_service import (
#     ConservationContextOptimizer,
#     ContentBlock,
# )
# from conservation.context_optimization_service import ConservationServiceRegistry


@dataclass
class ContentBlock:
    """Represents a block of content with metadata."""

    content: str
    priority: float  # 0.0 to 1.0
    source: str  # Where this content came from
    token_estimate: int
    metadata: dict[str, Any]
    score: float = 0.0  # Calculated score for optimization


class ConservationContextOptimizer:
    """Main context optimization service provided by Conservation plugin."""

    def __init__(self) -> None:
        """Initialize the context optimizer with default strategies."""
        self.strategies = {
            "priority": self._optimize_by_priority,
            "recency": self._optimize_by_recency,
            "importance": self._optimize_by_importance,
            "semantic": self._optimize_by_semantic_importance,
            "balanced": self._optimize_balanced,
        }
        self.optimizers = {}
        self._register_builtin_optimizers()

    def _register_builtin_optimizers(self) -> None:
        """Register built-in optimization strategies."""
        self.optimizers.update(
            {
                "conservation.priority": self._optimize_by_priority,
                "conservation.recency": self._optimize_by_recency,
                "conservation.importance": self._optimize_by_importance,
                "conservation.semantic": self._optimize_by_semantic_importance,
                "conservation.balanced": self._optimize_balanced,
            },
        )

    def optimize_content(
        self,
        content_blocks: list[ContentBlock],
        max_tokens: int,
        strategy: str = "balanced",
        preserve_structure: bool = True,
    ) -> dict[str, Any]:
        """Optimize content blocks to fit within max_tokens.

        Args:
            content_blocks: List of content blocks with metadata
            max_tokens: Maximum tokens to keep
            strategy: Optimization strategy to use
            preserve_structure: Whether to preserve document structure

        Returns:
            Dictionary with optimized content and metadata

        """
        result = {
            "optimized_content": "",
            "original_tokens": sum(b.token_estimate for b in content_blocks),
            "optimized_tokens": 0,
            "compression_ratio": 0.0,
            "blocks_kept": 0,
            "blocks_dropped": 0,
            "strategy_used": strategy,
            "preserved_structure": preserve_structure,
        }

        # Select optimization strategy
        optimizer = self.strategies.get(strategy, self._optimize_balanced)

        # Apply optimization
        optimized_blocks = optimizer(content_blocks, max_tokens)

        # Build final content
        if preserve_structure:
            result["optimized_content"] = self._rebuild_structure(optimized_blocks)
        else:
            result["optimized_content"] = "\n\n".join(
                b.content for b in optimized_blocks
            )

        # Calculate metrics
        result["optimized_tokens"] = sum(b.token_estimate for b in optimized_blocks)
        result["compression_ratio"] = (
            result["optimized_tokens"] / result["original_tokens"]
        )
        result["blocks_kept"] = len(optimized_blocks)
        result["blocks_dropped"] = len(content_blocks) - len(optimized_blocks)

        return result

    def _optimize_by_priority(
        self,
        blocks: list[ContentBlock],
        max_tokens: int,
    ) -> list[ContentBlock]:
        """Keep blocks with highest priority scores."""
        # Sort by priority (descending)
        sorted_blocks = sorted(blocks, key=lambda b: b.priority, reverse=True)

        # Keep blocks until we hit the token limit
        kept_blocks = []
        current_tokens = 0

        for block in sorted_blocks:
            if current_tokens + block.token_estimate <= max_tokens:
                kept_blocks.append(block)
                current_tokens += block.token_estimate
            else:
                # Try to truncate the last block if it's important
                if (
                    block.priority > HIGH_PRIORITY_THRESHOLD
                    and current_tokens < max_tokens * TOKEN_BUFFER_MULTIPLIER
                ):
                    remaining_tokens = max_tokens - current_tokens
                    truncated = self._truncate_block(block, remaining_tokens)
                    if truncated:
                        kept_blocks.append(truncated)
                        current_tokens += truncated.token_estimate
                break

        # Restore original order for consistency
        kept_blocks.sort(key=lambda b: blocks.index(b) if b in blocks else float("inf"))
        return kept_blocks

    def _optimize_by_recency(
        self,
        blocks: list[ContentBlock],
        max_tokens: int,
    ) -> list[ContentBlock]:
        """Keep most recent blocks based on metadata."""

        # Sort by timestamp if available
        def get_timestamp(block):
            return block.metadata.get("timestamp", 0)

        sorted_blocks = sorted(blocks, key=get_timestamp, reverse=True)

        kept_blocks = []
        current_tokens = 0

        for block in sorted_blocks:
            if current_tokens + block.token_estimate <= max_tokens:
                kept_blocks.append(block)
                current_tokens += block.token_estimate

        # Return in original order
        return sorted(kept_blocks, key=lambda b: blocks.index(b))

    def _optimize_by_importance(
        self,
        blocks: list[ContentBlock],
        max_tokens: int,
    ) -> list[ContentBlock]:
        """Keep blocks based on importance keywords and patterns."""
        # Importance indicators
        important_patterns = [
            r"\b(error|exception|fail|critical)\b",
            r"\b(TODO|FIXME|XXX)\b",
            r"\b(IMPORTANT|NOTE|WARNING)\b",
            r"```(?:python|javascript|bash|shell)",  # Code blocks
            r"^\s*def\s+\w+",  # Function definitions
            r"^\s*class\s+\w+",  # Class definitions
        ]

        # Score blocks based on importance patterns
        scored_blocks = []
        for block in blocks:
            score = block.priority  # Start with base priority

            # Add points for importance patterns
            for pattern in important_patterns:
                matches = len(
                    re.findall(pattern, block.content, re.IGNORECASE | re.MULTILINE),
                )
                score += matches * 0.1

            # Boost for code blocks
            if "```" in block.content:
                score += 0.3

            block.score = score
            scored_blocks.append(block)

        # Sort by score (descending)
        scored_blocks.sort(key=lambda b: b.score, reverse=True)

        # Keep top blocks within token limit
        kept_blocks = []
        current_tokens = 0

        for block in scored_blocks:
            if current_tokens + block.token_estimate <= max_tokens:
                kept_blocks.append(block)
                current_tokens += block.token_estimate

        return sorted(kept_blocks, key=lambda b: blocks.index(b))

    def _optimize_by_semantic_importance(
        self,
        blocks: list[ContentBlock],
        max_tokens: int,
    ) -> list[ContentBlock]:
        """Semantic optimization based on content analysis."""
        # Simple semantic scoring based on content characteristics
        semantic_keywords = {
            "high": ["main", "init", "core", "key", "primary", "essential", "critical"],
            "medium": ["helper", "util", "support", "secondary", "additional"],
            "low": ["test", "example", "demo", "temp", "debug"],
        }

        scored_blocks = []
        for block in blocks:
            content_lower = block.content.lower()

            # Calculate semantic score
            score = block.priority
            for keyword in semantic_keywords["high"]:
                if keyword in content_lower:
                    score += 0.3
            for keyword in semantic_keywords["medium"]:
                if keyword in content_lower:
                    score += 0.1
            for keyword in semantic_keywords["low"]:
                if keyword in content_lower:
                    score -= 0.1

            # Check for headers and structure
            if re.match(r"^#+\s", content_lower):  # Markdown headers
                score += 0.2

            block.score = max(0, score)  # validate non-negative
            scored_blocks.append(block)

        # Select top scoring blocks
        scored_blocks.sort(key=lambda b: b.score, reverse=True)

        kept_blocks = []
        current_tokens = 0

        for block in scored_blocks:
            if current_tokens + block.token_estimate <= max_tokens:
                kept_blocks.append(block)
                current_tokens += block.token_estimate

        return sorted(kept_blocks, key=lambda b: blocks.index(b))

    def _optimize_balanced(
        self,
        blocks: list[ContentBlock],
        max_tokens: int,
    ) -> list[ContentBlock]:
        """Balanced optimization considering multiple factors."""
        # Combine multiple scoring methods
        for block in blocks:
            # Start with base priority
            score = block.priority

            # Add recency factor
            timestamp = block.metadata.get("timestamp", 0)
            recency_score = min(timestamp / 1000000, 1.0)  # Normalize to 0-1
            score += recency_score * 0.2

            # Add importance factor
            importance_patterns = ["error", "exception", "critical", "main", "key"]
            for pattern in importance_patterns:
                if pattern in block.content.lower():
                    score += 0.1

            # Add structure factor
            if re.match(r"^(#+|def|class|function)", block.content):
                score += 0.2

            block.score = score

        # Use weighted selection
        scored_blocks = sorted(blocks, key=lambda b: b.score, reverse=True)

        kept_blocks = []
        current_tokens = 0

        for block in scored_blocks:
            if current_tokens + block.token_estimate <= max_tokens:
                kept_blocks.append(block)
                current_tokens += block.token_estimate
            elif (
                block.score > HIGH_SCORE_THRESHOLD
                and current_tokens < max_tokens * LOW_TOKEN_MULTIPLIER
            ):
                # Try to fit very important blocks by truncating
                remaining = max_tokens - current_tokens
                truncated = self._truncate_block(block, remaining)
                if truncated:
                    kept_blocks.append(truncated)
                    current_tokens += truncated.token_estimate

        return sorted(kept_blocks, key=lambda b: blocks.index(b))

    def _truncate_block(
        self,
        block: ContentBlock,
        max_tokens: int,
    ) -> ContentBlock | None:
        """Truncate a block to fit within token limit."""
        if block.token_estimate <= max_tokens:
            return block

        # Rough truncation - split by lines and keep what fits
        lines = block.content.split("\n")
        kept_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = len(line.split()) * 1.3  # Rough estimate
            if current_tokens + line_tokens <= max_tokens * 0.9:
                kept_lines.append(line)
                current_tokens += line_tokens
            else:
                kept_lines.append("... [truncated]")
                break

        if kept_lines:
            return ContentBlock(
                content="\n".join(kept_lines),
                priority=block.priority,
                source=block.source,
                token_estimate=int(current_tokens),
                metadata={**block.metadata, "truncated": True},
            )
        return None

    def _rebuild_structure(self, blocks: list[ContentBlock]) -> str:
        """Rebuild content preserving original structure."""
        # Simple concatenation - in real implementation would be more sophisticated
        sections = {}

        for block in blocks:
            section = block.metadata.get("section", "default")
            if section not in sections:
                sections[section] = []
            sections[section].append(block)

        # Build content with section headers
        content_parts = []
        for section, section_blocks in sections.items():
            if section != "default":
                content_parts.append(f"\n## {section.title()}\n")
            for block in section_blocks:
                content_parts.append(block.content)

        return "\n\n".join(content_parts)


# Service registration for other plugins to discover
class ConservationServiceRegistry:
    """Registry that other plugins can query for Conservation services."""

    _instance = None

    def __new__(cls):
        """Create a singleton instance of the registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize private attribute
            object.__setattr__(cls._instance, "_services", {})
        return cls._instance

    @property
    def services(self) -> dict[str, Callable]:
        """Get the services dictionary."""
        if not hasattr(self, "_services"):
            self._services = {}
        return self._services

    def register_service(self, name: str, service: Callable) -> None:
        """Register a service that other plugins can use."""
        self.services[name] = service

    def get_service(self, name: str) -> Callable | None:
        """Get a registered service."""
        return self.services.get(name)

    def list_services(self) -> list[str]:
        """List all available services."""
        return list(self.services.keys())


# Register the optimizer as a service
registry = ConservationServiceRegistry()
optimizer_instance = ConservationContextOptimizer()
registry.register_service(
    "context_optimizer", lambda *args, **kwargs: optimizer_instance
)
registry.register_service(
    "optimize_content",
    lambda *args, **kwargs: ConservationContextOptimizer().optimize_content(
        *args,
        **kwargs,
    ),
)


# Example usage patterns for other plugins
def example_abstract_usage():
    """Demonstrate how Abstract plugin would use Conservation."""
    # Abstract plugin code would do:
    # from conservation.context_optimization_service import (
    #     ConservationContextOptimizer,
    #     ContentBlock,
    # )

    # Create content blocks from skill analysis
    blocks = [
        ContentBlock(
            content="def analyze_skill(skill_path):",
            priority=0.9,
            source="function_definition",
            token_estimate=50,
            metadata={"section": "core", "timestamp": 1640995200},
        ),
        ContentBlock(
            content="# This is a comment explaining the logic",
            priority=0.3,
            source="comment",
            token_estimate=20,
            metadata={"section": "documentation", "timestamp": 1640995200},
        ),
        # ... more blocks
    ]

    # Use Conservation to optimize
    optimizer = ConservationContextOptimizer()
    result = optimizer.optimize_content(
        blocks,
        max_tokens=2000,
        strategy="importance",
        preserve_structure=True,
    )

    return result["optimized_content"]


def example_sanctum_usage():
    """Demonstrate how Sanctum plugin would use Conservation."""
    # Sanctum plugin code would do:
    # from conservation.context_optimization_service import ConservationServiceRegistry

    # Get the optimization service
    registry = ConservationServiceRegistry()
    optimize = registry.get_service("optimize_content")

    if optimize:
        # Use it to optimize git commit messages and diffs
        # git_content_blocks would be defined elsewhere
        return optimize(
            content_blocks=[],
            max_tokens=1500,
            strategy="recency",
        )
    return None


if __name__ == "__main__":
    # Demonstration
    optimizer = ConservationContextOptimizer()

    # Create example content blocks
    example_blocks = [
        ContentBlock(
            content=(
                "# Main Analysis Function\n\n"
                "def analyze(data):\n    return process(data)"
            ),
            priority=0.9,
            source="core_code",
            token_estimate=100,
            metadata={"section": "main", "timestamp": 1640995200},
        ),
        ContentBlock(
            content="# TODO: Add error handling\n# FIXME: This is slow",
            priority=0.7,
            source="comments",
            token_estimate=50,
            metadata={"section": "notes", "timestamp": 1640995300},
        ),
        ContentBlock(
            content="def helper_function():\n    pass",
            priority=0.5,
            source="helper_code",
            token_estimate=60,
            metadata={"section": "helpers", "timestamp": 1640995400},
        ),
        ContentBlock(
            content="# Debug information\nprint('Debug info')",
            priority=0.2,
            source="debug_code",
            token_estimate=40,
            metadata={"section": "debug", "timestamp": 1640995500},
        ),
    ]

    # Test different strategies
    for strategy in ["priority", "importance", "balanced"]:
        result = optimizer.optimize_content(
            example_blocks,
            max_tokens=150,
            strategy=strategy,
        )

    # Show available services
    registry = ConservationServiceRegistry()
    for _service_name in registry.list_services():
        pass
