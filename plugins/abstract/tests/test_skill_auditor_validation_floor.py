"""Regression test: skill-auditor validation success floor (issue #576).

Background
----------

Daily-learning snapshots (2026-04-08..04-24) reported the
``abstract:skill-auditor`` agent at a ~40% "validation failed" rate.
Issue #461 closed three auto-improvement cycles without a verifiable
fix, and no regression test guarded the contract. This is the Phase 3
deliverable from #461: a test that fails when valid skills stop
passing the auditor's frontmatter-validation contract.

What this test covers
---------------------

The auditor cannot be driven from a unit test (it needs an LLM), so
this test pins the *output-validation contract* the auditor depends
on: ``abstract.frontmatter.FrontmatterProcessor``. It feeds a curated
corpus of known-good skill and agent frontmatter (drawn from real
patterns in this repo plus Claude Code 2.1.0 edge cases) through the
contract and asserts:

- a >= 80% pass rate floor across the corpus,
- that the canonical required set is exactly name + description, so a
  future re-tightening that requires extra fields (the suspected #576
  root cause) breaks this test,
- that 2.1.0 tool-list edge cases (list form and string form) and
  ``context: fork`` are accepted, not rejected.

What this test does NOT cover
-----------------------------

- It does not execute the agent or its LLM reasoning.
- It does not test the separate ``scripts/skill_validator.py`` script,
  whose required set (name, description, category, tags,
  estimated_tokens) diverges from the canonical contract and requires
  ``estimated_tokens``, a field no real skill in the repo sets. That
  divergence is the documented suspected cause of the failure rate and
  is tracked for a follow-up fix rather than changed here.
"""

from __future__ import annotations

import pytest

from abstract.frontmatter import FrontmatterProcessor

# Floor codified by issue #461 Phase 3: the rolling success rate on a
# known-good corpus must not fall below 80%.
SUCCESS_FLOOR = 0.80

# Curated corpus of known-good frontmatter. Every entry is a valid
# Claude Code skill or agent that the auditor must not reject.
KNOWN_GOOD_CORPUS: list[tuple[str, str]] = [
    (
        "minimal-skill",
        """---
name: minimal-skill
description: Provides a minimal valid skill. Use when testing the
  canonical two-field frontmatter contract.
---

# Minimal Skill
""",
    ),
    (
        "abstract-style-with-category-tags",
        """---
name: escalation-governance
description: 'Assess whether to escalate models. Use when evaluating reasoning depth.'
alwaysApply: false
category: agent-workflow
tags:
- escalation
- model-selection
dependencies: []
---

# Body
""",
    ),
    (
        "skill-without-category-or-tags",
        """---
name: friction-detector
description: 'Detect friction signals; graduate patterns into rules. Use for session retrospectives.'
alwaysApply: false
trigger: friction, session retrospective
model_hint: standard
---

# Body
""",
    ),
    (
        "agent-allowed-tools-list",
        """---
name: skill-auditor
model: sonnet
agent: true
context: fork
allowed-tools:
- Read
- Grep
- Glob
- Bash
description: |
  Agent for detailed skill quality auditing and improvement
  recommendations. Use when auditing skill structure and quality.
---

# Skill Auditor
""",
    ),
    (
        "agent-allowed-tools-string",
        """---
name: string-tools-agent
agent: true
allowed-tools: Read, Grep, Glob, Bash
description: Provides an agent that lists tools as a comma string. Use
  when validating string-form allowed-tools.
---

# Body
""",
    ),
    (
        "skill-with-user-invocable",
        """---
name: invocable-skill
user-invocable: true
description: Provides a user-invocable skill. Use when verifying the
  boolean user-invocable field is accepted.
---

# Body
""",
    ),
    (
        "skill-with-hooks",
        """---
name: hooked-skill
description: Provides a skill that declares a hook. Use when verifying
  valid hook structures are accepted.
hooks:
  PostToolUse:
  - command: echo done
---

# Body
""",
    ),
    (
        "skill-folded-description",
        """---
name: folded-desc-skill
description: >
  Provides a skill whose description spans multiple folded lines.
  Use when verifying folded YAML descriptions parse cleanly without
  tripping the validator.
---

# Body
""",
    ),
]


def _is_valid(content: str) -> bool:
    """Return True if frontmatter passes the canonical auditor contract.

    The contract is: required fields (name, description) present and
    non-empty, and no Claude Code 2.1.0 structural errors.
    """
    result = FrontmatterProcessor.parse(content)
    if not result.is_valid:
        return False
    errors = FrontmatterProcessor.validate_210_fields(result.parsed)
    return len(errors) == 0


@pytest.mark.unit
class TestSkillAuditorValidationFloor:
    """Guards the skill-auditor validation contract against regression."""

    def test_corpus_meets_80_percent_floor(self) -> None:
        """The known-good corpus passes at or above the 80% floor."""
        results = {name: _is_valid(content) for name, content in KNOWN_GOOD_CORPUS}
        passed = sum(1 for ok in results.values() if ok)
        rate = passed / len(results)
        failures = [name for name, ok in results.items() if not ok]
        assert rate >= SUCCESS_FLOOR, (
            f"Validation success rate {rate:.0%} fell below the "
            f"{SUCCESS_FLOOR:.0%} floor. Failing fixtures: {failures}"
        )

    def test_every_known_good_fixture_passes(self) -> None:
        """Every curated fixture is valid; none should be rejected."""
        for name, content in KNOWN_GOOD_CORPUS:
            assert _is_valid(content), f"known-good fixture rejected: {name}"

    def test_canonical_required_set_is_name_and_description(self) -> None:
        """The required set stays minimal.

        The suspected #576 root cause is a validator requiring fields
        (category, tags, estimated_tokens) that valid skills omit. If
        the canonical required set is widened, this test fails and
        surfaces the regression.
        """
        assert FrontmatterProcessor.DEFAULT_REQUIRED_FIELDS == [
            "name",
            "description",
        ]

    def test_allowed_tools_list_form_accepted(self) -> None:
        """A YAML list of allowed-tools produces no 2.1.0 errors."""
        errors = FrontmatterProcessor.validate_210_fields(
            {"allowed-tools": ["Read", "Grep", "Bash"]}
        )
        assert errors == []

    def test_allowed_tools_string_form_accepted(self) -> None:
        """A comma-separated allowed-tools string produces no errors."""
        errors = FrontmatterProcessor.validate_210_fields(
            {"allowed-tools": "Read, Grep, Bash"}
        )
        assert errors == []

    def test_context_fork_accepted(self) -> None:
        """The 2.1.0 ``context: fork`` value is accepted."""
        errors = FrontmatterProcessor.validate_210_fields({"context": "fork"})
        assert errors == []

    def test_missing_required_field_is_rejected(self) -> None:
        """A skill missing description is correctly invalid (true negative).

        Guards against the opposite failure: a validator so loose it
        passes everything would also pass this, so the floor metric
        would be meaningless.
        """
        content = """---
name: no-description
---

# Body
"""
        assert not _is_valid(content)
