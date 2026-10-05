"""Skill and command frontmatter parses, and any hooks in it are readable.

A command whose frontmatter is not valid YAML loads with every field
ignored: `bloat-scan.md` lost its name, description and usage to an
unquoted colon in its description. Seven skills and commands also
declared `hooks:` as flat `{matcher, command}` entries, a shape Claude
Code never reads (handlers sit under a `hooks` list with a `type`), so
their audit logging never ran. Both load silently, hence this sweep.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from abstract.frontmatter import FrontmatterProcessor

REPO_ROOT = Path(__file__).resolve().parents[3]


def _files() -> list[Path]:
    found = set(REPO_ROOT.glob("plugins/*/skills/*/SKILL.md"))
    found |= set(REPO_ROOT.glob("plugins/*/commands/*.md"))
    found |= set(REPO_ROOT.glob(".claude/skills/*/SKILL.md"))
    return sorted(found)


def _frontmatter(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    return text[4:end] if end != -1 else None


def test_frontmatter_is_valid_yaml() -> None:
    broken = []
    for path in _files():
        block = _frontmatter(path)
        if block is None:
            continue
        try:
            yaml.safe_load(block)
        except yaml.YAMLError as exc:
            broken.append(f"{path.relative_to(REPO_ROOT)}: {exc.__class__.__name__}")
    assert broken == [], "\n".join(broken)


def test_frontmatter_hooks_use_the_shape_claude_code_reads() -> None:
    invalid = []
    for path in _files():
        block = _frontmatter(path)
        if block is None:
            continue
        try:
            parsed = yaml.safe_load(block) or {}
        except yaml.YAMLError:
            continue  # reported by the test above
        if isinstance(parsed, dict) and "hooks" in parsed:
            errors = FrontmatterProcessor.validate_210_fields(
                {"hooks": parsed["hooks"]}
            )
            invalid += [f"{path.relative_to(REPO_ROOT)}: {e}" for e in errors]
    assert invalid == [], "\n".join(invalid)
