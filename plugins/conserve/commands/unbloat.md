---
name: unbloat
description: Safe bloat remediation with user approval at each step
usage: /unbloat [--from-scan REPORT] [--auto-approve low] [--dry-run] [--focus code|docs|deps]
---

# Unbloat Command

<identification>
triggers: unbloat, remove bloat, cleanup codebase, reduce bloat

use_when:
- After bloat-scan identifies remediation targets
- Preparing for release
- Reducing codebase complexity
</identification>

Execute safe bloat remediation workflows with user approval at each step.

## Philosophy

- **Safety First**: Every change requires explicit approval (no auto-changes without review)
- **Progressive**: Start with high-confidence, low-risk changes first
- **Reversible**: Creates backup branches with clear rollback instructions

## Usage

```bash
# Integrated workflow: scan + remediate
/unbloat

# Use existing bloat-scan report
/unbloat --from-scan bloat-report.md

# Auto-approve low-risk changes (still shows preview)
/unbloat --auto-approve low

# Preview changes without executing
/unbloat --dry-run

# Focus on specific area
/unbloat --focus code
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--from-scan <file>` | Use existing bloat-scan report | Run new scan |
| `--auto-approve <level>` | Auto-approve: `low`, `medium`, `none` | `none` |
| `--dry-run` | Preview all changes without executing | `false` |
| `--focus <area>` | Focus: `code`, `docs`, `deps`, or `all` | `all` |
| `--backup-branch <name>` | Custom backup branch name | `backup/unbloat-{date}` |
| `--no-backup` | Skip backup branch creation | `false` |

## Workflow Overview

1. **Scan/Load**: Run integrated Tier 1 scan or load from `--from-scan` report
2. **Prioritize**: Group by type (DELETE, REFACTOR, CONSOLIDATE, ARCHIVE) and risk
3. **Backup**: Create timestamped backup branch
4. **Remediate**: Interactive approval for each finding with preview
5. **Verify**: Run tests after each change, rollback on failure
6. **Summary**: Report actions, token savings, rollback instructions

For remediation type definitions and risk assessment, see: `@module:remediation-types`

## Interactive Prompts

Each finding shows:
- File path, action type, confidence level
- Token impact estimate and rationale
- Content preview

Responses: `[y]es` / `[n]o` / `[d]iff` / `[s]kip rest` / `[q]uit`

## Example Session

```
$ /unbloat --auto-approve low

Phase 1: Scanning (Tier 1, quick scan)
[################] 847 files (4.2s)
Found 24 bloat items

Phase 2: Backup created: backup/unbloat-20251231-021500

Phase 3: Remediation

[1/10] src/deprecated/old_handler.py
  Action: DELETE | Confidence: 95% (LOW risk)
  Impact: ~3,200 tokens | Rationale: 0 refs, stale 22mo
  Auto-approved

[2/10] src/utils/helpers.py
  Action: REFACTOR | Confidence: 76% (MEDIUM risk)
  Impact: ~2,800 tokens
Approve? [y/n/d/s/q]: n
  Skipped

=== Summary ===
Applied: 7 | Skipped: 3
Token savings: ~18,400
Backup: backup/unbloat-20251231-021500
```

## Safety Features

1. **Always backup** (unless `--no-backup`)
2. **Git operations only** (`git rm`, not `rm` - reversible)
3. **Test after each change** - auto-rollback on failure
4. **Detailed logging** to `.unbloat-log`

## Rollback

```bash
# Undo entire unbloat session
git reset --hard backup/unbloat-YYYYMMDD-HHMMSS

# Restore specific file
git checkout backup/unbloat-YYYYMMDD-HHMMSS -- path/to/file
```

## Integration

```bash
# Two-step workflow (review findings first)
/bloat-scan --level 2 --report findings.md
/unbloat --from-scan findings.md

# With git workflows
git checkout -b cleanup/unbloat-Q1
/unbloat
/pr "Unbloat: Reduce codebase by 14%"
```

## See Also

- `/bloat-scan` - Detect bloat before remediation
- `unbloat-remediator` agent - Orchestration implementation
- `@module:remediation-types` - Type definitions and risk assessment
- `context-optimization` skill - Further optimization after unbloat
