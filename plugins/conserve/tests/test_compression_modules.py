"""Structural tests for the reversible-compression and cache-alignment docs.

These guard the wiring added when porting Headroom's CCR and prefix-alignment
ideas: the module files exist with valid frontmatter, the owning SKILL.md
files reference them, and both modified skills carry an Exit Criteria section
(repo rule: every modified SKILL.md needs one).
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parent.parent / "skills"

REVERSIBLE = SKILLS / "compression-strategy" / "modules" / "reversible-compression.md"
CACHE_ALIGNED = (
    SKILLS / "context-optimization" / "modules" / "cache-aligned-prefixes.md"
)
COMPRESSION_SKILL = SKILLS / "compression-strategy" / "SKILL.md"
CONTEXT_SKILL = SKILLS / "context-optimization" / "SKILL.md"


@pytest.mark.parametrize("module_path", [REVERSIBLE, CACHE_ALIGNED])
def test_module_exists_with_frontmatter(module_path):
    assert module_path.is_file(), f"missing module: {module_path}"
    text = module_path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), "module needs YAML frontmatter"
    head = text.split("---", 2)[1]
    for field in ("name:", "description:", "category:"):
        assert field in head, f"{module_path.name} frontmatter missing {field}"


def test_reversible_module_documents_handle_and_retrieval():
    text = REVERSIBLE.read_text(encoding="utf-8")
    assert "context_retrieve.py" in text
    assert "context-archive" in text
    # Honest constraint must be stated, not just the upside.
    assert "cannot redact" in text


def test_cache_module_states_write_cost_caveat():
    text = CACHE_ALIGNED.read_text(encoding="utf-8")
    assert "1.25x" in text  # cache writes cost more than normal tokens
    assert "volatile" in text.lower()


@pytest.mark.parametrize(
    ("skill_path", "module_name"),
    [
        (COMPRESSION_SKILL, "reversible-compression"),
        (CONTEXT_SKILL, "cache-aligned-prefixes"),
    ],
)
def test_skill_references_module_and_has_exit_criteria(skill_path, module_name):
    text = skill_path.read_text(encoding="utf-8")
    assert module_name in text, f"{skill_path.name} should reference {module_name}"
    assert "## Exit Criteria" in text, f"{skill_path.name} needs Exit Criteria"
