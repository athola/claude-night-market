"""Shared parse_frontmatter shim for validator modules (AR-06).

Routes through ``leyline.frontmatter.parse_frontmatter`` when
available; falls back to an inline minimal parser so the
validators do not hard-fail on systems without leyline. Public
under ``sanctum.validators`` because two scripts already import
``parse_frontmatter`` from there for backward compatibility.
"""

from __future__ import annotations

from typing import Any

import yaml

try:
    from leyline.frontmatter import parse_frontmatter
except ImportError:

    def parse_frontmatter(content: str) -> dict[str, Any] | None:
        """Inline fallback used when leyline is not available."""
        if not content.strip().startswith("---"):
            return None

        lines = content.split("\n")
        end_index = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_index = i
                break

        if end_index is None:
            return None

        frontmatter_text = "\n".join(lines[1:end_index])
        try:
            return yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return None


__all__ = ["parse_frontmatter"]
