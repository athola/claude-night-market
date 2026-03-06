# Stewardship Framework for Claude Night Market

**Date**: 2026-03-06
**Branch**: stewardship-1.5.7
**Status**: Draft

## Problem Statement

**Who**: Plugin users (125 skills, 98 commands across 16 plugins),
plugin contributors, and the plugins themselves as living systems.

**What**: The Night Market ecosystem has quality enforcement (pre-commit
hooks, homeostatic monitoring, quality gates) but lacks a unifying
philosophy of care. Existing tools answer "does this pass?" not "did
I leave this better?"

**Where**: Across all 16 plugins in 4 architectural layers (Meta,
Foundation, Utility, Domain).

**When**: At every interaction point: contributing code, using skills,
maintaining plugins, onboarding new contributors.

**Why**: At 16 plugins and growing, without a stewardship philosophy
the ecosystem risks uneven quality, contributor apathy, documentation
rot, and the broken windows effect. Quality gates enforce minimums;
stewardship cultivates excellence.

**Current State**: Existing infrastructure addresses detection and
enforcement but not motivation or culture:

- `abstract:homeostatic_monitor` detects skill degradation reactively
- `docs/quality-gates.md` enforces three-layer compliance
- `imbue:proof-of-work` verifies claims before completion
- `imbue:scope-guard` prevents overengineering
- `sanctum:workflow-improvement` repairs failed workflows
- `abstract:skills-eval` evaluates skill quality on demand

The gap: no framework that says "every time you touch a plugin,
leave a small gift for the next person."

## Goals

1. Establish stewardship as the central philosophy driving plugin
   development, maintenance, and contribution across the ecosystem
2. Provide concrete stewardship practices that activate
   at the point of work (not as afterthoughts)
3. Create visibility into the health and care of each plugin without
   creating punitive metrics
4. Make stewardship self-reinforcing: the framework should practice
   what it preaches

## Research Foundations

### Biblical Stewardship

The Greek word *oikonomos* (steward) means "manager of a household."
The steward manages what belongs to another, with both faithfulness
and initiative. Key principles from biblical scholarship:

1. **Ownership belongs to the master**: "The earth is the Lord's,
   and everything in it" (Psalm 24:1). In our context: the codebase
   belongs to the community, not to any individual contributor.

2. **Responsibility to multiply, not merely preserve**: The Parable
   of the Talents (Matthew 25:14-30) punishes the servant who buried
   his talent out of fear. Stewardship is generative, not just
   protective. The faithful steward actively grows what is entrusted.

3. **Faithfulness in small things**: "Whoever can be trusted with
   very little can also be trusted with much" (Luke 16:10). Small,
   consistent improvements compound. A renamed variable, an updated
   docstring, a clarified error message.

4. **Accountability**: "From everyone who has been given much, much
   will be demanded" (Luke 12:48). Those with greater access and
   capability bear greater responsibility for the ecosystem's health.

5. **The steward's reward**: "Well done, good and faithful servant"
   (Matthew 25:21). Recognition of faithful stewardship encourages
   continued care.

Sources: [TIFWE Four Principles][tifwe], [Ligonier on Biblical
Stewardship][ligonier], [1 Peter 4:10 on Spiritual Gifts][peter410]

### The Boy Scout Rule

Robert Baden-Powell: "Try and leave this world a little better than
you found it." Robert C. Martin (Uncle Bob) adapted this for
software: "Always leave the campground cleaner than you found it."
This means: check a module in cleaner than when you checked it out.
Not perfect, just better. Small improvements compound into systems
that get better with age instead of decaying.

Sources: [97 Things Every Programmer Should Know][97things],
[DevIQ Boy Scout Rule][deviq]

### Peter Block: Service Over Self-Interest

Block defines stewardship as "accountability for the well-being of
the larger organization by operating in service, rather than in
control, of those around us." Two core commitments: (1) act in
service of the long run, and (2) act in service to those with
little power. In our context: make plugins better for the users
and contributors who come after you, especially those with less
context than you have.

Source: [Stewardship: Choosing Service Over Self-Interest][block]

### Kaizen: Continuous Improvement

The Toyota Production System's twin pillars: continuous improvement
and respect for people. Kaizen teaches that improvement is everyone's
job, every day, in small increments. Not heroic rewrites but daily
acts of care. The respect for people pillar is critical: stewardship
without respect becomes surveillance.

Source: [Kaizen Wikipedia][kaizen]

### Seventh Generation Thinking

From the Haudenosaunee (Iroquois) Great Law of Peace: decisions
should consider their impact seven generations into the future.
When writing a skill, hook, or command, consider: will the person
modifying this in the seventh iteration thank me or curse me?

Source: [Seven Generation Sustainability][sevgen]

## Constraints

### Technical

- All 16 plugins across 4 layers must participate
- Python 3.9 compatibility for all hooks
- Must integrate with existing hook architecture (23 hooks)
- Cannot break plugin installation or usage patterns
- Must complement existing quality gates and homeostatic monitor

