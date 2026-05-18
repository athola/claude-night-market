"""Structural tests for the /conserve:filter-log command.

Verifies:
- Command file exists at the expected path.
- YAML frontmatter has name, description, and usage.
- Command body references the log-debugging-hygiene module.
- Command body documents at least 4 of the tier-1 filter
  patterns from that module (head, tail, rg, jq, awk, sort).
- Command is registered in plugin.json under commands.
- Prose lines respect the 80-char wrap rule (with the usual
  exemptions for tables, code, frontmatter, links).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_DIR = REPO_ROOT / "plugins" / "conserve"
COMMAND_FILE = PLUGIN_DIR / "commands" / "filter-log.md"
PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
MODULE_FILE = (
    PLUGIN_DIR
    / "skills"
    / "compression-strategy"
    / "modules"
    / "log-debugging-hygiene.md"
)


def _read_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    block = text[4:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            out[key.strip()] = val.strip()
    return out


def test_command_file_exists() -> None:
    assert COMMAND_FILE.exists(), f"Command not found at {COMMAND_FILE}"


def test_command_frontmatter_has_required_fields() -> None:
    text = COMMAND_FILE.read_text()
    fm = _read_frontmatter(text)
    missing = [k for k in ("name", "description", "usage") if k not in fm]
    assert not missing, f"Frontmatter missing: {missing}"
    assert fm["name"] == "filter-log", f"Expected name=filter-log, got {fm['name']}"


def test_command_references_log_debugging_module() -> None:
    text = COMMAND_FILE.read_text()
    assert "log-debugging-hygiene" in text, (
        "Command must reference the log-debugging-hygiene module to anchor "
        "its tier-1 guidance in the existing skill content"
    )


def test_command_documents_tier1_filters() -> None:
    text = COMMAND_FILE.read_text().lower()
    patterns = ["tail", "head", "rg ", "jq ", "awk ", "sort "]
    found = [p for p in patterns if p in text]
    assert len(found) >= 4, (
        f"Command must demonstrate >=4 of the tier-1 filter patterns "
        f"{patterns}; found {found}"
    )


def test_command_warns_against_compression_first() -> None:
    text = COMMAND_FILE.read_text().lower()
    anti_pattern_markers = [
        "filter beats",
        "filter first",
        "before compression",
        "not compression",
        "tier 3",
    ]
    assert any(m in text for m in anti_pattern_markers), (
        "Command must reinforce filter-first thesis; expected one of "
        f"{anti_pattern_markers}"
    )


def test_command_registered_in_plugin_manifest() -> None:
    data = json.loads(PLUGIN_JSON.read_text())
    commands = data.get("commands", [])
    expected = "./commands/filter-log.md"
    assert expected in commands, (
        f"plugin.json must register {expected}; current commands: {commands}"
    )


def test_command_prose_wraps_at_80_chars() -> None:
    """Prose lines must wrap at 80 chars. Exempt: tables, code blocks,
    frontmatter, headings, link definitions, URLs."""
    text = COMMAND_FILE.read_text()
    lines = text.splitlines()
    in_code = False
    in_frontmatter = False
    violations: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if i == 1 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter and stripped == "---":
            in_frontmatter = False
            continue
        if in_frontmatter:
            continue
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("|"):
            continue
        if re.match(r"^\s*\[[^\]]+\]:\s+https?://", line):
            continue
        if len(line) > 80 and not re.search(r"https?://\S{40,}", line):
            violations.append((i, line))
    assert not violations, "Lines exceeding 80 chars: " + "\n".join(
        f"  {n}: {txt!r}" for n, txt in violations[:5]
    )
