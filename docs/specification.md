# Stewardship Soul Integration -- Specification v0.1.0

**Date**: 2026-03-10
**Status**: Draft

## Change History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2026-03-10 | Initial specification |

## Overview

**Purpose**: Deepen the claude-night-market framework's sense of
stewardship by connecting Claude's trained character dispositions
to the engineering workflow through five action-oriented virtues:
Care, Curiosity, Humility, Diligence, and Foresight.

**Scope**:

- IN: Enhance STEWARDSHIP.md, leyline:stewardship skill,
  hookify rule messages, imbue skill preambles, stewardship
  tracker, and campsite-check rule
- OUT: New plugins, architectural changes, persona injection,
  gamification, cross-project standards

**Stakeholders**:

- Claude model instances operating within the framework
  (primary: the agents whose dispositions we engage)
- Plugin contributors (secondary: benefit from clearer WHY
  behind enforcement)
- Framework users (tertiary: experience more thoughtful
  agent behavior)

## Functional Requirements

### Tier 1: Foundation

#### FR-001: Soul of Stewardship Section in STEWARDSHIP.md

**Description**: Add a new section to `STEWARDSHIP.md` that
connects the existing five stewardship principles to Claude's
constitution through the five virtues. This section bridges
the philosophical (why stewardship matters) with the
dispositional (how Claude's trained character naturally aligns
with stewardship).

**File**: `STEWARDSHIP.md`

**Content requirements**:

- Opening paragraph connecting Claude's constitution to the
  stewardship principles (reason-based, not rule-based)
- Five virtue definitions, each containing:
  - The virtue name and one-sentence action orientation
  - Connection to Claude's trained disposition (soul-spec root)
  - Connection to the engineering workflow (practice mapping)
  - The stewardship principle(s) it underpins
- A virtue-to-workflow mapping table showing how each virtue
  connects to specific framework practices (TDD, proof-of-work,
  scope-guard, campsite rule, etc.)

**Acceptance Criteria**:

- [ ] Given the existing STEWARDSHIP.md, when the new section
      is added, then the five existing principles remain
      unchanged
- [ ] Given the new section, when read by an agent, then each
      virtue clearly maps to at least one engineering practice
- [ ] Given the virtue definitions, when compared to Claude's
      constitution, then each references an authentic trained
      disposition (not a manufactured persona)
- [ ] Given the mapping table, when an agent encounters a
      workflow mechanism (e.g., TDD gate), then it can look up
      which virtue that mechanism expresses
- [ ] Prose lines wrap at 80 characters per markdown formatting
      rules
- [ ] No tier-1 slop words (structured, comprehensive,
      actionable, seamless, robust)
- [ ] Em dash count: 0-2 per 1000 words

**Priority**: High
**Dependencies**: None
**Estimated Effort**: S

---

#### FR-002: Virtue-to-Workflow Mapping Table

**Description**: A reference table within the Soul of
Stewardship section that maps each virtue to the specific
framework mechanisms it underpins. This is the practical
bridge that lets agents and contributors see WHY each
engineering practice exists.

**File**: `STEWARDSHIP.md` (within FR-001 section)

**Table structure**:

| Virtue | Disposition Root | Engineering Practice | Framework Mechanism |
|--------|-----------------|---------------------|-------------------|
| Care | warmth, helpfulness | write for inheritors | campsite rule, docs standards |
| Curiosity | intellectual curiosity | understand before changing | brainstorm-first, read-before-write |
| Humility | calibrated uncertainty | don't claim without evidence | proof-of-work, scope-guard, TDD |
| Diligence | ethical commitment | quality in small things | quality gates, pre-commit hooks |
| Foresight | autonomy preservation | protect future choices | seven-iterations principle, reversibility |

**Acceptance Criteria**:

- [ ] Given the table, when an agent reads it, then every row
      connects a virtue to at least one concrete framework
      mechanism (skill, hook, or rule)
- [ ] Given the table, when compared to plugin.json files, then
      every referenced mechanism exists in the codebase
- [ ] Table renders correctly in GitHub markdown

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: S

---

### Tier 2: Skill Infrastructure

#### FR-003: Virtue Practice Modules for leyline:stewardship

**Description**: Add five virtue practice modules to the
existing `leyline:stewardship` skill. Each module provides
concise, token-efficient guidance for an agent to practice
that virtue in the current task. Modules are referenced from
the main SKILL.md but loaded on demand.