### Resources

- Single version bump scope (1.5.7)
- Implementable incrementally across three phases
- No external dependencies beyond current tooling

### Integration

- Leyline (foundation layer) for cross-cutting infrastructure
- Abstract for evaluation and monitoring integration
- Hookify for behavioral rules
- Sanctum for workflow integration points
- All 16 plugins for documentation and practice touchpoints

### Success Criteria

- [ ] Stewardship philosophy documented and discoverable in < 5 min
- [ ] Every plugin has stewardship touchpoints in its workflow
- [ ] Contributors receive concrete improvement suggestions at point
      of work
- [ ] Stewardship actions are tracked and visible (not punitive)
- [ ] The framework itself demonstrates the principles it teaches
- [ ] New contributors understand expectations without reading a book

## Approach Comparison

| Criterion | Oath | Campsite | Ledger | Garden |
|-----------|------|----------|--------|--------|
| Philosophy | High | Low | Low | High |
| Actionability | Low | High | Medium | High |
| Measurability | Low | Medium | High | High |
| Cost | Low | Medium | High | Medium |
| Sustainability | Medium | Medium | Medium | High |
| Cultural impact | Medium | Medium | Low | High |

## War Room Assessment

**Reversibility Score**: 0.25 (Type 2 decision, clearly reversible).
All approaches add new content without modifying existing behavior.
Worst case: remove unused files.

**Red Team Challenges**:

- "Docs nobody reads" (Approach 1): True risk, must pair with
  practice layer.
- "Notification fatigue" (Approach 2): Max 1-2 suggestions per
  session, prioritized by impact.
- "Goodhart's Law" (Approach 3): Frame scores as health indicators,
  not performance targets.
- "Scope creep" (Approach 4): Phase strictly with independent
  value at each stage.

**Premortem**: "The stewardship framework is unused 6 months from
now." Cause: built as infrastructure nobody asked for. Mitigation:
start with philosophy (zero code), prove value with hooks, build
metrics only after culture takes root.

## Selected Approach: The Living Garden

A three-layer framework that unifies stewardship as philosophy,
practice, and pulse:

### Layer 1: Philosophy (Phase 1)

The Steward's Manifesto, a `STEWARDSHIP.md` at project root plus
stewardship sections in every plugin README. Five principles
drawn from research:

1. **You are a steward, not an owner** (oikonomos)
2. **Multiply, do not merely preserve** (Parable of the Talents)
3. **Be faithful in small things** (The Boy Scout Rule)
4. **Serve those who come after you** (Peter Block)
5. **Think seven iterations ahead** (Seventh Generation)

### Layer 2: Practice (Phase 2)

Lightweight hooks and hookify rules that surface improvement
opportunities at the point of work:

- **Campsite Check** (prompt event rule): After working in a plugin,
  suggest 1-2 small improvements the contributor could make
- **Stewardship Actions**: Track small improvements (README
  updates, test additions, documentation fixes) as "stewardship
  contributions"
- **Contributor Guide Updates**: Each plugin gets a thin
  CONTRIBUTING section describing stewardship expectations

### Layer 3: Pulse (Phase 3)

A stewardship health view integrated with existing infrastructure:

- **Plugin Health Dimensions**: documentation freshness, test
  coverage trend, contributor friendliness, code health trend
- **Ecosystem Dashboard**: via minister plugin, aggregated view
  of stewardship health across all 16 plugins
- **Integration with Homeostatic Monitor**: stewardship signals
  feed into existing skill improvement pipeline

### Why This Approach

The Parable of the Talents teaches that stewardship is generative.
The Boy Scout Rule teaches that improvement happens at the point of
contact. Peter Block teaches that stewardship serves others, not
control. Only the Living Garden approach addresses all three
dimensions: why we care (philosophy), how we act (practice), and
whether it's working (pulse).

Each layer is independently valuable and shippable. Philosophy
first (small effort, immediate cultural impact), practice second
(medium effort, daily behavioral change), pulse third (medium
effort, long-term visibility).

## Next Steps

1. `/attune:specify` to create detailed specification for all
   three phases
2. `/attune:blueprint` to plan architecture and implementation
   tasks
3. `/attune:execute` to implement phase by phase

## References

[tifwe]: https://tifwe.org/four-principles-of-biblical-stewardship/
[ligonier]: https://learn.ligonier.org/articles/what-biblical-stewardship
[peter410]: https://www.lifebpc.com/index.php/resources/treasure-trove/31-1-2-peter/153-1-peter-4-10-11-stewardship-of-god-s-manifold-grace
[97things]: https://www.oreilly.com/library/view/97-things-every/9780596809515/ch08.html
[deviq]: https://deviq.com/principles/boy-scout-rule/
[block]: https://www.peterblock.com/books/stewardship-choosing-service-over-self-interest-2nd-edition/
[kaizen]: https://en.wikipedia.org/wiki/Kaizen
[sevgen]: https://en.wikipedia.org/wiki/Seven_generation_sustainability
