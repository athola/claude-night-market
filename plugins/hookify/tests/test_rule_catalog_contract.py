"""Every bundled rule must load, and no two may share a name.

``ConfigLoader.load_all_rules`` keys rules by frontmatter ``name`` and
``install_rule.py`` writes ``hookify.<name>.local.md`` without the
category, so a duplicate name across categories would make one rule
silently replace the other. A bundled rule that fails validation is
logged and dropped, which is how ``campsite-check`` shipped with an
``action`` the validator rejects and never fired.
"""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

from hookify.core.config_loader import ConfigLoader

RULES_DIR = Path(__file__).resolve().parent.parent / "skills" / "rule-catalog" / "rules"


def test_bundled_rule_names_are_unique_across_categories() -> None:
    names = Counter(p.stem for p in RULES_DIR.rglob("*.md"))
    duplicates = sorted(name for name, count in names.items() if count > 1)
    assert not duplicates, duplicates


def test_every_bundled_rule_loads_without_a_warning(caplog) -> None:
    loader = ConfigLoader(user_rules_dir=Path("/nonexistent"), include_bundled=True)
    with caplog.at_level(logging.WARNING, logger="hookify.core.config_loader"):
        rules = loader.load_all_rules()
    dropped = [r.message for r in caplog.records if "Error loading" in r.message]
    assert not dropped, dropped
    assert {r.name for r in rules} == {p.stem for p in RULES_DIR.rglob("*.md")}
