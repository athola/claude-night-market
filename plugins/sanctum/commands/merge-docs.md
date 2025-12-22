---
description: Consolidate ephemeral LLM-generated markdown files into permanent documentation.
usage: /merge-docs [file...] [--scan-only] [--docs-dir PATH]
---

# Merge Documentation

Consolidates ephemeral LLM-generated markdown files (reports, analyses, reviews) into permanent documentation.

## Arguments

- `[file...]` - Optional specific file paths to consolidate. If omitted, scans for all candidates.
- `--scan-only` - Show consolidation plan without executing (dry run).
- `--docs-dir PATH` - Target documentation directory (default: `docs/`).

## Examples

```bash
# Scan and consolidate all detected candidates
/merge-docs

# Consolidate specific files
/merge-docs API_REVIEW_REPORT.md REFACTORING_REPORT.md

# Preview without executing
/merge-docs --scan-only

# Target a different docs directory
/merge-docs --docs-dir plugins/abstract/docs/
```

## Workflow

Use the `sanctum:doc-consolidation` skill to orchestrate this workflow:

1. **Load the skill**: `Skill(sanctum:doc-consolidation)`
2. **Follow the two-phase workflow**:
   - Phase 1: Detect candidates, analyze content, route destinations, present plan
   - Phase 2: Execute merges after user approval

### When Specific Files Provided

If the user provides file paths, skip candidate detection and directly analyze those files:

```python
python scripts/consolidation_planner.py analyze FILE1.md FILE2.md
python scripts/consolidation_planner.py plan FILE1.md --docs-dir docs/
```

### When No Files Provided (Default)

Scan the repository for all consolidation candidates:

```python
python scripts/consolidation_planner.py scan --repo-path .
```

Then generate plans for each detected candidate.

## What Gets Consolidated

The skill identifies files by:
- Git status (untracked `.md` files)
- Naming patterns (`*_REPORT.md`, `*_ANALYSIS.md`, `*_REVIEW.md`)
- Content markers (Executive Summary, Findings, Action Items)
- Location (not in standard directories like `docs/`, `skills/`)

## Content Categories

Content is routed based on category:

| Category | Default Destination |
|----------|---------------------|
| Actionable Items | `docs/plans/YYYY-MM-DD-{topic}.md` |
| Decisions Made | `docs/adr/NNNN-{date}-{topic}.md` |
| Findings/Insights | Best-match existing doc |
| Metrics/Baselines | `docs/benchmarks/` |
| Migration Guides | `docs/migration-guide.md` |
| API Changes | `CHANGELOG.md` or API docs |

## Integration

This command invokes the `doc-consolidation` skill. For manual control:

```bash
# Direct script usage
python plugins/sanctum/skills/doc-consolidation/scripts/consolidation_planner.py scan
python plugins/sanctum/skills/doc-consolidation/scripts/consolidation_planner.py plan FILE.md
```

## See Also

- `/update-docs` - General documentation updates
- `/git-catchup` - Understand recent git changes
- `/pr` - PR preparation (warns about untracked reports)
