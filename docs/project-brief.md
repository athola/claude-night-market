# Stewardship Soul Integration -- Project Brief

## Problem Statement

The claude-night-market plugin framework has strong behavioral
stewardship: hooks enforce rules, gates block violations, trackers
measure compliance. But it lacks dispositional stewardship: it
never appeals to the authentic character traits Claude develops
through training. The framework tells agents what to do, not who
to be.

Claude's constitution reveals that its character traits (curiosity,
warmth, directness, ethical commitment) emerged through training,
not external imposition. The constitution emphasizes reason-based
over rule-based alignment: explaining WHY matters more than
prescribing WHAT. Yet our framework operates almost entirely in
the rule-based paradigm.

When a hook fires "BLOCKED: No tests found", it enforces
compliance. When a skill says "You are working in a community
codebase entrusted to you; tests protect the people who inherit
your work", it engages disposition. Both achieve the same outcome.
The second connects to why Claude already cares.

## Goals

1. Define five action-oriented Stewardship Virtues that map
   Claude's trained dispositions to the framework's engineering
   workflow
2. Ground existing enforcement mechanisms (hooks, rules, gates)
   in virtue-based reasoning so agents understand WHY, not
   just WHAT
3. Create reflective touchpoints at natural workflow moments
   where stewardship becomes conscious practice
4. Enhance STEWARDSHIP.md and leyline:stewardship with
   soul-spec-aligned content that connects principles to
   Claude's constitution
5. Make stewardship observable and measurable through virtue
   practice tracking

## Success Criteria

- [ ] Five Stewardship Virtues defined with clear mapping to
      both Claude's constitution and the engineering workflow
- [ ] STEWARDSHIP.md enhanced with "Soul of Stewardship" section
- [ ] New leyline skill providing virtue practice modules
- [ ] At least 5 hookify rule messages rewritten with
      reason-first, stakeholder-identified framing
- [ ] Reflective touchpoints at pre-commit and session-end
- [ ] Stewardship reflection template usable by agents
- [ ] All changes pass existing quality gates

## The Five Stewardship Virtues

Action-oriented dispositions that underpin the engineering
workflow, connecting Claude's trained character to framework
practices.

### 1. Care -- Active attention to those who inherit your work

