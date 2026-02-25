---
name: unbloat
description: Safe bloat remediation with user approval at each step
usage: /unbloat [--from-scan REPORT] [--auto-approve low] [--dry-run] [--focus code|docs|deps]
---

# Unbloat Command

Execute safe bloat remediation workflows with user approval at each step.

## When To Use

Use this command when you need to:
- After bloat-scan identifies remediation targets
- Preparing for release
- Reducing codebase complexity

## When NOT To Use

- Quick fixes that don't need structured workflow
- Already know the specific issue - fix it directly

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

## Unified Cleanup Mode

When invoked with `--cleanup` or as `/unbloat --cleanup`, this command orchestrates a full codebase cleanup (formerly the standalone `/cleanup` command), combining bloat removal, code quality refinement, and AI hygiene auditing.

### Cleanup Usage

```bash
# Full cleanup scan (all dimensions, Tier 1)
/unbloat --cleanup

# Quick pass (fastest possible)
/unbloat --cleanup --quick

# Focus on specific area
/unbloat --cleanup --focus bloat       # bloat-scan + unbloat
/unbloat --cleanup --focus quality     # refine-code
/unbloat --cleanup --focus hygiene     # ai-hygiene-audit

# Deep analysis with report
/unbloat --cleanup --level 3 --report cleanup-report.md

# Apply fixes interactively
/unbloat --cleanup --apply
```

### Cleanup Orchestration Workflow

```
/unbloat --cleanup
  |
  +-- Phase 1: Bloat Scan (/bloat-scan)
  |     Dead code, unused files, stale dependencies
  |
  +-- Phase 2: Code Refinement (/refine-code)  [if pensive installed]
  |     Duplication, algorithms, clean code, architecture
  |
  +-- Phase 3: AI Hygiene Audit (/ai-hygiene-audit)
  |     Git patterns, tab-completion bloat, test gaps, doc slop
  |
  +-- Phase 4: Consolidated Report
  |     Unified findings, quality score, prioritized actions
  |
  +-- Phase 5: Remediation (if --apply)
        Interactive approval for each finding
```

### Plugin Availability

| Plugin | Provides | Required? | Fallback |
|--------|----------|-----------|----------|
| `conserve` | `/bloat-scan`, `/unbloat`, `/ai-hygiene-audit` | **Yes** | N/A |
| `pensive` | `/refine-code` | Optional | Phase 2 skipped |
| `imbue` | Evidence logging | Optional | Evidence inline in report |

### Cleanup Options

| Option | Description | Default |
|--------|-------------|---------|
| `--cleanup` | Enable unified cleanup mode | `false` |
| `--focus <area>` | Focus: `all`, `bloat`, `quality`, `hygiene` | `all` |
| `--level <1\|2\|3>` | Depth passed to sub-commands | `1` |
| `--report <file>` | Save consolidated report | stdout |
| `--quick` | Tier 1 scan of all dimensions, minimal output | `false` |
| `--apply` | Interactive remediation after scan | `false` |

## See Also

- `/bloat-scan` - Detect bloat before remediation
- `unbloat-remediator` agent - Orchestration implementation
- `@module:remediation-types` - Type definitions and risk assessment
- `context-optimization` skill - Further optimization after unbloat
