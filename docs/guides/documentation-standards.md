# Documentation Standards

**Version**: 1.0
**Last Updated**: 2026-01-10
**Purpose**: Enforce conciseness and organization in project documentation

## Quick Reference

| Location | Max Lines | Style | Purpose |
|----------|-----------|-------|---------|
| `docs/` | 500 | Scannable reference | Quick-reference and scannable content |
| `book/` | 1000 | Step-by-step tutorial | Tutorials and explanations |
| Command files | 300 | Hub overview | High-level usage, links to modules |
| Modules | 600 | Focused detail | Specific aspect deep-dives |

## Core Principles

### 1. Progressive Disclosure

Start with an overview, then provide links to details:

```markdown
# Main File (150 lines)

Quick reference table with essentials

For details see:
- [Advanced Patterns](./modules/advanced-patterns.md)
- [Troubleshooting](./modules/troubleshooting.md)
```

### 2. Avoid Redundancy

**Do not duplicate content**:
- Reference detailed tutorials instead of duplicating code examples.
- Link to existing docs instead of repeating concepts.
- Extract common patterns to shared references.

**Good**: "See [error-handling-tutorial.md](../../book/src/tutorials/error-handling-tutorial.md) for examples"

**Bad**: Copy-pasting 300 lines of code examples already in tutorial.

### 3. Respect Directory Style

**docs/ = Strict 500-line limit**:
- Reference documentation
- Quick guides
- API references
- Pattern catalogs

**book/ = Lenient 1000-line limit**:
- Step-by-step tutorials
- Conceptual explanations
- Learning paths
- Case studies

## Debloating Techniques

### Technique 1: Table-of-Contents Pattern

Convert extensive guides to navigation hubs:

**Before** (748 lines):
```markdown
# Complete Hook Types Guide

## PreToolUse
[300 lines of detailed explanation]

## PostToolUse
[300 lines of detailed explanation]

## PermissionRequest
[148 lines of detailed explanation]
```

**After** (147 lines):
```markdown
# Hook Types Quick Reference

| Hook | Timing | Details |
|------|--------|---------|
| PreToolUse | Before tool | [Reference](hook-types/pre-tool-use.md) |
| PostToolUse | After tool | [Reference](hook-types/post-tool-use.md) |
| PermissionRequest | Permission dialog | [Reference](hook-types/permission-request.md) |

[Essential patterns and overview only]
```

**Savings**: 601 lines (~80% reduction)

### Technique 2: Consolidate Duplicates

Remove redundant examples that repeat concepts:

**Before**:
- Example 1: 50 lines showing error handling pattern
- Example 2: 50 lines showing same pattern different context
- Example 3: 50 lines showing same pattern third context

**After**:
- One canonical example: 30 lines
- Brief notes on variations: 10 lines

**Savings**: 110 lines (~73% reduction)

### Technique 3: Cross-Reference Tutorials

**Before** (docs/guides/error-handling-guide.md - 580 lines):
```markdown
## Error Classification

[100 lines of explanation + code]

## Retry Patterns

[100 lines of explanation + code]

## Circuit Breakers

[150 lines of explanation + code]

... more patterns with full implementations
```

**After** (316 lines):
```markdown
## Error Classification

Based on leyline:error-patterns standard:
- Critical: Halt execution
- Recoverable: Retry with backoff
- Warnings: Log and continue

See [tutorial](../../book/src/tutorials/error-handling-tutorial.md) for detailed examples.

## Plugin-Specific Patterns

Quick reference for each plugin (condensed)
```

**Savings**: 264 lines (~45% reduction)

### Technique 4: Delete Outdated Content

Review archive and plans directories:
- Historical implementation reports (preserved in git)
- Obsolete design documents (replaced by current implementation)
- Completed migration plans (no longer relevant)

**Phase 5 Example**: Deleted 2 outdated plan files (1,685 lines)

## Anti-Patterns to Avoid

### Anti-Pattern 1: "Complete Guide" in Modules

