"""Tests for the corpus keyword index builder.

The keyword index was emptied in 1.5.0 and its regeneration script was
never written, which left ``cache_lookup`` searching an empty index and
every retrieval-driven subsystem downstream of it inert. These tests pin
the builder that repopulates it.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "build_indexes.py"

EXPECTED_ENTRIES = 2
MIN_KEYWORDS = 3


def _load_script() -> Any:
    spec = importlib.util.spec_from_file_location("build_indexes", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_capture(corpus: Path, name: str, title: str, tags: list[str]) -> Path:
    """Write a staging capture with the frontmatter shape the fetch hook emits."""
    tag_block = "\n".join(f"- {tag}" for tag in tags)
    path = corpus / f"{name}.md"
    path.write_text(
        f"""---
title: '{title}'
source:
  type: web_fetch
  identifier: https://example.com/{name}
date_captured: '2026-06-30'
palace: Tacit Knowledge Capture
district: Research 2026-06-29
maturity: probation
tags:
{tag_block}
---

# {title}

## Intake Content

Discussion of **gradient descent** and retrieval-augmented systems.
""",
        encoding="utf-8",
    )
    return path


def test_build_index_populates_forward_and_reverse_indexes(tmp_path: Path) -> None:
    """A corpus of captures yields entry, keyword, and metadata sections."""
    module = _load_script()
    corpus = tmp_path / "staging"
    corpus.mkdir()
    index_dir = tmp_path / "indexes"
    _write_capture(corpus, "autosop-generator", "AutoSOP generator", ["api-docs"])
    _write_capture(corpus, "rrweb-recorder", "rrweb session recorder", ["replay"])

    result = module.build_indexes(corpus_dir=corpus, index_dir=index_dir)

    written = yaml.safe_load((index_dir / "keyword-index.yaml").read_text())
    assert len(written["entries"]) == EXPECTED_ENTRIES
    assert written["metadata"]["total_entries"] == EXPECTED_ENTRIES
    assert result["total_entries"] == EXPECTED_ENTRIES

    # Reverse index must resolve a tag back to the entry that carries it.
    assert "api-docs" in written["keywords"]
    assert "autosop-generator" in written["keywords"]["api-docs"]


def test_entries_carry_keywords_drawn_from_tags_and_title(tmp_path: Path) -> None:
    """Extraction pulls from frontmatter tags and title, not just body text."""
    module = _load_script()
    corpus = tmp_path / "staging"
    corpus.mkdir()
    _write_capture(corpus, "rrweb-recorder", "rrweb session recorder", ["replay"])

    module.build_indexes(corpus_dir=corpus, index_dir=tmp_path / "indexes")

    written = yaml.safe_load((tmp_path / "indexes" / "keyword-index.yaml").read_text())
    keywords = written["entries"]["rrweb-recorder"]["keywords"]
    assert "replay" in keywords
    assert "session" in keywords
    assert len(keywords) >= MIN_KEYWORDS


def test_dry_run_reports_without_writing(tmp_path: Path) -> None:
    """--dry-run must not create an index file, so operators can inspect first."""
    module = _load_script()
    corpus = tmp_path / "staging"
    corpus.mkdir()
    index_dir = tmp_path / "indexes"
    _write_capture(corpus, "autosop-generator", "AutoSOP generator", ["api-docs"])

    result = module.build_indexes(corpus_dir=corpus, index_dir=index_dir, dry_run=True)

    assert result["total_entries"] == 1
    assert not (index_dir / "keyword-index.yaml").exists()


def test_empty_corpus_is_reported_not_silently_written(tmp_path: Path) -> None:
    """An empty corpus is the 1.5.0 regression itself: refuse to enshrine it.

    Writing ``entries: {}`` over a populated index is how the corpus went
    dark and stayed dark. The builder reports the empty result and leaves
    any existing index alone.
    """
    module = _load_script()
    corpus = tmp_path / "staging"
    corpus.mkdir()
    index_dir = tmp_path / "indexes"
    index_dir.mkdir()
    existing = index_dir / "keyword-index.yaml"
    existing.write_text("entries: {sentinel: {}}\n", encoding="utf-8")

    result = module.build_indexes(corpus_dir=corpus, index_dir=index_dir)

    assert result["total_entries"] == 0
    assert result["wrote"] is False
    assert "sentinel" in existing.read_text()


def test_main_reports_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command line entry point parses arguments and prints a summary.

    Operators read that JSON to decide whether a rebuild did what they
    expected, so the argparse wiring and the printed shape are part of
    the contract, not incidental plumbing.
    """
    module = _load_script()
    corpus = tmp_path / "staging"
    corpus.mkdir()
    _write_capture(corpus, "rrweb-recorder", "rrweb session recorder", ["replay"])

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_indexes.py",
            "--corpus-dir",
            str(corpus),
            "--index-dir",
            str(tmp_path / "indexes"),
            "--dry-run",
        ],
    )
    module.main()

    reported = json.loads(capsys.readouterr().out)
    assert reported["total_entries"] == 1
    assert reported["wrote"] is False


def test_script_bootstraps_src_onto_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Loading the script puts the plugin's src on ``sys.path`` itself.

    The venv resolves memory_palace through an editable-install .pth
    file that a bare system python does not have. That bootstrap is the
    whole reason the recovery script runs outside the venv, so it is
    pinned here rather than left to be tidied away as dead setup.

    The .pth entry has to be stripped first. Asserting against the
    ambient path would pass whether or not the script bootstraps
    anything, which tests the venv rather than the script.
    """
    src_dir = str(SCRIPT_PATH.parent.parent / "src")
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != src_dir])
    assert src_dir not in sys.path

    _load_script()

    assert src_dir in sys.path
