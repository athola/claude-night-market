"""A list-shaped capture index raised on every WebFetch (ARCH-1).

`yaml.safe_load` returned a list, and `.setdefault` on it raised outside the
YAMLError set-aside path, so the file was never moved.
"""

from __future__ import annotations

from pathlib import Path

import shared.deduplication as dedup


def test_list_shaped_index_reads_as_empty_and_warns(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    index = tmp_path / "memory-palace-index.yaml"
    index.write_text("- a\n- b\n")
    monkeypatch.setattr(dedup, "_get_index_path", lambda: index)
    monkeypatch.setattr(dedup, "_index_cache", None)
    monkeypatch.setattr(dedup, "_index_mtime", 0)

    assert dedup.is_known(url="https://example.com/a") is False
    assert "memory-palace-index.yaml" in capsys.readouterr().err
