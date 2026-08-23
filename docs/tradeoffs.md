---
maturity: growing
type: tradeoffs
updated: 2026-08-23
---

# Tradeoffs

Decisions made over this project's lifetime, and the alternatives
we deliberately gave up. Records the *why*, not just the *what*.

## Active index

| ID | Status | Title | Date |
|----|--------|-------|------|
| TR-001 | accepted | Test-quality vagueness is about the expectation, not the variable name | 2026-08-23 |

## Decisions

## TR-001: Test-quality vagueness is about the expectation, not the variable name

- Status: accepted
- Date: 2026-08-23
- Phase: review
- Deciders: repository owner (ratified 2026-08-23), Claude session
- Links: 617a218b, plugins/sanctum/scripts/quality_checker.py, plugins/sanctum/tests/test_quality_checker.py
<!-- key: bf5ae88ad355 -->

### Context & problem

quality_checker.py scored a 37-test file at 0/100 while every test passed and every branch it guarded was covered. Two of the four causes were rules that punished shapes which were not defects: an assertion was called vague whenever the compared variable was named `result`, and deductions were counted per issue with no cap, so file length decided the score. Both rules had existing tests pinning them, so revising them meant changing assertions that a reader could mistake for deliberate invariants.

### Decision drivers

- A score has to discriminate. 0/100 for a good long file and 0/100 for an empty one carry the same information, which is none.
- An invariant test must not be weakened silently.
- The provenance matters: SAN-008 through SAN-010 were an extraction epic that moved this predicate out of inline code. The `result ==` rule was inherited by that move, not argued for.

### Options considered

| Option | Pros | Cons / what it sacrifices |
|--------|------|---------------------------|
| Existence-only vagueness plus proportional budgets (chosen) | Flags assertions that state no expectation (bare name, comparison against None); charges each category by the share of tests it touches | Loses the naming smell the old rule caught by accident: `assert result == 5` no longer prompts a better variable name |
| Keep the name-based rule, cap the deductions only | Smaller change; the four false positives on any file using `result` stay, but capped | Still charges points for specific, correct assertions, and the category cap hides that rather than fixing it |
| Drop the assertion-quality category entirely | No false positives at all | Loses the genuine catch: a test whose only assertion is `assert result` proves nothing about the value |

### Decision

Option A. `_is_vague_result_assertion` now returns True for a bare name and for any comparison against None, and False for a comparison against a concrete value whatever the variable is called. Static categories carry budgets, and naming, assertion and BDD deductions scale with the share of tests affected.

The sequence was modify, then flag, then ratify: the three pinned tests were updated in 617a218b, surfaced for review with the preserve, layer and revise options stated, and the revision was ratified rather than reverted. Recording the order honestly matters more than implying the flag came first.

### Y-statement

In the context of scoring test quality, facing a rubric that returned 0/100 for a suite with 37 passing tests, we chose an existence-only vagueness rule and proportional category budgets over the inherited name-based heuristic and uncapped per-issue counting, to make the score discriminate between a long good file and a bad one, accepting that a generically named variable is no longer flagged by the assertion check.

### Consequences

- Positive: The same file scores 88 where it scored 0, a file with no assertions and no docstrings scores 28, and every result carries a score_breakdown naming the deduction per category
- Negative / debt accepted: Reversal is one predicate (`_is_vague_result_assertion`) plus its three tests, so this is cheap to undo if the naming smell turns out to be worth the false positives. Revisit if reviewers start seeing `result` variables spread through new test files

## Archive

Superseded or deprecated entries sink here; nothing is deleted (git keeps history).

<!-- ENTRY TEMPLATE -- copy a block into the Decisions section above the
Archive heading, assign the next TR-NNN id, and fill it in. The journal_append
helper does this automatically; this block is the fallback for hand-editing.

## TR-NNN: <short decision title>

- Status: proposed
- Date: YYYY-MM-DD
- Phase: brainstorm | specify | plan | execute | review
- Deciders: <names/roles>
- Links: <PR/commit/issue>, <code paths>

### Context & problem

<the situation forcing a choice>

### Decision drivers

- <competing quality / constraint>

### Options considered

| Option | Pros | Cons / what it sacrifices |
|--------|------|---------------------------|
| A (chosen) | ... | ... |
| B | ... | ... |

### Decision

We chose A.

### Y-statement

In the context of <X>, facing <concern>, we chose A over B,
to achieve <quality>, accepting <the sacrifice / road not taken>.

### Consequences

- Positive: <what gets easier>
- Negative / debt accepted: <what gets harder; revisit trigger>
-->
