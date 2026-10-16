"""Tests for the manifest helpers shared by the egregore hooks."""

from __future__ import annotations

from _manifest_utils import get_items


def test_get_items_returns_nothing_when_the_item_list_is_not_a_list() -> None:
    """A manifest whose work_items is not a list yields no items.

    GIVEN manifest data whose work_items value is a string
    WHEN the items are read
    THEN the result is an empty list.
    """
    assert get_items({"work_items": "oops"}) == []


def test_get_items_drops_entries_that_are_not_objects() -> None:
    """Only object entries count as work items.

    GIVEN a work_items list mixing an object, a string, and a number
    WHEN the items are read
    THEN only the object remains.
    """
    assert get_items({"work_items": [{"id": "a"}, "b", 3]}) == [{"id": "a"}]
