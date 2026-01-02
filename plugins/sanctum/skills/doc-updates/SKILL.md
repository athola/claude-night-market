---
name: doc-updates
description: |
  Update documentation with writing guideline enforcement, consolidation detection, and accuracy verification.

  Triggers: documentation update, docs update, ADR, docstrings, writing guidelines, readme update, debloat docs

  Use when: updating documentation after code changes, enforcing writing guidelines, maintaining ADRs

  DO NOT use when: README-specific updates - use update-readme instead.
  DO NOT use when: complex multi-file consolidation - use doc-consolidation.

  Use this skill for general documentation updates with built-in quality gates.
category: artifact-generation
tags: [documentation, readme, adr, docstrings, writing, consolidation, debloat]
tools: [Read, Write, Edit, Bash, TodoWrite]
complexity: medium
estimated_tokens: 1200
progressive_loading: true
modules:
  - adr-patterns
  - directory-style-rules
  - accuracy-scanning
  - consolidation-integration
dependencies:
  - sanctum:shared
  - sanctum:git-workspace-review
  - imbue:evidence-logging
---

# Documentation Update Workflow

## When to Use

Use this skill when code changes require updates to the README, plans, wikis, or docstrings.
Run `Skill(sanctum:git-workspace-review)` first to capture the change context.

**New capabilities:**
- Detects consolidation opportunities (like /merge-docs)
- Enforces directory-specific style rules (docs/ strict, book/ lenient)
- Validates accuracy of version numbers and counts
- LSP integration (2.0.74+) for semantic documentation verification

## Required TodoWrite Items

1. `doc-updates:context-collected`
2. `doc-updates:targets-identified`
3. `doc-updates:consolidation-checked` (NEW - skippable)
4. `doc-updates:edits-applied`
5. `doc-updates:guidelines-verified`
6. `doc-updates:accuracy-verified` (NEW)
7. `doc-updates:preview`

## Step 1: Collect Context (`context-collected`)

- validate `Skill(sanctum:git-workspace-review)` has been run.
- Use its notes to understand the delta.
- Identify the features or bug fixes that need documentation updates.

## Step 2: Identify Targets (`targets-identified`)

- List the relevant files from the scope across all documentation locations:
  - `docs/` - Reference documentation (strict style)
  - `book/` - Technical book content (lenient style)
  - `README.md` files at project and plugin roots
  - `wiki/` entries if present
  - Docstrings in code files
- Prioritize user-facing documentation first, then supporting plans and specifications.
- When architectural work is planned, confirm whether an Architecture Decision Record (ADR) already exists in `wiki/architecture/` (or wherever ADRs are located).
- Add missing ADRs to the target list before any implementation begins.

## Step 2.5: Check for Consolidation (`consolidation-checked`)

Load: `@modules/consolidation-integration.md`

**Purpose**: Detect redundancy and bloat before making edits.

**Scan for:**
- Untracked reports (ALL_CAPS *_REPORT.md, *_ANALYSIS.md files)
- Bloated committed docs (files exceeding 500 lines in docs/, 1000 in book/)
- Stale files (outdated content that should be deleted)

**User approval required before:**
- Merging content from one file to another
- Deleting stale or redundant files
- Splitting bloated files

**Skip options:**
- Use `--skip-consolidation` flag to bypass this phase
- Select specific items instead of processing all

**Exit criteria**: User has approved/skipped all consolidation opportunities.

## Step 3: Apply Edits (`edits-applied`)

- Update each file with grounded language: explain what changed and why.
- Reference specific commands, filenames, or configuration options where possible.
- For docstrings, use the imperative mood and keep them concise.
- For ADRs, see `modules/adr-patterns.md` for complete template structure, status flow, immutability rules, and best practices.

## Step 4: Enforce Guidelines (`guidelines-verified`)

Load: `@modules/directory-style-rules.md`

**Apply directory-specific rules:**

| Location | Style | Max Lines | Max Paragraph |
|----------|-------|-----------|---------------|
| docs/ | Strict reference | 500 | 4 sentences |
| book/ | Technical book | 1000 | 8 sentences |
| Other | Default to strict | 500 | 4 sentences |

**Common checks:**
- No filler phrases ("in order to", "it should be noted")
- No emojis in body text (callouts allowed in book/)
- Grounded language (specific references, not vague claims)
- Imperative mood for instructions
- Bullets over prose for lists of 3+ items

**Warn on:**
- Wall-of-text paragraphs exceeding limits
- Files exceeding line count thresholds
- Marketing language ("capable", "smooth")

## Step 5: Verify Accuracy (`accuracy-verified`)

Load: `@modules/accuracy-scanning.md`

**Validate claims against codebase:**

```bash
# Quick version check
for p in plugins/*/.claude-plugin/plugin.json; do
    jq -r '"\(.name): \(.version)"' "$p"
done

# Quick counts
echo "Plugins: $(ls -d plugins/*/.claude-plugin/plugin.json | wc -l)"
echo "Skills: $(find plugins/*/skills -name 'SKILL.md' | wc -l)"
```

**Flag mismatches:**
- Version numbers that don't match plugin.json
- Plugin/skill/command counts that don't match actual directories
- File paths that don't exist

**LSP-Enhanced Verification (2.0.74+)**:

When `ENABLE_LSP_TOOLS=1` is set, enhance accuracy verification with semantic analysis:

1. **API Documentation Coverage**:
   - Query LSP for all public functions/classes
   - Check which lack documentation
   - Verify all exported items are documented

2. **Signature Verification**:
   - Compare documented function signatures with actual code
   - Detect parameter mismatches
   - Flag return type discrepancies

3. **Reference Finding**:
   - Use LSP to find all usages of documented items
   - Include real usage examples in documentation
   - Verify cross-references are accurate

4. **Code Structure Validation**:
   - Check documented file paths exist (via LSP definitions)
   - Verify module organization matches documentation
   - Detect renamed/moved items

**Efficiency**: LSP queries (50ms) vs. manual file tracing (minutes) - dramatically faster verification.

**Default Strategy**: Documentation updates should **prefer LSP** for all verification tasks. Enable `ENABLE_LSP_TOOLS=1` permanently for best results.

**Non-blocking**: Warnings are informational; user decides whether to fix.

## Step 6: Preview Changes (`preview`)

- Show diffs for each edited file (`git diff <file>` or `rg` snippets).
- Include accuracy warnings if any were flagged.
- Summarize:
  - Files created/modified/deleted
  - Consolidation actions taken
  - Style violations fixed
  - Remaining TODOs or follow-ups

## Exit Criteria

- All `TodoWrite` items are completed and documentation is updated.
- New ADRs, if any, are in `wiki/architecture/` (or the established ADR directory) with the correct status and links to related work.
- Directory-specific style rules are satisfied.
- Accuracy warnings addressed or acknowledged.
- Content does not sound AI-generated.
- Files are staged or ready for review.

## Flags

| Flag | Effect |
|------|--------|
| `--skip-consolidation` | Skip Phase 2.5 consolidation check |
| `--strict` | Treat all warnings as errors |
| `--book-style` | Apply book/ rules to all files |
