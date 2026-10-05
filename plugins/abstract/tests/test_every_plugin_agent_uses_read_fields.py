"""Every shipped plugin agent uses only fields Claude Code reads.

A plugin agent's ignored or misnamed field loads without error. Seven agents
declared `allowed-tools` or `tools_allowed` and ran with every tool; eleven
declared `hooks:` audit loggers that never ran; three set `permissionMode`
and inherited the session mode instead. This sweep keeps that closed.
"""

from __future__ import annotations

from pathlib import Path

from abstract.frontmatter import FrontmatterProcessor

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_no_plugin_agent_declares_an_ignored_or_misnamed_field() -> None:
    """List every finding with its file, so the fix needs no search."""
    findings = []
    for agent in sorted(REPO_ROOT.glob("plugins/*/agents/*.md")):
        result = FrontmatterProcessor.parse_file(agent)
        for error in FrontmatterProcessor.validate_plugin_agent(result.parsed):
            findings.append(f"{agent.relative_to(REPO_ROOT).as_posix()}: {error}")
    assert findings == [], "\n".join(findings)


def test_every_plugin_agent_has_a_name_and_description() -> None:
    """A nameless agent loads under its filename; one with no description
    shows the fallback text, which gives Claude no basis to delegate.
    """
    missing = []
    for agent in sorted(REPO_ROOT.glob("plugins/*/agents/*.md")):
        parsed = FrontmatterProcessor.parse_file(agent).parsed
        for field in ("name", "description"):
            if not parsed.get(field):
                missing.append(f"{agent.relative_to(REPO_ROOT).as_posix()}: {field}")
    assert missing == [], "\n".join(missing)
