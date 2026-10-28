"""Vendored leyline modules must equal their canonical source.

Plugin isolation forbids a cross-plugin import, so plugins that fall
back when leyline is absent carry a copy. Hand-kept copies drifted
(three of five were pinned by nothing), so the stdlib-only modules are
copied by ``scripts/sync_vendored.py`` and this test runs its check.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "sync_vendored.py"


def _load_sync() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sync_vendored", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_vendored"] = module
    spec.loader.exec_module(module)
    return module


def test_every_vendored_copy_matches_its_canonical_source() -> None:
    sync = _load_sync()
    assert sync.stale_targets(REPO_ROOT) == []


def test_check_reports_a_copy_that_differs_by_one_byte(tmp_path: Path) -> None:
    sync = _load_sync()
    for source, copies in sync.VENDORED.items():
        for rel in (source, *copies):
            (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / rel, tmp_path / rel)
    canonical, targets = next(iter(sync.VENDORED.items()))
    with (tmp_path / canonical).open("a", encoding="utf-8") as handle:
        handle.write("#")
    assert sync.stale_targets(tmp_path) == targets


def test_write_brings_a_stale_copy_back_in_line(tmp_path: Path) -> None:
    sync = _load_sync()
    for source in sync.VENDORED:
        (tmp_path / source).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / source, tmp_path / source)
    sync.write_targets(tmp_path)
    assert sync.stale_targets(tmp_path) == []
    source, targets = next(iter(sync.VENDORED.items()))
    for target in targets:
        assert (
            (tmp_path / target)
            .read_text(encoding="utf-8")
            .endswith((REPO_ROOT / source).read_text(encoding="utf-8"))
        )


@pytest.mark.parametrize(
    ("consumer", "vendored_module"),
    [
        (
            "plugins/sanctum/src/sanctum/validators/_frontmatter.py",
            "sanctum._vendored_leyline_frontmatter",
        ),
        (
            "plugins/gauntlet/src/gauntlet/graph.py",
            "gauntlet._vendored_leyline_sqlite_graph_base",
        ),
        (
            "plugins/memory-palace/src/memory_palace/knowledge_graph.py",
            "memory_palace._vendored_leyline_sqlite_graph_base",
        ),
        (
            "plugins/memory-palace/scripts/validate_knowledge_corpus.py",
            "_vendored_leyline_frontmatter",
        ),
        (
            "plugins/conjure/scripts/quota_tracker.py",
            "_vendored_leyline_fs",
        ),
        (
            "plugins/imbue/scripts/imbue_validator.py",
            "_vendored_abstract_report_formatter",
        ),
        (
            "plugins/tome/src/tome/session.py",
            "tome._vendored_leyline_session_store",
        ),
        (
            "plugins/memory-palace/src/memory_palace/session_history.py",
            "memory_palace._vendored_leyline_session_store",
        ),
        (
            "plugins/abstract/src/abstract/improvement_queue.py",
            "._vendored_leyline_atomic_file",
        ),
        (
            "plugins/abstract/hooks/skill_execution_logger.py",
            "abstract._vendored_leyline_atomic_file",
        ),
        (
            "plugins/conserve/hooks/tool_output_summarizer.py",
            "shared._vendored_leyline_atomic_file",
        ),
        (
            "plugins/egregore/scripts/budget.py",
            "_vendored_leyline_atomic_file",
        ),
        (
            "plugins/egregore/scripts/manifest.py",
            "_vendored_leyline_atomic_file",
        ),
        (
            "plugins/herald/hooks/double_shot_latte.py",
            "_vendored_leyline_atomic_file",
        ),
        (
            "plugins/memory-palace/src/memory_palace/palace_repository.py",
            "memory_palace._vendored_leyline_atomic_file",
        ),
        (
            "plugins/memory-palace/src/memory_palace/corpus/index_promoter.py",
            "memory_palace._vendored_leyline_atomic_file",
        ),
        (
            "plugins/memory-palace/src/memory_palace/lifecycle/autonomy_state.py",
            "memory_palace._vendored_leyline_atomic_file",
        ),
        (
            "plugins/memory-palace/hooks/shared/deduplication.py",
            "memory_palace._vendored_leyline_atomic_file",
        ),
        (
            "plugins/minister/src/minister/project_tracker.py",
            "minister._vendored_leyline_atomic_file",
        ),
        (
            "plugins/spec-kit/src/speckit/caching.py",
            "speckit._vendored_leyline_atomic_file",
        ),
        (
            "plugins/leyline/src/leyline/decision_journal.py",
            "leyline.atomic_file",
        ),
    ],
)
def test_each_fallback_imports_the_vendored_copy(
    consumer: str, vendored_module: str
) -> None:
    """The fallback branch must use the copy, not an inline rewrite."""
    text = (REPO_ROOT / consumer).read_text(encoding="utf-8")
    assert vendored_module in text, consumer
