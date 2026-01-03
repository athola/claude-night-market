---
name: unbloat
description: |
  Safe bloat remediation: delete dead code, consolidate duplicates, refactor large files with user approval.

  Triggers: unbloat, remove bloat, cleanup codebase, reduce bloat
  Use when: after bloat-scan or preparing for release
usage: /unbloat [--from-scan REPORT] [--auto-approve low] [--dry-run] [--focus code|docs|deps]
---

# Unbloat Command

Execute safe bloat remediation workflows with user approval at each step.

## Philosophy

**Safety First**: Every deletion, refactoring, or merge requires explicit approval.
No automatic changes without review.

**Progressive Remediation**: Start with high-confidence, low-risk changes first.
Build confidence before tackling complex refactorings.

**Reversible Actions**: Create backup branches, detailed git history, and
provide rollback instructions.

## Usage

```bash
# Integrated workflow: scan + remediate
/unbloat

# Use existing bloat-scan report
/unbloat --from-scan bloat-report-2025-12-31.md

# Auto-approve low-risk changes (still shows preview)
/unbloat --auto-approve low

# Preview changes without executing
/unbloat --dry-run

# Focus on specific area
/unbloat --focus code
/unbloat --focus docs
/unbloat --focus deps
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--from-scan <file>` | Use existing bloat-scan report | Run new scan |
| `--auto-approve <level>` | Auto-approve: `low`, `medium`, `none` | `none` |
| `--dry-run` | Preview all changes without executing | `false` |
| `--focus <area>` | Focus: `code`, `docs`, `deps`, or `all` | `all` |
| `--backup-branch <name>` | Custom backup branch name | `backup/unbloat-{date}` |
| `--no-backup` | Skip backup branch creation | `false` (always backup) |

## Remediation Workflow

### Phase 1: Scan or Load Findings

```bash
# If --from-scan provided
if [ -f "$SCAN_REPORT" ]; then
  load_findings_from_report "$SCAN_REPORT"
else
  # Run integrated Tier 1 scan
  findings=$(run_bloat_scan --level 1 --focus "$FOCUS")
fi
```

### Phase 2: Prioritize and Group

Group findings by remediation type and risk level:

**Type Categories:**
- **DELETE**: Remove dead code, unused files
- **REFACTOR**: Split god classes, reduce complexity
- **CONSOLIDATE**: Merge duplicate docs, deduplicate code
- **ARCHIVE**: Move stale files to archive directory

**Risk Levels:**
- **LOW**: High-confidence dead code (0 refs, stale, 95%+ confidence)
- **MEDIUM**: Moderate confidence (1-2 refs, some usage signals)
- **HIGH**: Requires careful review (core files, dependencies)

### Phase 3: Create Backup Branch

```bash
# Always create backup before any changes
git checkout -b backup/unbloat-$(date +%Y%m%d-%H%M%S)
git add -A
git commit -m "Backup before unbloat operation"

# Return to working branch
git checkout -

# Save backup branch name for rollback instructions
BACKUP_BRANCH=$(git branch --list 'backup/unbloat-*' | tail -1)
```

### Phase 4: Execute Remediation (Interactive)

For each finding, in priority order:

```python
def remediate_finding(finding):
    """
    Interactive remediation with user approval
    """
    # 1. Show finding details
    display_finding_summary(finding)

    # 2. Show proposed action
    display_proposed_action(finding)

    # 3. Show preview (diff, content sample, impact)
    show_preview(finding)

    # 4. Request approval (unless auto-approved)
    if not auto_approved(finding):
        action = prompt_user(
            "Action? [y]es / [n]o / [d]iff / [s]kip rest / [q]uit: "
        )
    else:
        action = 'y'
        print("Auto-approved (low risk)")

    # 5. Execute based on response
    if action == 'y':
        execute_remediation(finding)
        record_action('APPLIED', finding)
    elif action == 'd':
        show_detailed_diff(finding)
        return remediate_finding(finding)  # Re-prompt
    elif action == 's':
        return 'SKIP_REST'
    elif action == 'q':
        return 'QUIT'
    else:
        record_action('SKIPPED', finding)

    return 'CONTINUE'
```

### Phase 5: Verification

After each change:

```bash
# Run tests if available
if [ -f "Makefile" ] && grep -q "^test:" Makefile; then
  make test --quiet
elif [ -f "package.json" ] && grep -q "\"test\"" package.json; then
  npm test --silent
elif [ -f "pytest.ini" ] || [ -f "tests/" ]; then
  pytest --quiet
fi

# Verify build still works
if [ -f "Makefile" ] && grep -q "^build:" Makefile; then
  make build --quiet
fi
```

