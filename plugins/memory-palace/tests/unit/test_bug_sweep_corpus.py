"""Regression tests for the bug-review sweep over the corpus modules."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from memory_palace.corpus.marginal_value import (
    MarginalValueFilter,
    RedundancyLevel,
)


class TestRedundancyKeepsBestScore:
    """An entry found by both keywords and queries counts at its higher score."""

    @pytest.mark.unit
    def test_entry_matched_twice_uses_the_higher_match_score(
        self, tmp_path: Path
    ) -> None:
        """Keyword score 0.35 and query score 0.9 for e1 give overlap 0.9."""
        corpus_dir = tmp_path / "corpus"
        index_dir = tmp_path / "index"
        corpus_dir.mkdir()
        index_dir.mkdir()
        with (
            patch("memory_palace.corpus.marginal_value.CacheLookup") as lookup_cls,
            patch("memory_palace.corpus.marginal_value.KeywordIndexer"),
            patch("memory_palace.corpus.marginal_value.QueryTemplateManager"),
        ):
            mvf = MarginalValueFilter(
                corpus_dir=str(corpus_dir), index_dir=str(index_dir)
            )
        lookup = MagicMock()
        lookup_cls.return_value = lookup
        mvf.cache_lookup = lookup
        lookup.get_entry_content.return_value = "different text"

        def search(query: object, mode: str, min_score: float) -> list[dict]:
            score = 0.35 if mode == "keywords" else 0.9
            return [{"entry_id": "e1", "match_score": score}]

        lookup.search.side_effect = search

        check = mvf._check_redundancy({"cache"}, ["how to cache"], "new text")

        assert check.overlap_score == pytest.approx(0.9)
        assert check.level == RedundancyLevel.HIGHLY_REDUNDANT
