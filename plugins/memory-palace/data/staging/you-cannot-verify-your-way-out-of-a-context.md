---
title: You cannot verify your way out of a context problem
source:
  type: web_fetch
  identifier: https://www.sonarsource.com/blog/your-ai-agent-doesnt-know-your-codebases-context-or-constraints/
author: claude
date_captured: '2026-10-30'
palace: Agent Tooling
district: Review practice
maturity: probation
tags:
- agent-practice
- context
- rules-files
- verification
---

# You cannot verify your way out of a context problem

## Marginal Value Summary

- **Integration Decision**: standalone
- **Confidence**: 90%
- **Novelty Tags**: agent-practice, context, rules-files, verification

## Intake Content

# You cannot verify your way out of a context problem

Source: SonarSource blog, "Your AI agent doesn't know your codebase's
context or constraints", captured as a summary on 2026-10-21. The key
sentence: "You cannot verify your way out of a context problem."

Argument: prompt files, rules documents and linters are necessary but not
sufficient, because they act at the wrong point in the workflow. Linters
and PR review catch drift only after it is written, which costs
reprompting.

Practices it recommends:

- Start with context, not corrections: project-specific information before
  generation.
- Use `CLAUDE.md`-style rules files but expect upkeep. They are static and
  cannot hold a live architecture graph, the rules your history shows you
  break most, or the call flow around a change.
- Supply structured guidance: guidelines drawn from issue history, current
  architecture and intended constraints, semantic navigation to every
  location a change touches, dependency health checks.
- Verify inside the agent's loop with CI-level analysis while it writes.
- Treat context as a platform capability available to every agent.

The article is vendor content promoting its own product. The workflow
argument stands without it.

Relevance here: the counterpart to idiomatic drift. This repo's hooks
(session-start injections, vow checks) are the in-loop half.
