# Doc Consolidation Skill Design

**Date**: 2025-12-06
**Status**: Approved
**Plugin**: sanctum

## Problem Statement

LLM-assisted workflows generate ephemeral markdown files (e.g., `API_REVIEW_REPORT.md`, `REFACTORING_REPORT.md`) containing valuable insights, decisions, and action items. These files:

1. Should not be committed to git (they're working artifacts)
2. Contain knowledge worth preserving in permanent documentation
3. Currently require manual extraction and reorganization

## Goals

1. **Selective synthesis** - Extract only valuable, actionable content
2. **Dual audience** - Serve both maintainers (internal) and users (external docs)
3. **Prefer existing docs** - Merge into existing documentation when relevant
4. **Automate cleanup** - Delete source files after successful consolidation

## Design

### Skill Structure

```
plugins/sanctum/skills/doc-consolidation/
├── SKILL.md                              # Hub - orchestrates workflow
├── modules/
│   ├── candidate-detection.md            # Phase 1a: Find targets
│   ├── content-analysis.md               # Phase 1b: Extract value
│   ├── destination-routing.md            # Phase 1c: Map destinations
│   └── merge-execution.md                # Phase 2: Execute merges
└── scripts/
    └── consolidation_planner.py          # Fast model triage
```

### Two-Phase Workflow

#### Phase 1: Triage (Fast Model)

Read-only analysis delegated to haiku-class models for speed/cost:

1. **Candidate Detection**
   - Git-untracked `.md` files not in standard locations
   - ALL_CAPS naming (excluding README, LICENSE, etc.)
   - Content markers: "Executive Summary", "Findings", "Action Items"

2. **Content Analysis**
   - Extract content chunks by section
   - Categorize: Actionable Items, Decisions, Findings, Metrics, Migration Guides, API Changes
   - Score value: high/medium/low based on specificity, actionability, uniqueness

3. **Destination Routing**
   - Semantic matching against existing documentation
   - Fallback mappings for common patterns
   - Generate consolidation plan

4. **User Checkpoint**
   - Present plan for review
   - User approves/modifies before execution

#### Phase 2: Execution (Main Model)

Requires careful judgment, stays on conversation model:

1. **Merge Strategies**
   - CREATE NEW: No suitable destination exists
   - INTELLIGENT WEAVE: Add to existing sections, match style
   - REPLACE SECTION: New content more comprehensive/recent
   - APPEND WITH CONTEXT: New section with date/source reference

2. **Execution Order**
   - Group by destination file
   - Apply merges, validate results
   - Delete source files
   - Generate summary

### Detection Signals

```
Priority 1: Git Status
- Untracked .md files
- Not in: docs/, skills/, modules/, commands/, agents/

Priority 2: Naming Patterns
- ALL_CAPS (not README, LICENSE, CONTRIBUTING, CHANGELOG, SECURITY)
- Patterns: *_REPORT.md, *_ANALYSIS.md, *_REVIEW.md

Priority 3: Content Markers
- "Date:", "Executive Summary", "Findings"
- "Action Items", "Recommendations", "Conclusion"
- Structured tables with metrics
```

### Content Categories

| Category | Description | Default Destination |
|----------|-------------|---------------------|
| Actionable Items | Tasks, TODOs, next steps | `docs/plans/YYYY-MM-DD-{topic}.md` |
| Decisions Made | Architecture choices, tradeoffs | `docs/adr/NNNN-{date}-{topic}.md` |
| Findings/Insights | Audit results, analysis | Nearest relevant doc or new |
| Metrics/Baselines | Before/after, benchmarks | `docs/benchmarks/` or relevant doc |
| Migration Guides | Step-by-step procedures | `docs/migration-guide.md` |
| API Changes | Breaking changes, deprecations | `docs/api-stability.rst` or CHANGELOG |

### Merge Strategy Selection

```
INTELLIGENT WEAVE when:
- Destination has matching section header
- Content is additive (not contradictory)
- Existing section is not marked complete

REPLACE SECTION when:
- New content 2x+ more detailed
- New content has later date
- Existing marked "draft" or "TODO"

APPEND WITH CONTEXT when:
- No matching section exists
- Content doesn't fit existing structure

CREATE NEW FILE when:
- No suitable destination found
- Content warrants standalone document
```

### Fast Model Integration

Phase 1 tasks delegated to haiku-class models:

```python
FAST_MODEL_TASKS = [
    "scan_for_candidates",
    "extract_content_chunks",
    "categorize_chunks",
    "score_value",
    "find_semantic_matches",
]
```

### Trigger Conditions

**Explicit:**
- `/consolidate-docs`
- "consolidate markdown"
- "clean up LLM outputs"

**Proactive:**
- Git status shows untracked `*_REPORT.md` files
- PR prep with untracked analysis files

### Integration with Sanctum Skills

- `git-workspace-review` → Can suggest consolidation
- `pr-prep` → Warns about untracked reports
- `doc-updates` → Can be invoked for final polish

### Anti-patterns

Do NOT use when:
- Source files already in proper locations
- Files intentionally temporary
- User wants to keep report format
- No extractable value

## Consolidation Plan Format

```markdown
# Consolidation Plan

## Source: API_REVIEW_REPORT.md

### Content to Consolidate

| Content | Category | Value | Destination | Action |
|---------|----------|-------|-------------|--------|
| Plugin API inventory | Findings | High | docs/api-overview.md | Create |
| Versioning items | Actionable | High | docs/plans/... | Create |
| CLI naming decision | Decision | Med | docs/adr/... | Create ADR |

### Post-Consolidation
- Delete: API_REVIEW_REPORT.md

## Awaiting Approval
Proceed? [Y/n]
```

## Execution Summary Format

```markdown
# Consolidation Complete

## Changes Made

### Created (N files)
- path/to/new.md (size)

### Updated (N files)
- path/to/existing.md
  - Added: description
  - Strategy: WEAVE/REPLACE/APPEND

### Deleted (N files)
- source_file.md ✓

## Verification
- [ ] Review created files
- [ ] Run docs build
- [ ] Commit changes
```

## Success Criteria

1. Ephemeral reports consolidated without data loss
2. Existing documentation structure preserved
3. User has review checkpoint before changes
4. Source files cleaned up automatically
5. Fast model handles triage efficiently
