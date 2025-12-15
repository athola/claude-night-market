---
name: review
description: Start a structured review workflow with evidence logging and formatted output
usage: /review [target]
---

# Start Review Workflow

Initializes a structured review workflow using imbue's core methodology: context establishment, scope inventory, evidence capture, and deliverable structuring.

## Usage

```bash
# Start review of current branch
/review

# Review specific target
/review src/auth/

# Review with specific focus
/review --focus security src/api/
```

## What It Does

1. **Establishes Context**: Confirms repository, branch, and comparison baseline
2. **Inventories Scope**: Lists relevant artifacts for review
3. **Prepares Evidence Log**: Initializes tracking for commands and citations
4. **Structures Deliverables**: Sets up report template with sections

## Workflow Integration

This command orchestrates multiple imbue skills:
- `review-core` - Core workflow scaffolding
- `evidence-logging` - Reproducible evidence capture
- `structured-output` - Consistent deliverable formatting
- `diff-analysis` - Change categorization (if diffs involved)

## Examples

```bash
/review
# Output:
# Review Workflow Initialized
# ===========================
# Repository: my-project
# Branch: feature/auth-overhaul
# Baseline: main (3 commits behind)
#
# TodoWrite items created:
# - [ ] review-core:context-established
# - [ ] review-core:scope-inventoried
# - [ ] review-core:evidence-captured
# - [ ] review-core:deliverables-structured

/review src/api --focus performance
# Scoped review with performance focus
```

## Output

Creates structured review scaffold with:
- Context summary (repo, branch, baseline)
- Scope inventory (files, configs, specs)
- Evidence log template
- Deliverable outline

## Exit Criteria

- All TodoWrite items from review-core created
- Evidence log initialized with session context
- Deliverable template ready for findings
