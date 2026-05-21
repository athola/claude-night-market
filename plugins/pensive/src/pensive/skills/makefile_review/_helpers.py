"""Helpers mixin: content access and target extraction utilities."""

from __future__ import annotations

import re
from typing import Any


class HelpersMixin:
    """Low-level utilities shared by all makefile analysis mixins."""

    def _get_makefile_content(self, context: Any) -> str:
        """Get makefile content from context."""
        content = context.get_file_content()
        return content if isinstance(content, str) else ""

    def _extract_targets(self, content: str) -> list[str]:
        """Extract target names from makefile content."""
        target_pattern = re.compile(r"^([a-zA-Z0-9_\-\.]+)\s*:", re.MULTILINE)
        return target_pattern.findall(content)

    def _extract_phony_targets(self, content: str) -> list[str]:
        """Extract .PHONY declarations from makefile."""
        phony_pattern = re.compile(r"^\.PHONY:\s*(.+)$", re.MULTILINE)
        phony_targets: list[str] = []
        for match in phony_pattern.findall(content):
            phony_targets.extend(match.split())
        return phony_targets

    def _is_file_target(self, target: str) -> bool:
        """Return True if target looks like a file (has extension, not dot-leading)."""
        return "." in target and not target.startswith(".")