### Phase 6: Summary Report

```yaml
=== Unbloat Summary ===

Started: 2025-12-31T02:15:00Z
Completed: 2025-12-31T02:47:00Z
Duration: 32m

ACTIONS TAKEN:
  Deleted: 5 files
  Refactored: 2 files
  Consolidated: 3 files
  Archived: 1 file
  Skipped: 13 findings

TOKEN SAVINGS:
  Estimated: ~31,500 tokens
  Realized: ~28,200 tokens (89% of estimate)

CONTEXT REDUCTION:
  Before: 45% utilization
  After: 33% utilization
  Reduction: 12 percentage points

FILES CHANGED:
  - src/deprecated/old_handler.py (DELETED)
  - src/legacy/stale_module.py (DELETED)
  - docs/archive/old-setup.md (CONSOLIDATED → docs/setup.md)
  - src/utils/helpers.py (REFACTORED → src/utils/{auth,validation,format}.py)

TESTS:
  Status: PASSED ✓
  Duration: 2m 14s

BACKUP:
  Branch: backup/unbloat-20251231-021500
  Restore: git checkout backup/unbloat-20251231-021500

NEXT STEPS:
  1. Review changes: git diff HEAD~11
  2. Commit changes: git add -A && git commit -m "Unbloat: reduce codebase by 14%"
  3. Run full test suite: make test
  4. If satisfied: git branch -D backup/unbloat-20251231-021500
  5. If issues: git reset --hard backup/unbloat-20251231-021500
```

## Remediation Types

### DELETE (Dead Code Removal)

**When Applied:**
- 0 references found (git grep, static analysis)
- Stale (> 6 months unchanged)
- High confidence (> 90%)
- Non-core file

**Example:**
```
Finding: src/deprecated/old_handler.py
Score: 95/100
Confidence: HIGH (92%)

Proposed Action: DELETE
Rationale: 0 references, stale 22mo, 100% dead (Vulture)

Preview:
  File size: 847 lines (~3,200 tokens)
  Last modified: 2023-02-15
  References: None found

Command: git rm src/deprecated/old_handler.py

Approve deletion? [y/n/d/s/q]: _
```

### REFACTOR (Split God Classes)

**When Applied:**
- Large file (> 500 lines)
- Low cohesion (multiple responsibilities)
- High cyclomatic complexity
- Active (recent changes)

**Example:**
```
Finding: src/utils/helpers.py
Score: 82/100
Confidence: MEDIUM (76%)

Proposed Action: REFACTOR (split into modules)
Rationale: 634 lines, 18 methods, 4 distinct responsibilities

Preview:
  Current: src/utils/helpers.py (634 lines)

  Proposed split:
    → src/utils/auth.py (147 lines, 4 methods)
    → src/utils/validation.py (212 lines, 7 methods)
    → src/utils/formatting.py (189 lines, 5 methods)
    → src/utils/misc.py (86 lines, 2 methods)

  Import updates required: 23 files

Approve refactoring? [y/n/d/s/q]: _
```

### CONSOLIDATE (Merge Duplicates)

**When Applied:**
- Duplicate content (> 85% similarity)
- Redundant documentation
- Multiple outdated versions

**Example:**
```
Finding: docs/archive/old-setup-guide.md
Score: 88/100
Confidence: HIGH (89%)

Proposed Action: CONSOLIDATE
Rationale: 91% similar to docs/setup.md, content superseded

Preview:
  Target: docs/archive/old-setup-guide.md (324 lines)
  Destination: docs/setup.md

  Similarity: 91% (295/324 lines match)

  Unique content (29 lines):
    - Legacy installation steps (lines 45-58)
    - Deprecated configuration (lines 102-116)

  Action:
    1. Review unique sections
    2. Preserve valuable content in setup.md
    3. Delete old-setup-guide.md

Approve consolidation? [y/n/d/s/q]: _
```

### ARCHIVE (Move to Archive)

