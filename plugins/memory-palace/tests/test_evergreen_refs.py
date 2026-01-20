"""Regression guard for evergreen knowledge entries."""

from __future__ import annotations

from pathlib import Path

import yaml

KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "docs" / "knowledge-corpus"
VITALITY_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "indexes" / "vitality-scores.yaml"
)


def _load_front_matter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"Missing front matter in {path.name}"
    _, fm, _ = content.split("---", 2)
    return yaml.safe_load(fm)


def test_evergreen_entries_exist() -> None:
    """Evergreen reference files should remain present with proper maturity."""
    expected = {
        "franklin-protocol-learning",
        "konmari-method-tidying",
    }
    for slug in expected:
        path = KNOWLEDGE_DIR / f"{slug}.md"
        assert path.exists(), f"Evergreen entry missing: {slug}"
        front_matter = _load_front_matter(path)
        assert front_matter.get("maturity") == "evergreen"


def test_maturity_metadata_is_valid_yaml() -> None:
    """Front matter in corpus files must parse to valid YAML."""
    for path in KNOWLEDGE_DIR.glob("*.md"):
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        _, fm, _ = content.split("---", 2)
        data = yaml.safe_load(fm)
        assert data.get("maturity") in {"probation", "budding", "growing", "evergreen"}


def test_vitality_scores_preserve_evergreen_entries() -> None:
    """Vitality scores index must retain evergreen entries."""
    data = yaml.safe_load(VITALITY_PATH.read_text(encoding="utf-8"))
    entries = data.get("entries", {})
    slug = "konmari-method-tidying"
    payload = entries.get(slug)
    assert payload, f"Vitality entry missing for {slug}"
    maturity = payload.get("maturity") or payload.get("state")
    assert maturity == "evergreen"