**Files**:

- `plugins/leyline/skills/stewardship/modules/care.md`
- `plugins/leyline/skills/stewardship/modules/curiosity.md`
- `plugins/leyline/skills/stewardship/modules/humility.md`
- `plugins/leyline/skills/stewardship/modules/diligence.md`
- `plugins/leyline/skills/stewardship/modules/foresight.md`

**Per-module content requirements**:

Each module must contain:

1. **Virtue statement** (1 sentence): what this virtue means
   in engineering practice
2. **Recognition patterns** (3-5 items): situations where
   this virtue applies ("You are practicing care when...")
3. **Practice prompts** (3-5 items): concrete actions that
   express this virtue ("Before committing, ask: who will
   read this error message?")
4. **Anti-patterns** (2-3 items): what this virtue is NOT
   ("Care is not over-commenting obvious code")

**Token budget**: Each module must be under 400 words
(approximately 500 tokens) to stay within the 2% context
budget when loaded.

**Acceptance Criteria**:

- [ ] Given each module, when word count is measured, then it
      is under 400 words
- [ ] Given each module, when read by an agent during a task,
      then at least one practice prompt is actionable in the
      current context
- [ ] Given the recognition patterns, when compared to actual
      workflow moments, then they describe real situations
      agents encounter (not hypothetical scenarios)
- [ ] Given the anti-patterns, when read, then they prevent
      performative virtue (doing something to look good
      rather than to help)
- [ ] All five modules exist and are referenced in the parent
      SKILL.md frontmatter
- [ ] Prose wraps at 80 characters

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: M

---

#### FR-004: Reflection Template Module

**Description**: A structured reflection template that agents
can use at natural workflow boundaries (session-end,
pre-commit, post-PR). The template prompts genuine reflection
on stewardship impact, not just a checklist.

**File**:
`plugins/leyline/skills/stewardship/modules/reflection.md`

**Content requirements**:

1. **When to reflect**: natural boundary moments (completing a
   task, preparing a commit, ending a session)
2. **Reflection prompts** (5 total, one per virtue):
   - Care: "What did I leave better for the next person?"
   - Curiosity: "What did I learn about this code that I
     didn't know before?"
   - Humility: "Where was I uncertain, and did I handle that
     honestly?"
   - Diligence: "Did I follow through on the small things, or
     did I cut corners?"
   - Foresight: "Will the choices I made today be easy to
     change tomorrow?"
3. **Output format**: optional one-line stewardship note
   suitable for the stewardship tracker

**Token budget**: Under 300 words.

**Acceptance Criteria**:

- [ ] Given the template, when used at session-end, then an
      agent can complete a reflection in under 30 seconds
      of processing
- [ ] Given the reflection prompts, when answered honestly,
      then at least one prompt surfaces a genuine insight
      about the work done
- [ ] Given the output format, when a stewardship note is
      generated, then it is compatible with
      stewardship_tracker.py's record_action() format
- [ ] Template does not prescribe "correct" answers; it
      prompts authentic self-assessment
- [ ] Under 300 words

**Priority**: High
**Dependencies**: FR-003
**Estimated Effort**: S

---

#### FR-005: Enhanced leyline:stewardship SKILL.md

**Description**: Update the main stewardship skill to
reference the new virtue modules and reflection template.
Add a brief virtue overview section between the existing
principles and the decision table.

**File**: `plugins/leyline/skills/stewardship/SKILL.md`

**Changes**:

1. Add virtue modules to frontmatter `modules:` list
2. Add "The Five Virtues" section after "The Five Principles"
   with one-line description of each virtue and reference
   to its module
3. Add "Reflection" section after "Layer-Specific Guidance"
   referencing the reflection module
4. Update estimated_tokens to account for new content

**Acceptance Criteria**:

- [ ] Given the updated SKILL.md, when loaded by Claude Code,
      then all six modules are discoverable via frontmatter
- [ ] Given the virtue overview, when read, then an agent
      understands each virtue in one sentence without loading
      the full module
- [ ] Given the existing content (principles, decision table,
      layer guidance), when the update is applied, then no
      existing content is removed or altered
- [ ] Estimated tokens in frontmatter reflects actual content
      size (within 20%)

**Priority**: High
**Dependencies**: FR-003, FR-004
**Estimated Effort**: S

---

### Tier 3: Enforcement Integration

#### FR-006: Reason-First Hookify Rule Messages

**Description**: Rewrite the message/body content of at least
seven hookify rules to lead with WHY (connecting to a virtue
and identifying the stakeholder who benefits) before stating
WHAT is blocked or warned about. The rule's trigger logic
(conditions, patterns) remains unchanged.

**Files** (7 rules selected for rewrite):

1. `rules/stewardship/campsite-check.md` -- virtue: all five
2. `rules/git/block-force-push.md` -- virtue: Care, Foresight
3. `rules/git/block-destructive-git.md` -- virtue: Care,
   Foresight
4. `rules/python/warn-print-statements.md` -- virtue:
   Diligence
5. `rules/security/require-security-review.md` -- virtue: Care
6. `rules/workflow/enforce-scope-guard.md` -- virtue: Humility
7. `rules/workflow/plan-before-large-dispatch.md` -- virtue:
   Foresight

**Message rewrite pattern**:

Current pattern (rule-first):
```
BLOCKED: [what is blocked]
[technical explanation]
[alternatives]
```

New pattern (reason-first):
```
[1-sentence virtue connection: WHY this matters and WHO benefits]

[what is blocked/warned]
[technical explanation]
[alternatives]
```

**Example transformation for block-force-push**:

Before:
```
Force push to main/master is blocked.
This can overwrite other contributors' work...
```

After:
```
Shared history belongs to every contributor.
Force-pushing to main rewrites commits others depend on,
breaking their work and erasing their context.
(Care: protect the people who build alongside you)

Force push to main/master is blocked.
...
```

**Constraints**:

- YAML frontmatter (conditions, patterns, action, event)
  must NOT change
- Reason-first sentence must be under 25 words
- Virtue tag must be parenthetical at end of reason paragraph
- Existing technical content (alternatives, recovery steps)
  must be preserved
- Total message length increase: no more than 3 lines per rule

**Acceptance Criteria**:

- [ ] Given each rewritten rule, when the YAML frontmatter is
      compared to the original, then conditions, patterns,
      action, and event are identical
- [ ] Given each rewritten message, when the first line is
      read, then it explains WHY (not WHAT)
- [ ] Given each rewritten message, when searched for a virtue
      tag, then exactly one parenthetical virtue reference
      exists (e.g., "(Diligence: ...)")
- [ ] Given each rewritten message, when the technical content
      is compared to the original, then alternatives and
      recovery steps are preserved
- [ ] Given seven rewritten rules, when virtues are tallied,
      then at least four of the five virtues are represented
- [ ] All seven files pass markdown formatting rules

**Priority**: High
**Dependencies**: FR-001 (virtue definitions)
**Estimated Effort**: M

---

#### FR-007: Disposition Preambles for Imbue Skills

**Description**: Add a brief "disposition preamble" to the
beginning of two imbue skills (proof-of-work and scope-guard)
that connects the skill's enforcement purpose to its
underlying virtue. This is a 2-3 sentence addition to the
skill's opening content, not a change to its methodology.

**Files**:

- `plugins/imbue/skills/proof-of-work/SKILL.md`
- `plugins/imbue/skills/scope-guard/SKILL.md`

**Preamble content**:

For proof-of-work (virtue: Humility):
> Claims without evidence fail the people who depend on your
> work. Proof-of-work is the practice of humility: admitting
> that "it looks correct" is not the same as "I verified it
> works." Run it, test it, cite the evidence.

For scope-guard (virtue: Humility, Foresight):
> Building more than what's needed today takes choices away
> from the people who work here tomorrow. Scope-guard is the
> practice of humility and foresight: respecting that you
> don't know what future contributors will need, and
> preserving their freedom to decide.

**Constraints**:

- Preamble is added after the frontmatter closing `---` and
  before the first `#` heading
- Must be under 50 words per preamble
- Must not alter any existing skill content or frontmatter
- Must reference the virtue by name

**Acceptance Criteria**:

- [ ] Given each updated skill, when frontmatter is parsed,
      then it is identical to the original
- [ ] Given each preamble, when word count is measured, then
      it is under 50 words
- [ ] Given each preamble, when read by an agent before
      executing the skill, then the virtue connection is
      clear in one reading
- [ ] Given the existing skill content, when compared before
      and after, then no methodology, checklists, or red-flag
      tables are altered

**Priority**: Medium
**Dependencies**: FR-001
**Estimated Effort**: S

---

### Tier 4: Living Practice

#### FR-008: Enhanced Campsite-Check as Reflective Moment

**Description**: Transform the campsite-check hookify rule
from a simple reminder into a virtue-grounded reflective
moment. The rule currently fires on completion-related
keywords (commit, done, complete, finish, PR) with an
informational message. Enhance the message to prompt
genuine reflection using the virtue framework.

**File**:
`plugins/hookify/skills/rule-catalog/rules/stewardship/campsite-check.md`

**Changes**:

- Keep YAML frontmatter identical (event: prompt, action: info,
  same conditions)
- Replace body content with virtue-grounded reflection:
  - Lead with the stewardship principle (campsite rule)
  - Include one reflection prompt per virtue (5 total, each
    one line)
  - Reference the reflection template module for deeper
    practice
  - Keep the stewardship tracker suggestion

**Acceptance Criteria**:

- [ ] Given the updated rule, when YAML frontmatter is
      compared to original, then it is identical
- [ ] Given the updated body, when read at a completion
      moment, then it prompts genuine reflection (not just
      "did you clean up?")
- [ ] Given the five reflection prompts, when read, then
      each corresponds to exactly one virtue
- [ ] Given the message, when measured, then total length
      is under 20 lines (token efficiency)
- [ ] References reflection module path correctly

**Priority**: Medium
**Dependencies**: FR-004, FR-006
**Estimated Effort**: S

---

#### FR-009: Virtue-Aligned Stewardship Tracker

**Description**: Enhance `stewardship_tracker.py` to accept
an optional `virtue` field in recorded actions, allowing
the framework to track which virtues agents practice most
and least. This is an additive, backward-compatible change.

**File**:
`plugins/leyline/scripts/stewardship_tracker.py`

**Changes**:

1. Add optional `virtue` parameter to `record_action()`
   (default: `None` for backward compatibility)
2. Include `virtue` field in JSONL output when provided
3. Add `read_actions()` filtering by virtue (optional
   parameter, default: `None`)
4. No changes to existing function signatures or behavior
   when virtue is not provided

**Acceptance Criteria**:

- [ ] Given a call to `record_action()` without the virtue
      parameter, then output is identical to current behavior
- [ ] Given a call to `record_action(virtue="care")`, then
      the JSONL entry includes `"virtue": "care"`
- [ ] Given calls with mixed virtue/no-virtue entries, when
      `read_actions(virtue="humility")` is called, then only
      entries with `virtue="humility"` are returned
- [ ] Given the virtue parameter, when an invalid virtue name
      is passed, then the action is still recorded (no
      validation; the tracker is permissive)
- [ ] Python 3.9+ compatible (no 3.10+ syntax)
- [ ] All existing tests pass without modification
- [ ] New behavior has test coverage

**Priority**: Medium
**Dependencies**: None
**Estimated Effort**: S

---

#### FR-010: Stewardship Health Virtue Dimension

**Description**: Add a sixth health dimension to the
`/stewardship-health` command: "Virtue Practice", which
reports how many virtue-tagged stewardship actions have been
recorded for each plugin.

**File**:
`plugins/imbue/commands/stewardship-health.md`

**Changes**:

- Add "Virtue practice" to the list of health dimensions
- Describe how it is measured (count of virtue-tagged actions
  from stewardship tracker)
- Update example output table to include the new column
- Display "not practiced" when no virtue-tagged actions exist
  (never show zero or error)

**Acceptance Criteria**:

- [ ] Given the updated command, when run for a plugin with
      virtue-tagged actions, then virtue practice count is
      displayed
- [ ] Given a plugin with no virtue-tagged actions, when
      health is displayed, then "not practiced" appears
      (not "0" or blank)
- [ ] Given the example output, when rendered, then the new
      column is present and aligned
- [ ] Existing five dimensions are unchanged

**Priority**: Low
**Dependencies**: FR-009
**Estimated Effort**: S

## Non-Functional Requirements

### NFR-001: Token Efficiency

- All new skill modules combined must add fewer than 2500
  tokens to the stewardship skill's load
- Individual modules: under 500 tokens each
- Hookify message additions: under 100 tokens per rule
- Disposition preambles: under 75 tokens each

### NFR-002: Authenticity

- No manufactured persona language ("As a wise steward,
  I will...")
- No prescriptive emotions ("You should feel proud when...")
- All virtue references connect to observable engineering
  actions, not abstract ideals
- Language appeals to disposition, not roleplay

### NFR-003: Backward Compatibility

- All existing hook/rule trigger logic unchanged
- stewardship_tracker.py API unchanged for existing callers
- Existing STEWARDSHIP.md principles unchanged
- Existing leyline:stewardship decision table unchanged
- No new plugin dependencies introduced

### NFR-004: Documentation Quality

- All prose wraps at 80 characters (markdown formatting rules)
- Zero tier-1 slop words per scribe:slop-detector
- Em dashes: 0-2 per 1000 words
- No participial tail-loading

## Technical Constraints

- **Language**: Markdown for skills/rules/docs; Python 3.9+
  for stewardship_tracker.py
- **Architecture**: Claude Code plugin system (skills with
  SKILL.md + modules/, hookify rules with YAML frontmatter)
- **Quality gates**: ruff format, ruff check, pytest, mypy
  for Python changes
- **Testing**: stewardship_tracker.py changes require pytest
  test coverage

## Dependencies

| Requirement | Depends On | Reason |
|-------------|-----------|--------|
| FR-002 | FR-001 | Table lives within the Soul section |
| FR-003 | FR-001 | Modules reference virtue definitions |
| FR-004 | FR-003 | Reflection references virtue modules |
| FR-005 | FR-003, FR-004 | SKILL.md references all modules |
| FR-006 | FR-001 | Messages reference virtue names |
| FR-007 | FR-001 | Preambles reference virtue names |
| FR-008 | FR-004, FR-006 | Campsite-check uses reflection + virtues |
| FR-009 | None | Independent Python change |
| FR-010 | FR-009 | Reads virtue-tagged actions |

## Acceptance Testing Strategy

### Documentation artifacts (FR-001 through FR-008)

1. **Formatting validation**: Run markdown linting and
   slop detection on every modified .md file
2. **Content review**: Verify virtue references are
   authentic (connect to real dispositions, not persona)
3. **Integration check**: Verify all cross-references
   resolve (module paths exist, skill names match)
4. **Token measurement**: `wc -w` on each module to verify
   word count budget

### Python changes (FR-009)

1. **Unit tests**: New pytest tests for virtue parameter
   in record_action() and read_actions()
2. **Backward compatibility**: Existing tests pass
   unmodified
3. **Integration**: stewardship_tracker.py runs correctly
   with and without virtue parameter

### Command changes (FR-010)

1. **Manual verification**: Run `/stewardship-health` and
   confirm new dimension appears
2. **Edge case**: Verify "not practiced" display when no
   virtue-tagged actions exist

## Implementation Sequence

```
FR-009 (tracker)     FR-001 (STEWARDSHIP.md)
      |                     |
      v                     v
FR-010 (health cmd)  FR-002 (mapping table)
                            |
                            v
                     FR-003 (virtue modules)
                            |
                            v
                     FR-004 (reflection template)
                            |
                     +------+------+
                     |      |      |
                     v      v      v
              FR-005   FR-006   FR-007
             (SKILL)  (rules)  (imbue)
                            |
                            v
                     FR-008 (campsite-check)
```

Two parallel tracks:
- **Track A**: FR-009 -> FR-010 (Python, testable first)
- **Track B**: FR-001 -> FR-002 -> FR-003 -> FR-004 ->
  FR-005/FR-006/FR-007 -> FR-008 (documentation cascade)

## Glossary

- **Disposition**: An authentic tendency to act in a
  certain way, developed through training rather than
  imposed externally
- **Virtue**: An action-oriented disposition that underpins
  engineering practice
- **Reason-first**: Message pattern that leads with WHY
  (connecting to values and stakeholders) before stating
  WHAT (the rule or constraint)
- **Stakeholder-identified**: Message pattern that names
  WHO benefits from the constraint (future contributors,
  users, the community)
- **Disposition preamble**: A brief opening passage in a
  skill that connects the skill's purpose to its
  underlying virtue
- **Reflective touchpoint**: A natural workflow moment
  where stewardship reflection adds value

## References

- `STEWARDSHIP.md` -- existing stewardship manifesto
- `plugins/leyline/skills/stewardship/SKILL.md` -- existing
  stewardship skill
- Claude's Constitution (2026) -- Anthropic's foundational
  document defining Claude's values
- Claude Soul Spec -- internal guidance document for Claude's
  character and behavior
- `docs/project-brief.md` -- project brief from brainstorm
  phase
