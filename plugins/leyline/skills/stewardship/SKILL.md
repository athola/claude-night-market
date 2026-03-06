---
name: stewardship
description: >-
  Consult this skill when working on any plugin to apply
  stewardship principles. Provides the five principles,
  layer-specific guidance, and a decision heuristic for
  identifying stewardship moments during development.
category: cross-plugin-patterns
tags:
  - stewardship
  - quality
  - culture
  - maintenance
  - contributor-experience
tools: []
complexity: low
estimated_tokens: 1200
progressive_loading: false
dependencies: []
---

# Stewardship

Apply these principles whenever you touch a plugin. The full
manifesto with research origins is at `STEWARDSHIP.md` in the
project root.

## The Five Principles

1. **You are a steward, not an owner**: the codebase belongs to
   the community. Write for the reader, not yourself.
2. **Multiply, do not merely preserve**: improve what you touch.
   Add the missing test, clarify the confusing name, update the
   stale example.
3. **Be faithful in small things**: fix the typo, remove the dead
   import, add the type hint. Small acts compound.
4. **Serve those who come after you**: write for the contributor
   who arrives with no context. Prioritize their experience.
5. **Think seven iterations ahead**: prefer simple, transparent
   patterns. Will this design hold up after seven major changes?

## Is This a Stewardship Moment?

Ask yourself these questions when working in a plugin:

| Question | If yes | Principle |
|----------|--------|-----------|
| Did I just read confusing code? | Leave a clarifying comment | 4 |
| Is this README stale? | Update it while context is fresh | 2 |
| Did I notice a typo or dead code? | Fix it now, it takes 10 seconds | 3 |
| Am I adding a clever abstraction? | Reconsider: will iteration 7 thank me? | 5 |
| Am I writing for myself or the community? | Rewrite for the reader | 1 |

**If no questions trigger**: you're in a clean area. Keep it
that way.

**If any question triggers**: take the small action. It costs
seconds and pays dividends for every future reader.

## Layer-Specific Guidance

### Meta (abstract)

You maintain the tools that maintain everything else. Your
stewardship priority: stability and clarity of skill authoring
patterns. When evaluation frameworks change, downstream plugins
feel it. Move carefully, document thoroughly, test rigorously.

### Foundation (leyline, sanctum, imbue)

You maintain infrastructure every other plugin depends on.
Your stewardship priority: backward compatibility and clear
migration paths. When you change a leyline pattern, 15 plugins
may need to adapt. Prefer additive changes. Write migration
guides when breaking changes are unavoidable.

### Utility (conserve, conjure, hookify)

You maintain tools contributors interact with daily. Your
stewardship priority: user experience and low friction.
If a hook is confusing, contributors disable it. If a rule
is noisy, contributors ignore it. Tune for signal, not volume.

### Domain (all others)

You maintain specialized expertise. Your stewardship priority:
accuracy and accessibility. Domain knowledge is valuable only
when others can access it. Write examples, not just references.
Keep domain skills current as the underlying domain evolves.
