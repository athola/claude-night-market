"""The superpowers integration docs agree with each other and with upstream.

Six install snippets ran ``/plugin marketplace add obra/superpowers`` and
then installed ``superpowers@superpowers-marketplace``. That repository's
marketplace registers as ``superpowers-dev`` (its
``.claude-plugin/marketplace.json``), so the pair never resolved.
Upstream's one-step install is ``superpowers@claude-plugins-official``.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BOOK_PAGE = REPO_ROOT / "book/src/reference/superpowers-integration.md"
SANCTUM_GUIDE = REPO_ROOT / "plugins/sanctum/docs/superpowers-integration-guide.md"
DOC_GLOBS = ("book/src/**/*.md", "plugins/*/commands/*.md", "plugins/*/docs/*.md")


def _docs() -> list[Path]:
    return sorted({p for g in DOC_GLOBS for p in REPO_ROOT.glob(g)})


def test_no_doc_adds_the_superpowers_repo_as_a_marketplace() -> None:
    offenders = [
        str(p.relative_to(REPO_ROOT))
        for p in _docs()
        if re.search(r"marketplace add obra/superpowers\s*$", p.read_text(), re.M)
    ]
    assert not offenders, (
        "these pair `marketplace add obra/superpowers` with an install from a "
        "different marketplace; use `/plugin install "
        f"superpowers@claude-plugins-official`: {offenders}"
    )


def test_sync_docs_record_the_same_upstream_version() -> None:
    book = re.search(r"Last synced\*\*: superpowers (v[\d.]+)", BOOK_PAGE.read_text())
    guide = re.search(
        r"Synced with\*\*: superpowers (v[\d.]+)", SANCTUM_GUIDE.read_text()
    )
    assert book, "book page lost its Last synced line"
    assert guide, "sanctum guide lost its Synced with line"
    assert book.group(1) == guide.group(1)
