---
description: Update project documentation with consolidation, debloating, and accuracy verification.
usage: /update-docs [--skip-consolidation] [--strict] [--book-style]
---

# Update Project Documentation

Update documentation files based on recent changes while enforcing project writing guidelines. Now includes consolidation detection, directory-specific style rules, and accuracy verification.

## Arguments

- `--skip-consolidation` - Skip redundancy detection phase (Phase 2.5)
- `--strict` - Treat style warnings as errors
- `--book-style` - Apply lenient book/ rules to all files

## What's New

This command now addresses:
1. **Consolidation**: Detects redundant/bloated docs (like /merge-docs)
2. **Debloating**: Enforces directory-specific line limits and style rules
3. **Accuracy**: Validates version numbers and counts against codebase
4. **LSP Integration (2.0.74+)**: **Default approach** for documentation verification
   - Find all references to documented functions (semantic, not text-based)
   - Verify API completeness (all public APIs documented)
   - Check signature accuracy (docs match actual code)
   - **Recommended**: Enable `ENABLE_LSP_TOOLS=1` permanently
   - **Best Practice**: Always use LSP for documentation updates

## Workflow

Load the required skills in order:

1. Run `Skill(sanctum:git-workspace-review)` to capture the change context
2. Run `Skill(sanctum:doc-updates)` and follow the enhanced checklist:
   - Context collection
   - Target identification
   - **Consolidation check** (detects redundancy, bloat, staleness)
   - Edits applied
   - **Guidelines verified** (directory-specific: docs/ strict, book/ lenient)
   - **Accuracy verified** (version/count validation)
   - Preview changes

## Directory-Specific Style Rules

| Location | Style | Max File | Max Paragraph |
|----------|-------|----------|---------------|
| `docs/` | Strict reference | 500 lines | 4 sentences |
| `book/` | Technical book | 1000 lines | 8 sentences |
| Other | Default strict | 500 lines | 4 sentences |

The `book/` directory has more leeway because it follows technical book format with longer explanations and tutorials.

## Consolidation Detection

Phase 2.5 scans for:
- Untracked reports (ALL_CAPS *_REPORT.md files)
- Bloated committed docs exceeding line limits
- Stale files with outdated content

User approval is required before any:
- File deletions
- Content merges
- File splits

## Accuracy Verification

Phase 5 validates documentation claims:
- Version numbers vs `plugin.json` files
- Plugin/skill/command counts vs actual directories
- Referenced file paths exist

**LSP-Enhanced Verification (2.0.74+)**:
When `ENABLE_LSP_TOOLS=1` is set:
- Find all public APIs and check documentation coverage
- Verify function signatures match documented examples
- Locate all references to show usage patterns
- Cross-reference documentation with actual code structure

Warnings are non-blocking; user decides whether to fix.

## Examples

```bash
# Standard documentation update
/update-docs

# Quick update without consolidation check
/update-docs --skip-consolidation

# Strict mode: treat all warnings as errors
/update-docs --strict

# Apply lenient rules everywhere (for book-like docs)
/update-docs --book-style
```

## Manual Execution

If a skill cannot be loaded, follow these steps:
- Manually gather the Git context (`pwd`, `git status -sb`, `git diff --stat`, `git diff`)
- Check for bloated docs/ files: `find docs/ -name '*.md' -exec wc -l {} \; | awk '$1 > 500'`
- Check for bloated book/ files: `find book/ -name '*.md' -exec wc -l {} \; | awk '$1 > 1000'`
- Validate versions: `for p in plugins/*/.claude-plugin/plugin.json; do jq -r '"\(.name): \(.version)"' "$p"; done`
- Update each document using the guidelines and preview the resulting diffs

## See Also

- `/merge-docs` - Full consolidation workflow for complex multi-file merges
- `/update-readme` - README-specific updates with exemplar research
- `/git-catchup` - Understand recent git changes
