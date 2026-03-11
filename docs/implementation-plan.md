# Stewardship Soul Integration -- Implementation Plan

**Date**: 2026-03-10
**Status**: Ready for execution
**Estimated effort**: 14 tasks across 4 phases

## Architecture

No new components. This project enhances existing artifacts
across three plugins:

```
STEWARDSHIP.md (project root)
       |
       v
leyline:stewardship (skill + 6 new modules)
       |
       +---> imbue (2 disposition preambles)
       |
       +---> hookify (7 rule message rewrites)
       |
       v
stewardship_tracker.py (virtue parameter)
       |
       v
/stewardship-health (virtue dimension)
```

### Files Modified

| File | Change Type | FR |
|------|------------|-----|
| `STEWARDSHIP.md` | Add section | FR-001, FR-002 |
| `plugins/leyline/skills/stewardship/SKILL.md` | Update | FR-005 |
| `plugins/leyline/skills/stewardship/modules/care.md` | Create | FR-003 |
| `plugins/leyline/skills/stewardship/modules/curiosity.md` | Create | FR-003 |
| `plugins/leyline/skills/stewardship/modules/humility.md` | Create | FR-003 |
| `plugins/leyline/skills/stewardship/modules/diligence.md` | Create | FR-003 |
| `plugins/leyline/skills/stewardship/modules/foresight.md` | Create | FR-003 |
| `plugins/leyline/skills/stewardship/modules/reflection.md` | Create | FR-004 |
| `plugins/leyline/scripts/stewardship_tracker.py` | Modify | FR-009 |
| `plugins/leyline/tests/test_stewardship_tracker.py` | Create/Modify | FR-009 |
| `plugins/imbue/skills/proof-of-work/SKILL.md` | Add preamble | FR-007 |
| `plugins/imbue/skills/scope-guard/SKILL.md` | Add preamble | FR-007 |
| `plugins/imbue/commands/stewardship-health.md` | Update | FR-010 |
| `plugins/hookify/.../campsite-check.md` | Rewrite body | FR-008 |
| `plugins/hookify/.../block-force-push.md` | Add reason-first | FR-006 |
| `plugins/hookify/.../block-destructive-git.md` | Add reason-first | FR-006 |
| `plugins/hookify/.../warn-print-statements.md` | Add reason-first | FR-006 |
| `plugins/hookify/.../require-security-review.md` | Add reason-first | FR-006 |
| `plugins/hookify/.../enforce-scope-guard.md` | Add reason-first | FR-006 |
| `plugins/hookify/.../plan-before-large-dispatch.md` | Add reason-first | FR-006 |

## Task Breakdown

### Phase 1: Parallel Foundation

Two independent tracks start simultaneously.

---

#### TASK-001: Write failing tests for virtue parameter (TDD RED)

**Track**: A (Python)
**FR**: FR-009
**Type**: Testing
**Priority**: P0
**Dependencies**: None

**Description**: Write pytest tests for the new optional
`virtue` parameter in `stewardship_tracker.py`. Tests must
fail before implementation (Iron Law).

**File**: `plugins/leyline/tests/test_stewardship_tracker.py`

**Test cases**:

1. `test_record_action_without_virtue_unchanged` -- existing
   behavior preserved when virtue not provided
2. `test_record_action_with_virtue_included_in_jsonl` -- virtue
   field appears in output when provided
3. `test_record_action_virtue_none_omits_field` -- explicit
   None omits virtue from JSONL
4. `test_read_actions_filter_by_virtue` -- filtering returns
   only matching entries
5. `test_read_actions_no_virtue_filter_returns_all` -- default
   behavior unchanged
6. `test_read_actions_virtue_filter_with_mixed_entries` --
   entries without virtue field are excluded when filtering
   by virtue

**Acceptance Criteria**:

- [ ] All 6 tests written
- [ ] All 6 tests FAIL (no implementation yet)
- [ ] Tests use tmp_path fixture (no filesystem side effects)
- [ ] Python 3.9 compatible

---

#### TASK-002: Implement virtue parameter (TDD GREEN)

