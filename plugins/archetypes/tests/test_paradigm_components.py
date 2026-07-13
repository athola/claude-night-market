"""Test: every paradigm SKILL.md has a Concrete Components section.

PR #446 emptied the ``tools:`` frontmatter for all 13 paradigm
skills (correctly, since ``tools:`` is reserved for Claude Code tool
restrictions). The vocabulary that lived there has to live somewhere
visible. Issue #463 specifies that home as a Concrete Components
subsection in each SKILL.md body.

Feature: paradigm SKILL.md files surface concrete-component vocabulary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PARADIGMS_DIR = PLUGIN_ROOT / "skills"

# (skill_dir_suffix, expected_components) - extracted from issue #463
EXPECTED_COMPONENTS: dict[str, list[str]] = {
    "architecture-paradigm-client-server": [
        "api-contract-generator",
        "networking-debugger",
    ],
    "architecture-paradigm-cqrs-es": [
        "event-store",
        "message-broker",
        "projection-builder",
    ],
    "architecture-paradigm-domain-driven": [
        "ubiquitous-language-glossary",
        "context-map",
        "copy-constructor",
    ],
    "architecture-paradigm-event-driven": [
        "message-broker",
        "event-stream-processor",
        "distributed-tracing",
    ],
    "architecture-paradigm-functional-core": [
        "boundary-validator",
        "core-test-generator",
        "shell-adapter-generator",
    ],
    "architecture-paradigm-hexagonal": [
        "boundary-validator",
        "adapter-generator",
        "contract-tester",
    ],
    "architecture-paradigm-layered": [
        "dependency-validator",
        "layer-enforcer",
        "architecture-compliance-checker",
    ],
    "architecture-paradigm-microkernel": [
        "plugin-loader",
        "sandbox-executor",
        "sdk-generator",
    ],
    "architecture-paradigm-microservices": [
        "service-boundary-analyzer",
        "api-contract-generator",
        "resilience-patterns",
    ],
    "architecture-paradigm-modular-monolith": [
        "dependency-analyzer",
        "module-boundary-enforcer",
        "refactoring-planner",
    ],
    "architecture-paradigm-pipeline": [
        "stream-processor",
        "message-queue",
        "data-validator",
    ],
    "architecture-paradigm-serverless": [
        "cloud-sdk",
        "serverless-framework",
        "IaC-tools",
    ],
    "architecture-paradigm-service-based": [
        "api-gateway",
        "service-registry",
        "schema-management",
    ],
    "architecture-paradigm-space-based": [
        "data-grid-platform",
        "replication-manager",
        "load-tester",
    ],
}


@pytest.mark.parametrize("skill_dir,components", list(EXPECTED_COMPONENTS.items()))
def test_paradigm_has_concrete_components_section(
    skill_dir: str, components: list[str]
) -> None:
    """Each paradigm SKILL.md has a Concrete Components section.

    Given a paradigm SKILL.md
    When I scan the body for a Concrete Components heading
    Then the heading exists and lists the expected vocabulary items.
    """
    skill_file = PARADIGMS_DIR / skill_dir / "SKILL.md"
    assert skill_file.exists(), f"missing SKILL.md: {skill_file}"
    text = skill_file.read_text(encoding="utf-8")

    assert "## Concrete Components" in text, (
        f"{skill_dir}: missing '## Concrete Components' section"
    )
    for component in components:
        assert component in text, (
            f"{skill_dir}: Concrete Components section must mention '{component}'"
        )


def test_tools_frontmatter_remains_empty() -> None:
    """The fix in PR #446 must not regress: tools: frontmatter stays empty."""
    for skill_dir in EXPECTED_COMPONENTS:
        skill_file = PARADIGMS_DIR / skill_dir / "SKILL.md"
        text = skill_file.read_text(encoding="utf-8")
        assert "\ntools: []" in text, (
            f"{skill_dir}: tools: frontmatter must remain empty (PR #446 fix)"
        )


def test_expected_components_covers_every_paradigm_on_disk() -> None:
    """EXPECTED_COMPONENTS is the only thing driving the parametrize above.

    A paradigm added to disk but not to the dict is silently untested: no
    Concrete Components check, no tools-frontmatter regression guard. This
    test makes the dict track the filesystem so the next paradigm cannot
    skip the harness by omission.

    Given the paradigm skills on disk
    When the registered paradigm names are compared against them
    Then the two sets are equal.
    """
    on_disk = {
        path.name
        for path in PARADIGMS_DIR.glob("architecture-paradigm-*")
        if path.is_dir() and (path / "SKILL.md").exists()
    }
    registered = set(EXPECTED_COMPONENTS)

    unregistered = on_disk - registered
    assert not unregistered, (
        "paradigm(s) on disk but absent from EXPECTED_COMPONENTS, so they are "
        f"silently untested: {sorted(unregistered)}"
    )

    missing_on_disk = registered - on_disk
    assert not missing_on_disk, (
        "paradigm(s) registered in EXPECTED_COMPONENTS but not on disk: "
        f"{sorted(missing_on_disk)}"
    )
