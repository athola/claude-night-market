"""Unit tests for the rust-review shared line cache.

Feature: Line Splitting Is Cached By Content Identity
  As a rust-review analysis mixin
  I want `_get_lines` to split file content once and reuse the result
  So that running many detection dimensions over one file does not
    re-split the whole file on every dimension.
"""

from __future__ import annotations

import pytest

from pensive.skills.rust_review import RustReviewSkill
from pensive.skills.rust_review.line_cache import LineCacheMixin


@pytest.mark.unit
class TestLineCacheMixin:
    """Detector base: _get_lines caches by content identity."""

    def setup_method(self) -> None:
        self.cache = LineCacheMixin()

    def test_splits_content_into_lines(self) -> None:
        """The lines returned are `content.splitlines()`."""
        content = "a\nb\nc\n"
        assert self.cache._get_lines(content) == ["a", "b", "c"]

    def test_same_content_returns_cached_object(self) -> None:
        """A second call with the same object reuses the cached list."""
        content = "x\ny\n"
        first = self.cache._get_lines(content)
        second = self.cache._get_lines(content)
        assert first is second

    def test_new_content_resplits(self) -> None:
        """Different content invalidates the cache and re-splits."""
        first = self.cache._get_lines("one\ntwo\n")
        second = self.cache._get_lines("three\nfour\n")
        assert first is not second
        assert second == ["three", "four"]

    def test_empty_content_yields_no_lines(self) -> None:
        """Empty content splits to an empty list, not a crash."""
        assert self.cache._get_lines("") == []

    def test_instances_do_not_share_cache(self) -> None:
        """The cache is per-instance, not shared via the class. The default
        is the None sentinel (no shared mutable list), so an untouched
        instance never sees another instance's lines."""
        a = LineCacheMixin()
        b = LineCacheMixin()
        a._get_lines("aaa\n")
        assert b._cached_lines is None


@pytest.mark.unit
class TestRustReviewSkillUsesSharedCache:
    """RustReviewSkill inherits _get_lines from the shared base."""

    def test_skill_has_get_lines(self) -> None:
        skill = RustReviewSkill()
        assert isinstance(skill, LineCacheMixin)
        assert skill._get_lines("p\nq\n") == ["p", "q"]