**Track**: A (Python)
**FR**: FR-009
**Type**: Implementation
**Priority**: P0
**Dependencies**: TASK-001

**Description**: Add the optional `virtue` parameter to
`record_action()` and virtue filtering to `read_actions()`.
Minimal implementation to pass all tests.

**File**: `plugins/leyline/scripts/stewardship_tracker.py`

**Changes**:

```python
def record_action(
    base_dir: Path,
    plugin: str,
    action_type: str,
    file_path: str,
    description: str,
    virtue: str | None = None,  # New parameter
) -> None:
```

- Add `virtue` to entry dict only when not None
- Add `virtue` parameter to `read_actions()` signature
- Filter by virtue when parameter is provided

**Acceptance Criteria**:

- [ ] All 6 tests from TASK-001 pass
- [ ] Existing tests (if any) still pass
- [ ] ruff format and ruff check clean
- [ ] mypy passes
- [ ] No Python 3.10+ syntax (use `Optional[str]` not
      `str | None` in runtime code; use
      `from __future__ import annotations`)

---

#### TASK-003: Soul of Stewardship in STEWARDSHIP.md

**Track**: B (Documentation)
**FR**: FR-001, FR-002
**Type**: Documentation
**Priority**: P0
**Dependencies**: None

**Description**: Add the "Soul of Stewardship" section to
STEWARDSHIP.md after the existing "Applying the Principles"
section. This establishes the virtue vocabulary that all
subsequent tasks reference.

**Content to write**:

1. Section heading: `## The Soul of Stewardship`
2. Opening paragraph (3-4 sentences): Connect the five
   principles to Claude's constitution. Stewardship is not
   just rules; it's a disposition that emerges from caring
   about the work and the people who inherit it. The five
   virtues name the dispositions that make the five
   principles come alive in practice.
