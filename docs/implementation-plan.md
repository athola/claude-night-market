# Markdown Formatting Enhancement - Implementation Plan v0.1.0

**Author**: Claude (attune mission)
**Date**: 2026-03-04
**Target Completion**: Single session

## Architecture

### System Overview

This is an instruction-propagation project: one shared module
defines canonical formatting rules, and N skills reference it.
No code is written. All changes are to markdown skill/module
files that guide agent behavior.

### Component Diagram

```
leyline:markdown-formatting (SHARED MODULE)
    ├── SKILL.md (canonical rules + examples)
    └── modules/
        └── wrapping-rules.md (detailed algorithm)

Referenced by:
    ├── scribe:doc-generator/modules/generation-guidelines.md
    ├── sanctum:doc-updates/modules/directory-style-rules.md
    ├── sanctum:update-readme/SKILL.md
    ├── sanctum:tutorial-updates/modules/markdown-generation.md
    ├── sanctum:doc-consolidation/SKILL.md
    └── .claude/rules/markdown-formatting.md
         └── .claude/rules/slop-scan-for-docs.md (updated)
```

### Data Flow

1. Agent receives task to generate/modify documentation
2. Skill loads (e.g., doc-generator, doc-updates)
3. Skill references leyline:markdown-formatting module
4. Agent follows wrapping rules when writing prose
5. Post-write: slop-scan rule reminds to check formatting

## Task Breakdown

### Phase 1: Foundation (TASK-001 to TASK-002)

#### TASK-001: Create Shared Formatting Module

**Description**: Create `leyline:markdown-formatting` skill with
SKILL.md and modules/wrapping-rules.md containing all canonical
formatting rules, exemptions, and examples.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 5 points
**Dependencies**: None
**Linked Requirements**: FR-001, FR-002, FR-003, FR-004, FR-005,
FR-006, FR-007

**Files to create**:
- `plugins/leyline/skills/markdown-formatting/SKILL.md`
- `plugins/leyline/skills/markdown-formatting/modules/wrapping-rules.md`

**Content requirements for SKILL.md**:
- Overview of formatting conventions
- Quick-reference checklist
- When to apply (prose text blocks)
- When NOT to apply (tables, code, headings, etc.)
- Cross-reference to wrapping-rules module

**Content requirements for wrapping-rules.md**:
- Hybrid wrapping algorithm with priority order
- Sentence boundary rules (. ! ?)
- Clause boundary rules (, ; :)
- Conjunction rules (and, but, or)
- Word boundary fallback
- Exemption list with examples
- Before/after examples for each rule
- Blank lines around headings rule
- ATX-only headings rule
- Blank line before lists rule
- Reference-style links rule

**Acceptance Criteria**:
- [ ] SKILL.md exists with frontmatter
- [ ] wrapping-rules.md has before/after examples
- [ ] Exemption list covers all 8 content types
- [ ] Module itself follows the 80-char wrapping rules

---

#### TASK-002: Create Claude Rule for Markdown Formatting

**Description**: Create `.claude/rules/markdown-formatting.md`
with quick-reference formatting checklist and update
`slop-scan-for-docs.md` to reference it.

**Type**: Implementation
**Priority**: P0 (Critical)
**Estimate**: 2 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-013, FR-014

**Files to create/modify**:
- CREATE: `.claude/rules/markdown-formatting.md`
- EDIT: `.claude/rules/slop-scan-for-docs.md`

**Acceptance Criteria**:
- [ ] Rule file exists with formatting checklist
- [ ] Slop-scan rule references markdown-formatting rule
- [ ] Rule content follows 80-char wrapping

---

### Phase 2: Skill Updates (TASK-003 to TASK-007)

All tasks in this phase can be executed in parallel.

#### TASK-003: Update Scribe Doc-Generator

**Description**: Add formatting instructions to doc-generator's
generation-guidelines module referencing the shared module.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-008

**Files to modify**:
- EDIT: `plugins/scribe/skills/doc-generator/modules/generation-guidelines.md`