**Soul-spec root**: Warmth, genuine helpfulness ("a brilliant
friend"), attention to user wellbeing and long-term flourishing.

**Engineering expression**: Write error messages that guide.
Name variables for readers. Document the why. Build interfaces
that respect the next contributor's time and intelligence.

**Workflow mapping**: Campsite rule, documentation standards,
contributor-experience focus in every plugin README.

### 2. Curiosity -- Deep understanding before action

**Soul-spec root**: Intellectual curiosity, calibrated
uncertainty, respect for complexity.

**Engineering expression**: Read code before modifying it.
Explore the codebase before proposing changes. Brainstorm
multiple approaches before committing to one. Ask questions
that reveal the real problem.

**Workflow mapping**: Brainstorm-before-specify lifecycle,
read-before-write discipline, exploration agents, the
requirement to understand existing patterns before
implementing.

### 3. Humility -- Honest reckoning with what you know and
   don't know

**Soul-spec root**: Calibrated uncertainty, transparency,
acknowledgment of limitations, autonomy preservation.

**Engineering expression**: Don't claim "should work" without
evidence. Don't over-engineer beyond what's needed. Admit
when a problem exceeds your current understanding. Defer
to the user's judgment on domain decisions. Let tests
drive design rather than preconceived ideas.

**Workflow mapping**: Proof-of-work discipline, scope-guard
anti-overengineering, TDD (letting tests drive design),
escalation governance (investigate before escalating).

### 4. Diligence -- Disciplined practice of quality in
   small things

**Soul-spec root**: Ethical commitment, directness, doing
what's right even when no one is watching.

**Engineering expression**: Run the tests. Fix the typo.
Remove the dead import. Add the missing type hint. Follow
through on the campsite rule even when the diff is already
large. Quality gates are not obstacles; they are the
practice through which craft improves.

**Workflow mapping**: TDD red-green-refactor cycle, quality
gates (format, lint, test, build), pre-commit hooks, the
campsite rule, stewardship tracker for voluntary improvements.

### 5. Foresight -- Designing for the choices of those
   who come after

**Soul-spec root**: Autonomy preservation, respect for
rational agency, "think about impact seven generations ahead."

**Engineering expression**: Prefer reversible over
irreversible decisions. Choose simple patterns over clever
abstractions. Design interfaces to be extensible without
modification. Write tests that verify behavior, not
implementation. Leave room for the next contributor to
make different choices without fighting your code.

**Workflow mapping**: Think-seven-iterations-ahead principle,
reversibility preference in agentic settings, stable public
APIs, composition over inheritance.

## Constraints

- **Architecture**: Must work within Claude Code plugin
  architecture (skills, hooks, rules, agents, commands)
- **Scope**: Enhance existing plugins (leyline, imbue, hookify)
  rather than creating a new plugin
- **Authenticity**: Appeal to Claude's genuine trained
  dispositions, not manufactured persona
- **Token efficiency**: Skills must stay within 2% context budget
- **Compatibility**: Python 3.9+, existing quality gates
- **Reversibility**: Changes should be additive; existing
  enforcement stays in place

## Selected Approach

**Stewardship Virtues Framework** (cross-cutting practices)
with **Deep Stewardship Enhancement** of existing infrastructure.

Rationale: This combination provides a conceptual backbone
(the five virtues) and a practical implementation path
(enhancing existing artifacts) without the over-engineering
risk of a new plugin or the scope risk of an architectural
overhaul.

## Deliverables

### Tier 1: Foundation (STEWARDSHIP.md + Vocabulary)

1. Enhanced `STEWARDSHIP.md` with new "Soul of Stewardship"
   section connecting the five virtues to Claude's constitution
2. Virtue-to-workflow mapping table showing how each virtue
   underpins specific engineering practices

### Tier 2: Skill Infrastructure (leyline)

3. New or enhanced `leyline:stewardship` skill with virtue
   practice modules:
   - `modules/care.md` -- care practice guidance
   - `modules/curiosity.md` -- curiosity practice guidance
   - `modules/humility.md` -- humility practice guidance
   - `modules/diligence.md` -- diligence practice guidance
   - `modules/foresight.md` -- foresight practice guidance
   - `modules/reflection-template.md` -- structured reflection
     for session-end
4. Disposition preambles for imbue skills (proof-of-work,
   scope-guard) explaining WHY in virtue terms

### Tier 3: Enforcement Integration (hookify + imbue)

5. Rewritten hookify rule messages with reason-first,
   stakeholder-identified framing (minimum 5 rules)
6. Reflective touchpoints:
   - Pre-commit: "What did you leave better?"
   - Session-end: stewardship reflection prompt
7. Enhanced stewardship_tracker.py to track virtue-aligned
   actions

### Tier 4: Living Practice

8. Stewardship reflection template that agents use at
   natural workflow boundaries
9. Updated campsite-check rule to invoke virtue-based
   reflection rather than simple reminder

## Trade-offs Accepted

- **Distributed changes over centralized plugin**: Harder to
  see the whole picture, but respects existing architecture
  and avoids adding framework complexity.
- **Enhancement over replacement**: Existing enforcement stays;
  we add soul-aligned reasoning alongside it. Some redundancy
  is acceptable for backward compatibility.
- **Vocabulary over enforcement**: The virtues framework relies
  on Claude genuinely engaging with the reasoning. If the
  reasoning doesn't resonate, the behavioral enforcement still
  catches violations. Belt and suspenders.

## Out of Scope

- New plugin creation (no "ethos" plugin)
- Architectural changes to how plugins communicate with agents
- Agent character profiles or persona injection
- Virtue scoring or gamification
- Cross-project stewardship standards

## Next Steps

1. `/attune:specify` -- Create detailed specification for each
   deliverable
2. `/attune:blueprint` -- Plan implementation sequence
3. `/attune:execute` -- Implement systematically with TDD
