"""_ReviewContext.get_file_content reads each file once per review pass.

The rust/api/math review skills compose roughly twenty ``analyze_*``
mixins, and each mixin calls ``context.get_file_content(path)``
independently. Without memoization the same file is read from disk once
per mixin. This test pins the read-once-per-filename contract that
every mixin relies on the host having read the file a single time.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from pensive.workflows.code_review import _ReviewContext


@pytest.mark.unit
class TestReviewContextFileContentCache:
    """get_file_content memoizes by filename for the life of the context."""

    def test_repeated_reads_hit_disk_once(self, tmp_path: Path) -> None:
        (tmp_path / "lib.rs").write_text("fn main() {}\n")
        ctx = _ReviewContext(tmp_path, ["lib.rs"])
        original_read_text = Path.read_text
        calls = {"n": 0}

        # Plain function (not a Mock) so descriptor binding passes the Path
        # instance as self. *args/**kwargs typed Any to forward cleanly into
        # read_text's specific signature without a type-ignore suppression.
        def counting_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
            calls["n"] += 1
            return original_read_text(self, *args, **kwargs)

        with patch.object(Path, "read_text", counting_read_text):
            first = ctx.get_file_content("lib.rs")
            second = ctx.get_file_content("lib.rs")

        assert first == second == "fn main() {}\n"
        assert calls["n"] == 1, (
            f"expected one disk read for repeated calls, got {calls['n']}"
        )

    def test_distinct_files_each_read_once(self, tmp_path: Path) -> None:
        (tmp_path / "a.rs").write_text("a")
        (tmp_path / "b.rs").write_text("b")
        ctx = _ReviewContext(tmp_path, ["a.rs", "b.rs"])

        assert ctx.get_file_content("a.rs") == "a"
        assert ctx.get_file_content("b.rs") == "b"

    def test_missing_file_returns_empty_and_is_cached(self, tmp_path: Path) -> None:
        ctx = _ReviewContext(tmp_path, [])
        assert ctx.get_file_content("nope.rs") == ""
        assert ctx.get_file_content("nope.rs") == ""