3. Five virtue subsections (### each), containing:
   - One-sentence action orientation
   - Soul-spec root (what trained disposition it connects to)
   - Engineering expression (what it looks like in practice)
   - Which stewardship principles it underpins
4. Virtue-to-workflow mapping table (FR-002)
5. Closing paragraph connecting back to the principles

**Acceptance Criteria**:

- [ ] Existing content (principles, applying section)
      unchanged
- [ ] Five virtues defined: Care, Curiosity, Humility,
      Diligence, Foresight
- [ ] Mapping table includes all five virtues with workflow
      mechanisms
- [ ] Prose wraps at 80 characters
- [ ] No tier-1 slop words
- [ ] Em dashes: 0-2 per 1000 words
- [ ] Under 600 words total for the new section

---

### Phase 2: Virtue Modules

Sequential creation of the six modules. Each builds on the
vocabulary established in TASK-003.

---

#### TASK-004: Write virtue modules (care, curiosity, humility)

**Track**: B
**FR**: FR-003
**Type**: Documentation
**Priority**: P1
**Dependencies**: TASK-003

**Description**: Create the first three virtue practice
modules. Each module follows the same structure: virtue
statement, recognition patterns, practice prompts,
anti-patterns.

**Files**:

- `plugins/leyline/skills/stewardship/modules/care.md`
- `plugins/leyline/skills/stewardship/modules/curiosity.md`
- `plugins/leyline/skills/stewardship/modules/humility.md`

**Per-module structure**:

```markdown
# [Virtue]: [one-sentence action orientation]

## You are practicing [virtue] when...
- [recognition pattern 1]
- [recognition pattern 2]
- [recognition pattern 3]

## Practice
- [concrete action 1]
- [concrete action 2]
- [concrete action 3]

## This is not [virtue]
- [anti-pattern 1]
- [anti-pattern 2]
```

**Care module guidance**:

- Recognition: writing error messages for someone with no
  context, choosing names that serve readers, documenting
  the why
- Practice: "Before committing, re-read your error messages
  as if you've never seen this code"
- Anti-patterns: over-commenting obvious code, excessive
  hand-holding that insults intelligence

**Curiosity module guidance**:

- Recognition: reading surrounding code before modifying,
  exploring multiple approaches, asking "what does this
  code already do?"
- Practice: "Before writing, read. Before proposing, explore.
  Before deciding, brainstorm."
- Anti-patterns: researching endlessly without acting,
  curiosity as procrastination

**Humility module guidance**:

- Recognition: running tests instead of claiming correctness,
  scoping to what's needed, admitting uncertainty
- Practice: "Replace 'should work' with 'I verified by...'
  every time"
- Anti-patterns: false modesty, refusing to commit to a
  recommendation when you have evidence

**Acceptance Criteria**:

- [ ] Three module files created
- [ ] Each under 400 words
- [ ] Each follows the defined structure
- [ ] Practice prompts reference real workflow moments
- [ ] Anti-patterns prevent performative virtue
- [ ] Prose wraps at 80 characters

---

#### TASK-005: Write virtue modules (diligence, foresight)

**Track**: B
**FR**: FR-003
**Type**: Documentation
**Priority**: P1
**Dependencies**: TASK-003

**Description**: Create the remaining two virtue practice
modules.

**Files**:

- `plugins/leyline/skills/stewardship/modules/diligence.md`
- `plugins/leyline/skills/stewardship/modules/foresight.md`

**Diligence module guidance**:

- Recognition: running quality gates before committing,
  fixing the typo you noticed, following through on
  campsite improvements
- Practice: "Run format, lint, test before every commit.
  Not because a hook forces you, but because quality is
  the practice through which craft improves."
- Anti-patterns: busywork disguised as diligence, polishing
  code nobody reads while ignoring broken tests

**Foresight module guidance**:

- Recognition: choosing simple patterns over clever ones,
  writing tests that verify behavior not implementation,
  preferring reversible decisions
- Practice: "Before adding an abstraction, ask: will the
  seventh person to modify this thank me or curse me?"
- Anti-patterns: premature optimization, designing for
  requirements nobody has stated

**Acceptance Criteria**:

- [ ] Two module files created
- [ ] Each under 400 words
- [ ] Each follows the defined structure
- [ ] Prose wraps at 80 characters

---

#### TASK-006: Write reflection template module

**Track**: B
**FR**: FR-004
**Type**: Documentation
**Priority**: P1
**Dependencies**: TASK-004, TASK-005

**Description**: Create the reflection template module that
agents use at natural workflow boundaries.

**File**:
`plugins/leyline/skills/stewardship/modules/reflection.md`

**Content**:

1. When to reflect (completion, commit, session-end)
2. Five one-line reflection prompts (one per virtue)
3. Optional output format for stewardship tracker
4. Note that reflection is genuine self-assessment, not
   performance

**Acceptance Criteria**:

- [ ] Module file created
- [ ] Under 300 words
- [ ] Five reflection prompts, one per virtue
- [ ] Output format compatible with stewardship_tracker.py
- [ ] Does not prescribe "correct" answers
- [ ] Prose wraps at 80 characters

---

### Phase 3: Integration

Three independent tasks that can run in parallel. All depend
on Phase 2 vocabulary being established.

---

#### TASK-007: Update leyline:stewardship SKILL.md

**Track**: B
**FR**: FR-005
**Type**: Documentation
**Priority**: P1
**Dependencies**: TASK-006

**Description**: Update the main stewardship skill to
reference all six new modules and add a virtue overview.

**File**: `plugins/leyline/skills/stewardship/SKILL.md`

**Changes**:

1. Add to frontmatter:
   ```yaml
   modules:
     - modules/care.md
     - modules/curiosity.md
     - modules/humility.md
     - modules/diligence.md
     - modules/foresight.md
     - modules/reflection.md
   ```
2. Add "## The Five Virtues" section between "The Five
   Principles" and "Is This a Stewardship Moment?"
3. Add "## Reflection" section after "Layer-Specific
   Guidance"
4. Update `estimated_tokens` in frontmatter

**Acceptance Criteria**:

- [ ] Six modules listed in frontmatter
- [ ] Virtue overview provides one-line per virtue
- [ ] Reflection section references module
- [ ] Existing content unchanged
- [ ] estimated_tokens updated

---

#### TASK-008: Rewrite hookify rule messages (reason-first)

**Track**: B
**FR**: FR-006
**Type**: Documentation
**Priority**: P1
**Dependencies**: TASK-003

**Description**: Add reason-first opening to seven hookify
rules. YAML frontmatter unchanged. Add 1-3 lines at the
start of each rule's body that explain WHY with a virtue
tag.

**Files and virtue mappings**:

1. `block-force-push.md`
   - Reason: "Shared history belongs to every contributor
     who builds on it."
   - Virtue tag: (Care, Foresight)

2. `block-destructive-git.md`
   - Reason: "Uncommitted work represents someone's
     thinking. Destroying it erases context that can't
     be rebuilt."
   - Virtue tag: (Care)

3. `warn-print-statements.md`
   - Reason: "Print statements bypass the logging that
     future debuggers will depend on."
   - Virtue tag: (Diligence)

4. `require-security-review.md`
   - Reason: "Security-sensitive code protects the people
     who trust this system with their data."
   - Virtue tag: (Care, Diligence)

5. `enforce-scope-guard.md`
   - Reason: "Building only what's needed today preserves
     tomorrow's freedom to choose differently."
   - Virtue tag: (Humility, Foresight)

6. `plan-before-large-dispatch.md`
   - Reason: "Planning before acting respects the context
     window and the work that depends on its results."
   - Virtue tag: (Foresight)

7. `campsite-check.md` -- handled separately in TASK-010

**Acceptance Criteria**:

- [ ] Six rule files updated (campsite-check is TASK-010)
- [ ] YAML frontmatter identical to original in each file
- [ ] Each body opens with reason-first sentence (under
      25 words)
- [ ] Each has parenthetical virtue tag
- [ ] Existing technical content preserved
- [ ] At least four of five virtues represented
- [ ] Prose wraps at 80 characters

---

#### TASK-009: Add disposition preambles to imbue skills

**Track**: B
**FR**: FR-007
**Type**: Documentation
**Priority**: P2
**Dependencies**: TASK-003

**Description**: Add brief disposition preambles to two
imbue skills connecting their enforcement purpose to
stewardship virtues.

**Files**:

- `plugins/imbue/skills/proof-of-work/SKILL.md`
- `plugins/imbue/skills/scope-guard/SKILL.md`

**Preamble placement**: After frontmatter `---`, before
first `#` heading. Blockquote format.

**proof-of-work preamble** (Humility):
> Claims without evidence fail the people who depend on
> your work. Proof-of-work is humility in practice:
> "it looks correct" is not "I verified it works."

**scope-guard preamble** (Humility, Foresight):
> Building more than what's needed takes choices away
> from those who work here next. Scope-guard is humility
> and foresight: preserving freedom by building only
> what's earned.

**Acceptance Criteria**:

- [ ] Two skills updated
- [ ] Frontmatter identical to original
- [ ] Preambles under 50 words each
- [ ] Preambles reference virtue by name
- [ ] No existing methodology content altered
- [ ] Blockquote format (> prefix)

---

### Phase 4: Completion

---

#### TASK-010: Transform campsite-check rule

**Track**: B
**FR**: FR-008
**Type**: Documentation
**Priority**: P2
**Dependencies**: TASK-006, TASK-008

**Description**: Rewrite the campsite-check rule body to
be a virtue-grounded reflective moment rather than a
simple reminder.

**File**: `plugins/hookify/skills/rule-catalog/rules/stewardship/campsite-check.md`

**New body structure**:

```markdown
You're about to mark this work complete. Before you do,
the campsite rule asks: did you leave this better than
you found it?

**Quick reflection** (one per virtue):

- Care: What did you leave better for the next person?
- Curiosity: What did you learn about this code?
- Humility: Where were you uncertain? Did you handle it
  honestly?
- Diligence: Did you follow through on the small things?
- Foresight: Will your choices be easy to change tomorrow?

If any of these prompts surface an improvement you can
make in under a minute, consider making it now.

For deeper reflection, see the stewardship reflection
module: `modules/reflection.md` in `leyline:stewardship`.

Record a stewardship action with
`Skill(leyline:stewardship)` if you made a voluntary
improvement.
```

**Acceptance Criteria**:

- [ ] YAML frontmatter identical to original
- [ ] Body contains five reflection prompts (one per virtue)
- [ ] References reflection module
- [ ] References stewardship tracker
- [ ] Under 20 lines total
- [ ] Prose wraps at 80 characters

---

#### TASK-011: Update stewardship-health command

**Track**: A
**FR**: FR-010
**Type**: Documentation
**Priority**: P3
**Dependencies**: TASK-002

**Description**: Add "Virtue practice" as sixth health
dimension in the stewardship-health command.

**File**: `plugins/imbue/commands/stewardship-health.md`

**Changes**:

- Add "Virtue practice" to the dimension list with
  description of how it's measured
- Update example output table with new column
- Display "not practiced" when no virtue-tagged actions

**Acceptance Criteria**:

- [ ] Sixth dimension documented
- [ ] Example table includes new column
- [ ] "not practiced" specified for empty state
- [ ] Existing five dimensions unchanged

---

#### TASK-012: Validation pass

**Track**: Both
**FR**: All
**Type**: Testing
**Priority**: P0
**Dependencies**: All previous tasks

**Description**: Final validation of all changes.

**Steps**:

1. Run pytest on stewardship_tracker.py changes
2. Run ruff format + ruff check on Python changes
3. Run slop detection on all modified .md files
4. Verify all module word counts under budget
5. Verify all cross-references resolve (module paths,
   skill names)
6. Verify YAML frontmatter unchanged in hookify rules
7. Run existing pre-commit hooks on all changes

**Acceptance Criteria**:

- [ ] All Python tests pass
- [ ] ruff clean
- [ ] Zero slop detections
- [ ] All word count budgets met
- [ ] All cross-references valid
- [ ] Pre-commit hooks pass

## Dependency Graph

```
TASK-001 (tests RED)        TASK-003 (STEWARDSHIP.md)
    |                              |
    v                         +----+----+
TASK-002 (impl GREEN)         |         |
    |                    TASK-004    TASK-005
    v                   (care,cur,  (dil,fore)
TASK-011 (health cmd)    hum)          |
                              |         |
                              +----+----+
                                   |
                              TASK-006
                             (reflection)
                                   |
                         +---------+---------+
                         |         |         |
                    TASK-007  TASK-008  TASK-009
                    (SKILL)   (rules)  (imbue)
                         |         |         |
                         +---------+---------+
                                   |
                              TASK-010
                           (campsite-check)
                                   |
                         +---------+---------+
                         |                   |
                    TASK-011            TASK-012
                   (health)           (validation)
```

## Execution Strategy

**Parallel agents**: Tasks on Track A (TASK-001, TASK-002,
TASK-011) are independent from Track B until the validation
pass. They can execute in parallel with Track B tasks.

**Sequential within Track B**: TASK-003 must complete before
TASK-004/005, which must complete before TASK-006, which
must complete before TASK-007/008/009 (those three are
parallel), which must complete before TASK-010.

**Agent dispatch plan**:

| Phase | Parallel Agents | Tasks |
|-------|----------------|-------|
| 1 | 2 | Track A: TASK-001+002, Track B: TASK-003 |
| 2 | 1 | TASK-004, TASK-005 (sequential, same agent) |
| 3 | 1 | TASK-006 |
| 4 | 3 | TASK-007, TASK-008, TASK-009 (parallel) |
| 5 | 1 | TASK-010 |
| 6 | 1 | TASK-011, TASK-012 (sequential) |

**Total**: 6 execution phases, max 3 parallel agents.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Virtue language feels performative | Medium | Anti-patterns in each module prevent this |
| Token budget exceeded | Low | Word counts enforced per module |
| Hookify frontmatter accidentally changed | High | Acceptance criteria requires identical comparison |
| stewardship_tracker.py breaks existing callers | High | TDD ensures backward compatibility |

## Success Metrics

- [ ] All 12 tasks completed
- [ ] All acceptance criteria met
- [ ] Python tests green
- [ ] Pre-commit hooks pass
- [ ] Slop-free documentation
- [ ] Five virtues consistently referenced across all
      modified artifacts
