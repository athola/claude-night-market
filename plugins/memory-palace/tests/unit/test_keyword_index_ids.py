"""A nested corpus file must not collide with a dash-named sibling.

``relative_str.removesuffix(".md").replace("/", "-")`` mapped the path
separator onto a character this corpus already uses in file names, so
``foo/bar.md`` and ``foo-bar.md`` produced the same entry id and the
second silently replaced the first.

Latent rather than theoretical: the corpus is flat today, ``rglob`` at
the top of the build walks recursively, and the names here are
dash-heavy, so the first nested file makes it reachable.
"""

from __future__ import annotations

from pathlib import Path

from memory_palace.corpus.keyword_index import KeywordIndexer


def _write(path: Path, title: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntitle: {title}\n---\n\nContent about {title}.\n", encoding="utf-8"
    )


def test_a_nested_file_and_a_dash_named_file_get_distinct_ids(
    tmp_path: Path,
) -> None:
    """Both files must survive the build with ids of their own."""
    corpus = tmp_path / "corpus"
    _write(corpus / "foo" / "bar.md", "Nested")
    _write(corpus / "foo-bar.md", "Flat")

    indexer = KeywordIndexer(str(corpus), str(tmp_path / "index"))
    indexer.build_index(save=False)

    entry_ids = sorted(indexer.index["entries"].keys())
    assert len(entry_ids) == 2, f"one entry overwrote the other; ids were {entry_ids}"
    assert len(set(entry_ids)) == 2
