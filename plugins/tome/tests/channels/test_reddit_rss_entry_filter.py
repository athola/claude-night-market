"""Reddit RSS entries without a title or link are dropped before parsing.

The tag strip on ``<content>`` runs only for entries that will become a
finding. These tests pin what that ordering must preserve: incomplete
entries yield nothing, and a complete entry keeps its tag-stripped text.
"""

from __future__ import annotations

import pytest

from tome.channels.discourse import parse_reddit_rss

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>No link here</title>
<content type="html">&lt;p&gt;orphan&lt;/p&gt;</content></entry>
<entry><title></title>
<link href="https://www.reddit.com/r/rust/comments/untitled/"/>
<content type="html">&lt;p&gt;untitled&lt;/p&gt;</content></entry>
<entry><title>Borrow checker tips</title>
<link href="https://www.reddit.com/r/rust/comments/abc/tips/"/>
<content type="html">&lt;div&gt;&lt;p&gt;Use &lt;b&gt;scoped&lt;/b&gt;
borrows.&lt;/p&gt;&lt;/div&gt;</content></entry>
</feed>"""


@pytest.mark.unit
def test_entries_without_title_or_link_are_skipped() -> None:
    findings = parse_reddit_rss(FEED, "rust")

    assert [f.url for f in findings] == [
        "https://www.reddit.com/r/rust/comments/abc/tips/"
    ]


@pytest.mark.unit
def test_a_complete_entry_keeps_its_tag_stripped_text() -> None:
    [finding] = parse_reddit_rss(FEED, "rust")

    assert finding.title == "Borrow checker tips"
    assert finding.summary == "Use scoped borrows."