**Avoid**: `commands/foo/modules/complete-guide.md` (1,000 lines)
**Prefer**: `commands/foo.md` (200 lines) with focused modules

**Reason**: "Complete" guides defeat the purpose of modularity.

### Anti-Pattern 2: Verbose Examples

**Avoid**: Explaining library basics or general concepts
**Prefer**: Focused patterns, assuming basic knowledge

### Anti-Pattern 3: Redundant Code Examples

**Avoid**: Multiple examples showing the same pattern with minor variations
**Prefer**: One canonical example with notes on variations

### Anti-Pattern 4: Monolithic Files

**Avoid**: Single large files covering all aspects
**Prefer**: Hub files (150 lines) with focused modules (400 lines each)

## Enforcement

### Pre-Commit Checks

Warn on files exceeding limits:
```bash
# Check docs/ files
find docs/ -name '*.md' -exec wc -l {} \; | awk '$1 > 500 {print $1, $2}'

# Check book/ files
find book/ -name '*.md' -exec wc -l {} \; | awk '$1 > 1000 {print $1, $2}'
```

### Monthly Review

Run bloat scan to identify candidates:
```bash
/bloat-scan --level 2 --report bloat-monthly-YYYY-MM.md
```

### During PR Review

Check for:
- [ ] New docs/ files under 500 lines
- [ ] New book/ files under 1000 lines
- [ ] Progressive disclosure used for complex topics
- [ ] Cross-references instead of duplication
- [ ] No "complete-guide" files in modules/

## Migration Guide

### For Existing Large Files

1. **Assess structure**: Identify distinct sections
2. **Create hub file**: Overview + navigation (150-300 lines)
3. **Split into modules**: Each module focused on one aspect (400-600 lines)
4. **Update references**: Fix links in other files
5. **Verify**: Check all cross-references work

### Example Migration

**File**: `docs/examples/skill-development/authoring-best-practices.md` (652 lines)

**Step 1 - Assess**:
- Core principles (100 lines)
- Progressive disclosure patterns (150 lines)
- Workflows (100 lines)
- Common patterns (200 lines)
- Anti-patterns (102 lines)

**Step 2 - Trim**:
- Remove redundant examples
- Consolidate verbose explanations
- Reference external guides instead of duplicating

**Result**: 427 lines (225 saved, 34% reduction)

## Results from Phase 5

Applied these standards to 8 oversized files:

| File | Before | After | Saved | Method |
|------|--------|-------|-------|--------|
| hook-types-extensive.md | 748 | 147 | 601 | Table-of-contents |
| security-patterns.md | 904 | 534 | 370 | Consolidate duplicates |
| authoring-best-practices.md | 652 | 427 | 225 | Trim verbosity |
| evaluation-methodology.md | 653 | 377 | 276 | Extract implementations |
| error-handling-guide.md | 580 | 316 | 264 | Cross-reference tutorial |
| documentation-drive-plan.md | 887 | 0 | 887 | Delete outdated |
| plugin-superpowers-linking-implementation.md | 798 | 0 | 798 | Delete outdated |

**Total**: 5,222 lines -> 1,801 lines (3,421 saved, 65% reduction)

## Benefits

This documentation strategy reduces token usage, saving approximately 3,200 tokens from Phase 5 alone. The quick-reference pattern improves navigation speed for developers, while progressive disclosure maintains technical details without bloating the primary files. By separating quick-reference content from deep-dive tutorials, we organize the corpus more effectively.

## Related Patterns

- **Hub-and-Spoke Architecture**: Command structure pattern (Phase 2)
- **Modular Documentation**: Breaking large files into focused modules
- **Progressive Disclosure**: Start simple, provide links to complexity
- **Archive Management**: Moving historical content to git history

## See Also

- [Plugin Development Guide](../plugin-development-guide.md) - Overall structure
- [Writing Guidelines](https://docs.anthropic.com/en/docs/build-with-claude/skill-authoring) - Claude Developer Platform