**When Applied:**
- Historical value (can't delete)
- Stale but referenced
- Examples or tutorials

**Example:**
```
Finding: examples/legacy-tutorial.md
Score: 71/100
Confidence: MEDIUM (68%)

Proposed Action: ARCHIVE
Rationale: Outdated tutorial, historical value, few references

Preview:
  Source: examples/legacy-tutorial.md
  Destination: docs/archive/legacy-tutorial.md

  References: 2 found (README.md mentions it)

  Action:
    1. Move to docs/archive/
    2. Update README.md reference
    3. Add deprecation notice in file

Approve archiving? [y/n/d/s/q]: _
```

## Auto-Approval Levels

### `--auto-approve low`

Auto-approves findings that meet ALL criteria:
- Confidence ≥ 90%
- Risk = LOW
- 0 references (dead code only)
- File type: test files, deprecated/* directories, or docs/archive/*

**Still shows preview**, just skips manual approval prompt.

### `--auto-approve medium`

Auto-approves LOW + findings that meet:
- Confidence ≥ 80%
- Risk ≤ MEDIUM
- ≤ 2 references
- Non-core file

**Use with caution** - review summary before committing.

### `--auto-approve none` (default)

Prompts for every single change. Safest option.

## Safety Features

### 1. Always Create Backup

```bash
# Before any changes
git checkout -b backup/unbloat-$(date +%Y%m%d-%H%M%S)
git add -A
git commit -m "Backup before unbloat"
git checkout -
```

### 2. Reversible Actions

```bash
# Every deletion is a git operation
git rm <file>  # Not rm <file>

# Can be restored
git checkout HEAD -- <file>
```

### 3. Test After Each Change

```bash
# Verify nothing broke
make test --quiet

# If tests fail, immediately revert
git checkout HEAD -- <changed-files>
```

### 4. Detailed Logging

```bash
# Log every action to .unbloat-log
echo "$(date) | DELETE | src/old.py | Approved" >> .unbloat-log
echo "$(date) | REFACTOR | src/helpers.py | Skipped" >> .unbloat-log
```

### 5. Rollback Instructions

Always provide clear rollback steps:

```bash
# If anything goes wrong
git reset --hard <backup-branch>

# Or restore specific file
git checkout <backup-branch> -- path/to/file
```

## Integration

### With /bloat-scan

```bash
# Two-step workflow (recommended)
/bloat-scan --level 2 --report bloat-report.md
# Review report, plan approach
/unbloat --from-scan bloat-report.md

# Integrated workflow (faster)
/unbloat  # Runs Tier 1 scan internally
```

### With Conservation Skills

```bash
# Check context before/after
/context-status
/unbloat
/context-status  # See reduction

# Combine with other optimization
/unbloat --focus code
/optimize-context  # Further optimize remaining code
```

### With Git Workflows (Sanctum)

```bash
# Clean branch workflow
git checkout -b cleanup/unbloat-Q1-2025
/unbloat
make test
/pr "Unbloat: Reduce codebase by 14%, save 28k tokens"
```

## Examples

### Example 1: Safe Interactive Cleanup

```bash
$ /unbloat

🧹 Starting unbloat workflow...

Phase 1: Scanning for bloat (Tier 1, quick scan)
[████████████████████] 847 files scanned (4.2s)

✅ Found 24 bloat items

Phase 2: Creating backup branch
✅ Backup created: backup/unbloat-20251231-021500

Phase 3: Prioritizing findings
  - 5 HIGH confidence deletions
  - 3 MEDIUM confidence refactorings
  - 2 Documentation consolidations

Phase 4: Remediation (interactive)

[1/10] src/deprecated/old_handler.py
  Action: DELETE
  Confidence: 95% (HIGH)
  Impact: ~3,200 tokens
  Rationale: 0 refs, stale 22mo, 100% dead code

  Preview (first 10 lines):
    1  # This module is deprecated
    2  # TODO: Remove after migration complete
    3
    4  def old_handler(request):
    ...

Approve deletion? [y/n/d/s/q]: y

✅ Deleted src/deprecated/old_handler.py
   Running tests... ✅ PASSED

[2/10] docs/archive/old-setup.md
  Action: CONSOLIDATE
  Confidence: 89% (HIGH)
  Impact: ~2,400 tokens
  ...

Approve consolidation? [y/n/d/s/q]: y

✅ Consolidated into docs/setup.md
✅ Deleted docs/archive/old-setup.md

[3/10] src/utils/helpers.py
  Action: REFACTOR
  Confidence: 76% (MEDIUM)
  Impact: ~2,800 tokens
  ...

Approve refactoring? [y/n/d/s/q]: n
⏭️  Skipped

...

Phase 5: Summary

=== Unbloat Complete ===

Actions: 7 applied, 3 skipped
Token savings: ~18,400 tokens (65% of estimate)
Context reduction: 8 percentage points
Duration: 18m 32s

Backup: backup/unbloat-20251231-021500
Tests: PASSED ✓

Next steps:
  1. Review: git diff HEAD~7
  2. Commit: git add -A && git commit -m "Unbloat: 7 deletions/consolidations"
  3. Clean backup: git branch -D backup/unbloat-20251231-021500
```

### Example 2: Use Existing Scan Report

```bash
$ /bloat-scan --level 2 --report audit.md
# Review audit.md, identify priorities

$ /unbloat --from-scan audit.md --focus code
🧹 Loading findings from audit.md...
✅ Loaded 24 findings, filtering for code bloat...
📋 Processing 15 code-related findings

[1/15] src/deprecated/old_api.py
...
```

### Example 3: Low-Risk Auto-Approval

```bash
$ /unbloat --auto-approve low

🧹 Starting unbloat (auto-approve: low-risk only)...

Phase 4: Remediation

[1/10] src/deprecated/old_handler.py
  Action: DELETE
  Confidence: 95% (HIGH)
  Auto-approved ✓

✅ Deleted (3,200 tokens saved)

[2/10] src/utils/helpers.py
  Action: REFACTOR
  Confidence: 76% (MEDIUM)
  Requires manual approval

Approve refactoring? [y/n/d/s/q]: _
```

### Example 4: Dry Run Preview

```bash
$ /unbloat --dry-run

🧹 Unbloat Preview (DRY RUN - no changes will be made)

Phase 4: Remediation Preview

[1/10] src/deprecated/old_handler.py
  Action: DELETE
  Impact: ~3,200 tokens
  Status: WOULD DELETE ⚠️

[2/10] src/utils/helpers.py
  Action: REFACTOR
  Impact: ~2,800 tokens
  Status: WOULD REFACTOR ⚠️

...

Summary (DRY RUN):
  Would delete: 5 files
  Would refactor: 2 files
  Would consolidate: 3 files
  Total token savings: ~28,400 tokens

To execute: /unbloat (remove --dry-run flag)
```

## Error Handling

### Test Failures

```bash
# If tests fail after a change
❌ Tests failed after deleting src/old.py

Rolling back...
git checkout HEAD -- src/old.py

✅ Restored src/old.py
⚠️  Marked as SKIP, continuing with remaining findings
```

### Build Failures

```bash
# If build breaks
❌ Build failed after refactoring src/helpers.py

Rolling back refactoring...
git checkout HEAD -- src/helpers.py src/utils/

✅ Restored files
⚠️  Marked as SKIP
```

### User Abort

```bash
# User presses Ctrl+C or chooses 'q'
⚠️  Unbloat interrupted by user

Summary (partial):
  Completed: 3/10 findings
  Applied: 2 changes
  Skipped: 1 change
  Remaining: 7 findings

Backup: backup/unbloat-20251231-021500

To resume: /unbloat --from-scan .unbloat-progress.yaml
To rollback: git reset --hard backup/unbloat-20251231-021500
```

## Best Practices

### 1. Review Before Unbloat

```bash
# Run scan first, review findings
/bloat-scan --level 2 --report findings.md
# Review findings.md carefully
# Then execute remediation
/unbloat --from-scan findings.md
```

### 2. Start Conservative

```bash
# First time: low-risk only
/unbloat --auto-approve low

# Build confidence: expand to medium
/unbloat --auto-approve medium

# Expert mode: full interactive
/unbloat
```

### 3. Test Frequently

```bash
# After unbloat, run full test suite
/unbloat
make test  # Full suite, not just quick tests
make build
```

### 4. Commit Incrementally

```bash
# Don't commit all changes at once
git add src/deprecated/
git commit -m "Remove deprecated modules (unbloat 1/3)"

git add docs/archive/
git commit -m "Consolidate duplicate docs (unbloat 2/3)"

git add src/utils/
git commit -m "Refactor utils into focused modules (unbloat 3/3)"
```

## Troubleshooting

### "Tests fail after unbloat"

Check `.unbloat-log` to see what changed:
```bash
cat .unbloat-log | grep APPLIED
# Rollback specific change
git checkout HEAD -- path/to/problematic-file
```

### "Deleted file was actually needed"

Restore from backup:
```bash
git checkout backup/unbloat-YYYYMMDD-HHMMSS -- path/to/file
```

### "Want to undo entire unbloat"

```bash
# Find backup branch
git branch --list 'backup/unbloat-*'

# Reset to backup
git reset --hard backup/unbloat-YYYYMMDD-HHMMSS
```

## See Also

- `/bloat-scan` - Detect bloat before remediation
- `bloat-detector` skill - Detection patterns and algorithms
- `bloat-auditor` agent - Scan orchestration
- `context-optimization` skill - Further optimization after unbloat
- `/optimize-context` - Optimize remaining codebase
