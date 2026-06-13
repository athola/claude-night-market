"""Shared line cache for rust-review analysis mixins.

Every analysis mixin walks the file content line by line. Splitting the
content on each dimension would re-scan the whole file repeatedly, so the
split result is cached against the content it came from: the host reads
the same string once per file and passes it to every dimension, so an
identity check is enough to know the cache is still valid.

Defining ``_get_lines`` here also gives each analysis mixin a typed base.
Without it, a mixin's ``self._get_lines(...)`` call refers to a method
that exists only on the composed :class:`RustReviewSkill`, which mypy
cannot see when it checks the mixin in isolation. Inheriting this base
makes the method real on every mixin's own type.
"""

from __future__ import annotations

__all__ = ["LineCacheMixin"]


class LineCacheMixin:
    """Splits file content into lines once and reuses the result."""

    _cached_content: str | None = None
    _cached_lines: list[str] = []

    def _get_lines(self, content: str) -> list[str]:
        """Return ``content.splitlines()``, cached by content identity."""
        if self._cached_content is not content:
            self._cached_content = content
            self._cached_lines = content.splitlines()
        return self._cached_lines
