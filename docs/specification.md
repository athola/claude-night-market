# Stewardship Framework - Specification v0.1.0

**Author**: Claude Night Market
**Date**: 2026-03-06
**Status**: Draft
**Branch**: stewardship-1.5.7

## Change History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-03-06 | stewardship-1.5.7 | Initial draft |

## Overview

**Purpose**: Establish stewardship as the central philosophy and
practice across all 16 Night Market plugins through a three-layer
framework: philosophy (why we care), practice (how we act), and
pulse (whether it's working).

**Scope**:

- **IN**: Stewardship manifesto, per-plugin stewardship sections,
  campsite-check hookify rule, stewardship action tracking,
  plugin health dimensions, leyline stewardship skill
- **OUT**: Rewriting existing plugins, new standalone plugin,
  gamified leaderboards, mandatory blocking gates

**Stakeholders**:

- Plugin users: benefit from better documentation, clearer code,
  more maintainable skills
- Plugin contributors: receive guidance on what "leaving it better"
  looks like, get recognition for stewardship actions
- Ecosystem maintainers: gain visibility into plugin health trends
  and areas needing attention

## Glossary

- **Stewardship**: Managing what is entrusted to you with
  faithfulness, initiative, and care for those who come after
- **Campsite Check**: A non-blocking prompt surfaced after working
  in a plugin, suggesting small improvements the contributor could
  make (from the Boy Scout Rule)
- **Stewardship Action**: A small, voluntary improvement made
  while working on something else: fixing a typo, updating a
  docstring, adding a test, clarifying an error message
- **Plugin Health**: A multi-dimensional view of a plugin's state
  of care: documentation freshness, test coverage, code quality
  trends, contributor friendliness
- **The Five Principles**: The core stewardship tenets derived
  from research (see FR-001)

## Functional Requirements

### FR-001: Stewardship Manifesto

**Description**: Create a `STEWARDSHIP.md` file at the project
root that defines the five stewardship principles, their research
origins, and concrete examples of what each looks like in practice
within the Night Market ecosystem.

**Acceptance Criteria**:

- [ ] Given a new contributor reading the repo, when they open
  `STEWARDSHIP.md`, then they can understand all five principles
  and at least one concrete example per principle in under 5
  minutes
- [ ] Given the five principles, when each is stated, then it
  includes: the principle name, a one-sentence definition, the
  research origin (biblical, Boy Scout, Block, Kaizen, or
  Seventh Generation), and 2-3 concrete examples from plugin
  development
- [ ] Given the manifesto, when reviewed, then it contains zero
  ambiguous language (no "might", "could", "maybe", "should
  consider")

**The Five Principles**:

1. You are a steward, not an owner (oikonomos)
2. Multiply, do not merely preserve (Parable of the Talents)
3. Be faithful in small things (Boy Scout Rule)
4. Serve those who come after you (Peter Block)
5. Think seven iterations ahead (Seventh Generation)

**Priority**: High
**Dependencies**: None
**Estimated Effort**: S

---

### FR-002: Per-Plugin Stewardship Sections

**Description**: Add a "Stewardship" section to each of the 16
plugin README.md files. Each section identifies the plugin-specific
stewardship touchpoints: what "leaving it better" looks like for
that particular plugin, what areas need the most care, and how to
contribute improvements.

**Acceptance Criteria**:

- [ ] Given any of the 16 plugins, when a contributor opens its
  README.md, then there is a "## Stewardship" section present
- [ ] Given the stewardship section, when read, then it contains:
  (a) 3-5 plugin-specific improvement opportunities, (b) a link
  to the root `STEWARDSHIP.md`, and (c) at most 20 lines of
  content
- [ ] Given a plugin in the Meta layer (abstract), when its
  stewardship section is read, then it includes guidance specific
  to skill authoring and evaluation patterns
- [ ] Given a plugin in the Foundation layer (leyline, sanctum,
  imbue), when its stewardship section is read, then it includes
  guidance on maintaining infrastructure that other plugins depend
  on

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: M

---

### FR-003: Campsite Check Hookify Rule

**Description**: Create a hookify rule that activates as a
`UserPromptSubmit` event. When a contributor's prompt indicates
they are finishing work (commit, PR, done, complete), the rule
surfaces 1-2 small, concrete improvement suggestions relevant to
the files they have been working with.

**Acceptance Criteria**:

- [ ] Given a contributor who has been editing files in
  `plugins/sanctum/`, when they type a message containing
  "commit" or "done" or "PR", then the rule outputs a brief
  stewardship reminder with at most 2 suggestions
- [ ] Given the campsite check fires, when suggestions are
  generated, then each suggestion is specific (e.g., "README.md
  last updated 45 days ago" not "consider updating docs")
- [ ] Given the campsite check, when it fires, then it completes
  in under 2 seconds and does not block the user's action
- [ ] Given a session where no plugin files were modified, when
  the contributor finishes, then the campsite check does not fire
  (no false positives)
- [ ] Given the rule format, when examined, then it follows the
  hookify rule-catalog structure with YAML frontmatter, conditions,
  and markdown body

**Priority**: High
**Dependencies**: FR-001 (references principles in output)
**Estimated Effort**: M

---

### FR-004: Stewardship Action Tracking

**Description**: Create a lightweight JSON-based tracking system
that records stewardship actions taken during sessions. A
stewardship action is any small improvement made while working on
a primary task: documentation fix, test addition, error message
improvement, type annotation addition, dead code removal.

**Acceptance Criteria**:

- [ ] Given a contributor who updates a README while working on
  a bug fix, when the session ends, then the stewardship tracker
  records the action with: timestamp, plugin name, action type,
  and file path
- [ ] Given the tracking file at
  `.claude/stewardship/actions.jsonl`, when read, then each line
  is a valid JSON object with the schema: `{"timestamp": str,
  "plugin": str, "action_type": str, "file": str, "description":
  str}`
- [ ] Given accumulated stewardship actions, when queried, then
  the system can report total actions per plugin and per action
  type
- [ ] Given the tracking system, when it records an action, then
  it adds zero latency to the contributor's workflow (append-only
  file write)

**Priority**: Medium
**Dependencies**: FR-003
**Estimated Effort**: S

---

### FR-005: Leyline Stewardship Skill

**Description**: Create a `leyline:stewardship` skill that serves
as the cross-cutting reference for stewardship principles. Other
plugins reference this skill for consistent stewardship guidance.
The skill provides: the five principles, decision heuristics for
when to take stewardship actions, and examples per plugin layer.

**Acceptance Criteria**:

- [ ] Given a skill author running `Skill(leyline:stewardship)`,
  when the skill loads, then it presents the five principles with
  layer-specific guidance
- [ ] Given the skill, when invoked, then it provides a decision
  heuristic: "Is this a stewardship moment?" with yes/no criteria
- [ ] Given the skill YAML frontmatter, when validated, then it
  passes `abstract:validate-plugin-structure` checks
- [ ] Given the skill's estimated tokens, when measured, then it
  is under 2000 tokens (leyline skills must be lightweight)

**Priority**: High
**Dependencies**: FR-001
**Estimated Effort**: S

---

### FR-006: Plugin Health Dimensions

**Description**: Define and implement measurable health dimensions
for each plugin. Dimensions are informational, not scored or
ranked. Each dimension captures a facet of plugin care.

**Acceptance Criteria**:

- [ ] Given the health dimensions, when defined, then there are
  exactly 5 dimensions: (1) documentation freshness, (2) test
  coverage, (3) code quality, (4) contributor friendliness, and
  (5) improvement velocity
- [ ] Given the documentation freshness dimension, when measured
  for a plugin, then it reports the age in days of the most
  recently modified `.md` file in that plugin
- [ ] Given the test coverage dimension, when measured, then it
  reports the line coverage percentage from the plugin's most
  recent pytest run (or "not measured" if unavailable)
- [ ] Given the improvement velocity dimension, when measured,
  then it reports the count of stewardship actions (from FR-004)
  recorded for that plugin in the last 30 days
- [ ] Given all dimensions, when displayed, then they use
  descriptive labels (e.g., "docs updated 3 days ago") not
  numeric scores or grades

**Priority**: Medium
**Dependencies**: FR-004
**Estimated Effort**: M

---

### FR-007: Stewardship Health Command

**Description**: Create a `/stewardship-health` command (in the
imbue or minister plugin) that displays the current stewardship
health dimensions for one or all plugins.

**Acceptance Criteria**:

- [ ] Given the command `/stewardship-health`, when run without
  arguments, then it displays a summary table of all 16 plugins
  with their 5 health dimensions
- [ ] Given the command `/stewardship-health sanctum`, when run
  with a plugin name, then it displays detailed health for that
  specific plugin including recent stewardship actions
- [ ] Given the command output, when displayed, then it uses
  descriptive language (e.g., "Tests: 87% coverage, up from 82%
  last month") not letter grades or numeric scores
- [ ] Given the command, when it encounters missing data (e.g.,
  no test coverage info), then it displays "not measured" rather
  than zero or an error

**Priority**: Medium
**Dependencies**: FR-006
**Estimated Effort**: M

---

### FR-008: Stewardship Integration with Existing Systems

**Description**: Connect the stewardship framework to existing
Night Market infrastructure so that stewardship signals enrich
(not replace) current systems.

**Acceptance Criteria**:

- [ ] Given the homeostatic monitor (abstract), when a plugin
  has zero stewardship actions in 60 days and declining health
  dimensions, then the monitor includes this context in its
  improvement queue entries
- [ ] Given the post-implementation protocol (sanctum Stop hook),
  when it displays the completion checklist, then it includes a
  "Stewardship" item reminding the contributor of the campsite
  check
- [ ] Given the proof-of-work skill (imbue), when a contributor
  claims completion, then stewardship actions taken during the
  session are included as positive evidence
- [ ] Given plugin.json for each plugin, when the stewardship
  skill is referenced, then it appears in the `dependencies` or
  `provides` section as appropriate

**Priority**: Low
**Dependencies**: FR-003, FR-004, FR-005, FR-006
**Estimated Effort**: M

## Non-Functional Requirements

### NFR-001: Performance - Hook Latency

**Requirement**: All stewardship hooks and rules must complete
within their timeout budget without blocking contributor workflow.

**Measurement**:

- Metric: Wall-clock execution time of campsite check rule
- Target: Under 2 seconds
- Tool: Timing output in hook stderr

**Priority**: Critical

---

### NFR-002: Compatibility - Python 3.9

**Requirement**: All hook scripts must run under Python 3.9.6
(macOS system Python) without virtual environment activation.

**Measurement**:

- Metric: Successful execution under Python 3.9.6
- Target: Zero import errors, zero syntax errors
- Tool: `python3.9 -c "import hook_module"` on CI

**Priority**: Critical

---

### NFR-003: Usability - Discoverability

**Requirement**: A new contributor must be able to find and
understand stewardship expectations within 5 minutes of first
encountering the repository.

**Measurement**:

- Metric: Clicks/steps from repo root to understanding all five
  principles
- Target: 1 click (STEWARDSHIP.md at root) or 2 clicks (plugin
  README stewardship section linking to root)
- Tool: Manual walkthrough

**Priority**: High

---

### NFR-004: Maintainability - Self-Stewardship

**Requirement**: The stewardship framework itself must demonstrate
the principles it teaches. Documentation must be fresh, tests must
exist, and the framework must be improvable by the same patterns
it promotes.

**Measurement**:

- Metric: The stewardship skill passes its own health dimensions
- Target: All 5 dimensions report healthy status
- Tool: `/stewardship-health leyline` self-check

**Priority**: High

---

### NFR-005: Culture - Non-Punitive Framing

**Requirement**: All stewardship messaging must use invitational
language ("opportunity to improve") never judgmental language
("you missed this", "failure to maintain"). Health dimensions
report state, never assign blame.

**Measurement**:

- Metric: Language review of all user-facing messages
- Target: Zero instances of blame-oriented language
- Tool: Manual review + slop detector scan

**Priority**: High

## Technical Constraints

- **Architecture**: Stewardship skill lives in leyline (foundation
  layer) so all plugins can reference it without circular
  dependencies
- **Hook format**: Campsite check follows hookify rule-catalog
  format (YAML frontmatter + markdown body)
- **Tracking format**: JSONL append-only file at
  `.claude/stewardship/actions.jsonl`
- **Plugin compatibility**: No changes to plugin.json schema; uses
  existing `provides` and `dependencies` fields
- **Version**: Ships as part of 1.5.7 version bump
- **No new dependencies**: Uses only Python stdlib and existing
  Night Market infrastructure

## Out of Scope (v1.0)

- **Gamification**: No points, badges, leaderboards, or
  competitive elements. Stewardship is service, not competition.
  Rationale: Peter Block's insight that stewardship serves the
  powerless, not the ambitious.
- **Mandatory gates**: Stewardship actions are voluntary. The
  campsite check suggests, never blocks. Rationale: Kaizen
  teaches respect for people; forced improvement breeds resentment.
- **New standalone plugin**: Stewardship is a cross-cutting
  concern, not a domain. It lives in leyline (foundation) with
  touchpoints in other plugins. Rationale: avoids another plugin
  to maintain.
- **Automated code fixes**: The campsite check suggests
  improvements but never auto-applies them. Rationale: stewardship
  requires intentional action, not automation.
- **Per-contributor tracking**: Actions are tracked per-plugin,
  not per-person. Rationale: stewardship is about the ecosystem's
  health, not individual performance reviews.

## Dependencies

- **Hookify rule catalog**: FR-003 depends on the existing
  hookify rule format and loading mechanism
- **Homeostatic monitor**: FR-008 integrates with
  `abstract:homeostatic_monitor.py`
- **Sanctum Stop hook**: FR-008 integrates with
  `sanctum:verify_workflow_complete.py`
- **Minister plugin**: FR-007 may use minister's reporting
  infrastructure for the health command
- **Quality gates**: FR-006 reads test coverage data from
  existing pytest infrastructure

## Acceptance Testing Strategy

### Phase 1 (Philosophy) Tests

1. Verify `STEWARDSHIP.md` exists at repo root and contains
   all five principles
2. Verify all 16 plugin READMEs contain a "## Stewardship"
   section
3. Verify `leyline:stewardship` skill passes frontmatter
   validation
4. Manual readability review: can a new contributor understand
   principles in under 5 minutes?

### Phase 2 (Practice) Tests

1. Verify campsite check rule loads without errors
2. Simulate a session with plugin file edits, verify campsite
   check fires with relevant suggestions
3. Simulate a session with no plugin file edits, verify campsite
   check does not fire
4. Verify stewardship action tracking writes valid JSONL
5. Verify hook execution completes under 2 seconds
6. Verify all hooks pass Python 3.9 compatibility check

### Phase 3 (Pulse) Tests

1. Verify health dimensions report for all 16 plugins without
   errors
2. Verify `/stewardship-health` command produces valid output
3. Verify missing data displays as "not measured" not as errors
4. Verify integration with homeostatic monitor context
5. Verify the stewardship framework passes its own health check
   (NFR-004)

## Success Criteria

- [ ] STEWARDSHIP.md at repo root with all five principles
- [ ] All 16 plugin READMEs have stewardship sections
- [ ] Leyline stewardship skill passes validation
- [ ] Campsite check hookify rule fires correctly
- [ ] Stewardship actions tracked in JSONL format
- [ ] Health dimensions report for all 16 plugins
- [ ] `/stewardship-health` command works for single and all
      plugins
- [ ] All hooks compatible with Python 3.9.6
- [ ] All hooks complete under 2-second timeout
- [ ] Zero blame-oriented language in user-facing messages
- [ ] New contributor can understand principles in < 5 minutes

## References

- Project Brief: `docs/project-brief.md`
- Existing quality gates: `docs/quality-gates.md`
- Homeostatic monitor ADR: `docs/adr/0006-self-adapting-skill-health.md`
- Hookify rule catalog: `plugins/hookify/skills/rule-catalog/`
- Plugin development guide: `docs/plugin-development-guide.md`
- Sanctum hooks: `plugins/sanctum/hooks/hooks.json`
