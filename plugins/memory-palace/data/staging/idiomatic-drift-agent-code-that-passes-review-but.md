---
title: 'Idiomatic drift: agent code that passes review but ignores house style'
source:
  type: web_fetch
  identifier: https://tianpan.co/blog/2026-06-01-the-idiom-your-coding-agent-wrote-around
author: claude
date_captured: '2026-10-30'
palace: Agent Tooling
district: Review practice
maturity: probation
tags:
- agent-practice
- code-review
- conventions
- drift
---

# Idiomatic drift: agent code that passes review but ignores house style

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: agent-practice, code-review, conventions, drift

## Intake Content

# Idiomatic drift: agent code that passes review but ignores house style

Source: tianpan.co, "The Idiom Your Coding Agent Wrote Around"
(2026-06-01), captured as a summary on 2026-10-21.

Claim: coding agents produce code that compiles, passes tests and passes
review, yet does not match the codebase's conventions. The author calls
it idiomatic drift. Over many merges the codebase splits into agent-style
and human-style zones, and linters and type checkers do not catch it,
because the conventions live in existing code rather than in a rule set.

Recommended practices:

1. An idiom index (for example `IDIOMS.md`) that points to representative
   examples, which the agent reads.
2. Retrieval before generation: search the repo for how the team already
   handles the task, and read a few examples first.
3. A post-generation idiom audit that checks a diff against nearby
   patterns, then refactors it or flags it.
4. Periodic audits for statistically unusual code, treated as a refactor
   backlog.

Figures the post cites, unverified here: AI-generated code at about 41% of
new code in large organizations (2026 surveys); a 2026 study finding AI
PRs less likely to reuse helpers; a generation-to-review ratio near 18x.

Relevance here: the same failure `pensive:code-refinement` and the
duplication lens look for, and the reason this repo's rules ask fixes to
match surrounding style.
