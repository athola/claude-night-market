"""Every markdown frontmatter block in plugins/ parses as YAML.

The per-skill validators read SKILL.md only, so a module whose
`description:` held an unquoted ": " failed to parse with nothing noticing.
Three such modules were found in the 2026-10-27 unbloat; any reader that
loads module metadata got an exception or nothing.

The agent template is pinned too: abstract reports `tools_allowed` and
`max_iterations` as names the harness never reads, and the template is
where new agents copy them from.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]


def _frontmatter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    return text[4:end] if end != -1 else None


def _plugin_markdown() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "plugins/**/*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [ROOT / rel for rel in listed]


def test_every_plugin_markdown_frontmatter_is_valid_yaml() -> None:
    unparsable = []
    for path in _plugin_markdown():
        block = _frontmatter(path.read_text(encoding="utf-8"))
        if block is None:
            continue
        try:
            yaml.safe_load(block)
        except yaml.YAMLError:
            unparsable.append(str(path.relative_to(ROOT)))
    assert unparsable == []


def test_agent_template_uses_field_names_the_harness_reads() -> None:
    template = ROOT / "plugins/attune/templates/agent-discoverability-template.md"
    text = template.read_text(encoding="utf-8")
    assert "tools_allowed:" not in text
    assert "max_iterations:" not in text
    assert "tools: [" in text
