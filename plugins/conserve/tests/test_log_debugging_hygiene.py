"""Structural and honesty tests for the log-debugging-hygiene module.

Verifies:
- Module file exists in the expected location.
- Module contains the documented tier structure.
- Exit Criteria section is present with falsifiable checkboxes
  (per .claude/rules/skill-exit-criteria.md).
- Parent SKILL.md references the module.
- The "filter beats compress" claim is reproducible on the
  committed intake_queue.jsonl fixture.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO_ROOT / "plugins" / "conserve" / "skills" / "compression-strategy"
MODULE_FILE = SKILL_DIR / "modules" / "log-debugging-hygiene.md"
PARENT_SKILL = SKILL_DIR / "SKILL.md"
FIXTURE = REPO_ROOT / "plugins" / "memory-palace" / "data" / "intake_queue.jsonl"


def test_module_file_exists() -> None:
    assert MODULE_FILE.exists(), f"Module not found at {MODULE_FILE}"


def test_module_has_required_sections() -> None:
    content = MODULE_FILE.read_text()
    required = [
        "# Log Debugging Hygiene",
        "## When to Use",
        "## Tier 1",
        "## Tier 2",
        "## Tier 3",
        "## Exit Criteria",
    ]
    missing = [s for s in required if s not in content]
    assert not missing, f"Missing required sections: {missing}"


def test_exit_criteria_has_falsifiable_checkboxes() -> None:
    content = MODULE_FILE.read_text()
    if "## Exit Criteria" not in content:
        pytest.fail("Exit Criteria section missing")
    exit_section = content.split("## Exit Criteria", 1)[1]
    next_h2 = re.search(r"\n##\s", exit_section)
    if next_h2:
        exit_section = exit_section[: next_h2.start()]
    boxes = re.findall(r"^\s*-\s*\[\s\]\s+\S", exit_section, re.MULTILINE)
    assert len(boxes) >= 3, (
        f"Need >=3 falsifiable exit criteria checkboxes; "
        f"found {len(boxes)} in Exit Criteria section"
    )


def test_parent_skill_references_module() -> None:
    content = PARENT_SKILL.read_text()
    assert "log-debugging-hygiene" in content, (
        "Parent SKILL.md must reference the log-debugging-hygiene "
        "module so progressive loading can resolve it."
    )


def test_module_avoids_em_dashes() -> None:
    """Cap em-dashes per slop-scan layer 2.

    Target is 0-2 em-dashes per 1000 words per
    .claude/rules/slop-scan-for-docs.md. Module is small so we cap
    at 2 absolute.
    """
    content = MODULE_FILE.read_text()
    em_count = content.count("—")
    assert em_count <= 2, (
        f"Module has {em_count} em-dashes; replace with colons, "
        "periods, commas, or parentheses (slop-scan layer 2)."
    )


def test_module_lacks_unsupported_accuracy_claim() -> None:
    """Forbid unsupported LLM accuracy claims in the module body.

    Lit review showed 'LLMs work better on compressed logs' is
    unsupported for log debugging. Module must not repeat that
    claim as its own assertion. Quoting the phrase inside the
    Anti-Patterns section to warn against it is allowed.
    """
    content = MODULE_FILE.read_text()
    # Strip the Anti-Patterns section so warnings that quote the
    # banned phrase do not trip the check.
    body = re.split(
        r"^##\s+Anti-Patterns\b",
        content,
        maxsplit=1,
        flags=re.MULTILINE,
    )[0]
    body_lower = body.lower()
    banned_phrases = [
        "improves accuracy",
        "better accuracy",
        "work better on compressed",
        "models work better on compressed",
    ]
    hits = [p for p in banned_phrases if p in body_lower]
    assert not hits, (
        f"Module asserts unsupported accuracy claims: {hits}. "
        "Reframe as 'preserves accuracy while saving tokens' "
        "(LLMLingua family) and cite evidence. Quoting the banned "
        "phrase inside Anti-Patterns to warn against it is allowed."
    )


@pytest.mark.skipif(not FIXTURE.exists(), reason="intake_queue.jsonl fixture missing")
def test_filter_first_claim_is_reproducible() -> None:
    """Verify the filter-first benchmark on the committed fixture.

    The module claims Tier 1 (e.g. `tail -n 100`) achieves >=90%
    byte reduction on highly-repetitive committed logs. Verify on
    the actual intake_queue.jsonl fixture so the claim cannot rot
    silently.
    """
    orig_bytes = FIXTURE.stat().st_size
    result = subprocess.run(  # noqa: S603 - hardcoded argv, no shell, fixture path resolved from repo root
        ["tail", "-n", "100", str(FIXTURE)],  # noqa: S607 - partial path tail intentional; system PATH only
        capture_output=True,
        check=True,
    )
    tail_bytes = len(result.stdout)
    savings = 1 - tail_bytes / orig_bytes
    assert savings >= 0.90, (
        f"tail -n 100 should achieve >=90% byte reduction on the "
        f"committed intake_queue.jsonl fixture; got {savings:.2%}. "
        f"Either the fixture changed or the module claim is no "
        f"longer accurate."
    )
