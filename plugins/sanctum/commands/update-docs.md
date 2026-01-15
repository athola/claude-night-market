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
   - **Recommended**: Enable `ENABLE_LSP_TOOL=1` permanently
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
| `wiki/` | Wiki reference | 500 lines | 4 sentences |
| `plugins/*/README.md` | Plugin summary | 300 lines | 4 sentences |
| Other | Default strict | 500 lines | 4 sentences |

The `book/` directory has more leeway because it follows technical book format with longer explanations and tutorials. Plugin READMEs should be concise summaries.

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
When `ENABLE_LSP_TOOL=1` is set:
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

### 1. Gather Git Context
```bash
pwd && git status -sb && git diff --stat
```

### 2. Check All Doc Locations for Bloat
```bash
# docs/ - strict (500 lines)
find docs/ -name '*.md' -exec wc -l {} \; 2>/dev/null | awk '$1 > 500'

# book/ - lenient (1000 lines)
find book/ -name '*.md' -exec wc -l {} \; 2>/dev/null | awk '$1 > 1000'

# wiki/ - strict (500 lines)
find wiki/ -name '*.md' -exec wc -l {} \; 2>/dev/null | awk '$1 > 500'

# Plugin READMEs - summary (300 lines)
for f in plugins/*/README.md; do
  [ -f "$f" ] && lines=$(wc -l < "$f") && [ "$lines" -gt 300 ] && echo "$lines $f"
done
```

### 3. Validate Versions
```bash
for p in plugins/*/.claude-plugin/plugin.json; do
  jq -r '"\(.name): \(.version)"' "$p" 2>/dev/null
done
```

### 4. Update Documents and Preview
- Update each document using the directory-specific guidelines
- Preview the resulting diffs with `git diff`

## Output Examples

### Consolidation Detection Output

When Phase 2.5 runs, you'll see a table of detected candidates:

```markdown
## Phase 2.5: Consolidation Opportunities

### Untracked Reports (merge or delete)

| File | Score | Markers | Recommendation |
|------|-------|---------|----------------|
| API_REVIEW_REPORT.md | 6 | Executive Summary, Findings | Merge to docs/api-overview.md |
| MIGRATION_NOTES.md | 4 | Action Items, Tables | Merge to docs/migration-guide.md |

### Bloated Files (split or trim)

| File | Lines | Threshold | Recommendation |
|------|-------|-----------|----------------|
| docs/architecture-analysis-report.md | 571 | 500 | Consider splitting by section |
| book/src/tutorials/advanced-workflows.md | 1031 | 1000 | Split into multiple tutorials |

---

**Options:**
- `Y` - Proceed with all recommended actions
- `n` - Skip consolidation, continue to edits
- `select` - Choose specific items to address
```

Use `--skip-consolidation` to bypass this phase entirely.

### Accuracy Verification Output

Phase 5 validates documentation claims against the codebase:

```markdown
## Accuracy Scan Results

Scanned: docs/api-overview.md, README.md (2 files)
Time: 0.3 seconds

### Warnings Found

| Type | File | Line | Issue | Fix |
|------|------|------|-------|-----|
| version | docs/api-overview.md | 15 | abstract v2.1.0 → 1.2.7 | Update |
| version | book/src/plugins/sanctum.md | 18 | sanctum v3.0.0 → 1.2.7 | Update |
| count | README.md | 42 | "11 plugins" → 8 | Update |

### No Issues
- All file paths valid
- Command references exist

**Action**: Review warnings before proceeding to preview.
```

Warnings are **non-blocking** - you decide whether to fix them.

### Style Violation Output

Directory-specific style rules are enforced:

```markdown
## Style Check Results

### docs/ (strict mode)

| File | Issue | Severity |
|------|-------|----------|
| docs/api-overview.md:45 | Paragraph exceeds 4 sentences | Warning |
| docs/architecture-analysis-report.md | File exceeds 500 lines (571) | Warning |

### book/ (lenient mode)

| File | Issue | Severity |
|------|-------|----------|
| book/src/tutorials/error-handling.md:120 | Paragraph exceeds 8 sentences | Warning |

### Filler Phrases Detected

| File | Line | Phrase |
|------|------|--------|
| docs/api-overview.md | 23 | "I'd be happy to" |
| docs/getting-started.md | 15 | "leverage" (overused) |
```

Style warnings help maintain documentation quality but don't block the workflow.

## See Also

- `/merge-docs` - Full consolidation workflow for complex multi-file merges
- `/update-readme` - README-specific updates with exemplar research
- `/git-catchup` - Understand recent git changes