**Changes**: Add a "Line Wrapping" section after "Paragraph
Guidance" that describes the hybrid wrapping rules and
references `leyline:markdown-formatting` for full details.
Add a before/after example showing wrapped prose.

---

#### TASK-004: Update Sanctum Doc-Updates

**Description**: Add formatting rules to directory-style-rules
module, adding prose line wrapping as a shared rule.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 3 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-009

**Files to modify**:
- EDIT: `plugins/sanctum/skills/doc-updates/modules/directory-style-rules.md`

**Changes**: Add to "Shared Rules (All Locations)" section:
- Prose text wraps at 80 chars (hybrid, sentence-preference)
- Blank lines around headings
- ATX headings only
- Blank line before lists
- Reference `leyline:markdown-formatting` for full rules

---

#### TASK-005: Update Sanctum Update-README

**Description**: Add formatting reference to update-readme
SKILL.md.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 2 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-010

**Files to modify**:
- EDIT: `plugins/sanctum/skills/update-readme/SKILL.md`

**Changes**: Add formatting reference to the skill, noting
that all README prose should follow
`leyline:markdown-formatting` conventions.

---

#### TASK-006: Update Tutorial Markdown Generation

**Description**: Add wrapping instructions to the
markdown-generation module for both tones.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 2 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-011

**Files to modify**:
- EDIT: `plugins/sanctum/skills/tutorial-updates/modules/markdown-generation.md`

**Changes**: Add to "Common Rules (Both)" section:
- Prose wraps at 80 chars following
  `leyline:markdown-formatting` rules
- Reference-style links when URLs are long

---

#### TASK-007: Update Doc-Consolidation

**Description**: Add formatting reference to doc-consolidation
skill's merge execution module.

**Type**: Implementation
**Priority**: P2 (Medium)
**Estimate**: 2 points
**Dependencies**: TASK-001
**Linked Requirements**: FR-012

**Files to modify**:
- EDIT: `plugins/sanctum/skills/doc-consolidation/SKILL.md`

**Changes**: Add note that merged content should follow
`leyline:markdown-formatting` conventions.

---

### Phase 3: Plugin Registration (TASK-008)

#### TASK-008: Register New Skill in Leyline Plugin

**Description**: Add the markdown-formatting skill to leyline's
plugin.json registration.

**Type**: Implementation
**Priority**: P1 (High)
**Estimate**: 1 point
**Dependencies**: TASK-001
**Linked Requirements**: FR-001

**Files to modify**:
- EDIT: `plugins/leyline/.claude-plugin/plugin.json`

---

## Dependency Graph

```
TASK-001 (Shared Module) [P0, 5pts]
    ├──▶ TASK-002 (Claude Rules) [P0, 2pts]
    ├──▶ TASK-003 (Scribe Doc-Gen) [P1, 3pts]
    ├──▶ TASK-004 (Sanctum Doc-Updates) [P1, 3pts]
    ├──▶ TASK-005 (Sanctum README) [P1, 2pts]
    ├──▶ TASK-006 (Tutorial Markdown) [P1, 2pts]
    ├──▶ TASK-007 (Doc-Consolidation) [P2, 2pts]
    └──▶ TASK-008 (Plugin Registration) [P1, 1pt]
```

Critical path: TASK-001 → TASK-002 (everything else parallel)

## Execution Strategy

**Phase 1** (sequential): TASK-001, then TASK-002
**Phase 2** (parallel via subagents): TASK-003 through TASK-008

Phase 2 tasks are independent and can be dispatched to parallel
agents since each modifies a different file.

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Rules too verbose | Med | Med | Keep module under 200 lines |
| Agents ignore formatting | Med | Low | Rules file enforces reminder |
| Wrapping breaks links | High | Low | Explicit exemption list |

## Success Metrics

- [ ] 2 new files created (leyline skill + Claude rule)
- [ ] 6 existing files updated with formatting references
- [ ] All modified files follow 80-char wrapping themselves
- [ ] No rendering changes to existing documentation

## Next Steps

1. Execute Phase 1: Create shared module and rules
2. Execute Phase 2: Update all skills in parallel
3. Verify all files follow the conventions they describe
