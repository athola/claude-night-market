---
name: bloat-scan
description: |
  Run progressive bloat detection scan to identify dead code, duplication,
  and documentation bloat. Reduces context usage and technical debt.

  Triggers: bloat scan, dead code detection, codebase cleanup, detect bloat

  Use when: preparing for refactoring, high context usage, quarterly maintenance

  DO NOT use when: actively developing features, codebase < 1000 lines
usage: /bloat-scan [--level 1|2|3] [--focus code|docs|deps] [--report FILE] [--dry-run]
---

# Bloat Scan Command

Execute progressive bloat detection across code, documentation, and dependencies.

## Usage

```bash
# Quick scan (Tier 1, default)
/bloat-scan

# Targeted analysis (Tier 2)
/bloat-scan --level 2
/bloat-scan --level 2 --focus code
/bloat-scan --level 2 --focus docs

# Comprehensive audit (Tier 3)
/bloat-scan --level 3 --report audit-report.md

# Dry run (no changes)
/bloat-scan --dry-run
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--level <1|2|3>` | Scan tier: 1=quick, 2=targeted, 3=comprehensive | `1` |
| `--focus <type>` | Focus area: `code`, `docs`, `deps`, or `all` | `all` |
| `--report <file>` | Save report to file | stdout |
| `--dry-run` | Preview findings without taking action | false |
| `--exclude <pattern>` | Exclude paths matching pattern | `.bloat-ignore` |

## Scan Tiers

### Tier 1: Quick Scan (2-5 min)

**Detects:**
- Large files (> 500 lines)
- Stale files (unchanged 6+ months)
- Commented code blocks
- Old TODOs (> 3 months)
- Zero-reference files

**Requirements:** None (heuristics + git)

### Tier 2: Targeted Analysis (10-20 min)

**Detects:**
- Dead code (static analysis)
- Duplicate patterns
- Import bloat
- Documentation similarity
- Code churn hotspots

**Requirements:** Optional static analysis tools (Vulture, Knip)

### Tier 3: Comprehensive Audit (30-60 min)

**Detects:**
- All Tier 1 + Tier 2
- Cyclomatic complexity
- Dependency graphs
- Bundle size analysis
- Readability metrics

**Requirements:** Full tooling suite

## Workflow

1. **Invoke Command**
   ```
   /bloat-scan --level 2 --focus code
   ```

2. **Agent Executes Scan**
   - Dispatches `bloat-auditor` agent
   - Loads `bloat-detector` skill modules
   - Runs detection algorithms

3. **Generate Report**
   ```yaml
   === Bloat Detection Report ===

   Scan Level: 2
   Files Scanned: 847
   Findings: 24

   HIGH PRIORITY (5):
     - src/deprecated/old_api.py (95/100)
     - docs/archive/old-guide.md (88/100)
     ...

   MEDIUM PRIORITY (11):
     ...

   STATS:
     Estimated bloat: 14%
     Token savings: ~31,500
     Context reduction: ~12%
   ```

4. **Review & Approve Actions**
   - User reviews high-priority findings
   - Approves deletions/refactorings
   - Agent executes approved changes

## Output Format

### Terminal Output

```
🔍 Running Bloat Scan (Tier 1)...

[████████████████████] 847 files scanned (5.2s)

✅ Scan complete!

HIGH PRIORITY (Immediate Action):
  ❌ src/deprecated/old_handler.py
     Score: 95/100 | Confidence: HIGH
     Signals: Stale (22mo), Unused (0 refs), Large (847 lines)
     Impact: ~3,200 tokens
     Action: DELETE

MEDIUM PRIORITY (Review Soon):
  ⚠️  src/utils/helpers.py
     Score: 76/100 | Confidence: MEDIUM
     Signals: God class (634 lines), Low cohesion
     Impact: ~2,800 tokens
     Action: REFACTOR

SUMMARY:
  • Total findings: 24
  • High priority: 5
  • Token savings: ~31,500 (12% reduction)

NEXT STEPS:
  1. Review HIGH priority items (5 findings)
  2. Run: git checkout -b cleanup/bloat-reduction
  3. Process findings sequentially
```

### Report File (--report)

```markdown
# Bloat Detection Report

**Scan Date:** 2025-12-31
**Level:** 2 (Targeted Analysis)
**Duration:** 12m 34s
**Files Scanned:** 847

## Summary

- **Total Findings:** 24
- **High Priority:** 5
- **Medium Priority:** 11
- **Low Priority:** 8
- **Estimated Token Savings:** ~31,500 tokens
- **Context Reduction:** ~12%

## High Priority Findings

### [1] src/deprecated/old_handler.py

**Bloat Score:** 95/100
**Confidence:** HIGH (92%)

**Signals:**
- Stale: 22 months unchanged
- Unused: 0 references found
- Large: 847 lines
- Dead code: 100% (Vulture)

**Token Impact:** ~3,200 tokens

**Recommendation:** DELETE

**Rationale:** Multiple high-confidence signals confirm complete abandonment. No active usage detected.

**Action Plan:**
```bash
# Create backup
git checkout -b backup/old-handler
git add src/deprecated/old_handler.py
git commit -m "Backup before deletion"

# Delete on main branch
git checkout main
git rm src/deprecated/old_handler.py
git commit -m "Remove deprecated handler (bloat scan #1)"
```

[... more findings ...]

## Next Steps

1. ✅ Review all HIGH priority findings
2. ⏳ Create cleanup branch
3. ⏳ Process deletions (safest first)
4. ⏳ Run tests after each change
5. ⏳ Create PR with detailed rationale
```

## Integration

### With Context Optimization

```bash
# If context usage is high, bloat scan can help
/context-status  # Shows 45% utilization
/bloat-scan --level 2
# "Found 12% bloat, can reduce context to 33%"
```

### With Git Workflows

```bash
# Clean up before PR
/bloat-scan --dry-run
# Review findings
git checkout -b cleanup/pre-release
/bloat-scan --level 2
# Execute approved changes
/pr "Reduce codebase bloat by 14%"
```

### With Performance Monitoring

```bash
# Correlate bloat with performance
/bloat-scan --level 3
/performance-report
# Identify bloat causing slowdowns
```

## Safety

**CRITICAL: No automatic deletions**

- All changes require explicit user approval
- Dry-run mode by default (use `--execute` to apply)
- Creates backup branches before deletions
- Provides detailed diffs for review

## Examples

### Example 1: Quick Health Check

```bash
$ /bloat-scan

🔍 Running Bloat Scan (Tier 1)...
✅ Scan complete! Found 5 high-priority items.
   Estimated token savings: ~8,400 tokens
```

### Example 2: Focused Documentation Cleanup

```bash
$ /bloat-scan --level 2 --focus docs

🔍 Scanning documentation for bloat...
Found 3 duplicate docs (>85% similar)
Found 2 overly verbose guides (>5,000 words)
Estimated token savings: ~12,000 tokens
```

### Example 3: Comprehensive Pre-Release Audit

```bash
$ /bloat-scan --level 3 --report Q1-2025-audit.md

🔍 Running comprehensive bloat audit...
This will take 30-60 minutes. Continue? (y/n) y

[████████████████████] Deep analysis complete!

Report saved to: Q1-2025-audit.md
Found 24 bloat items across code, docs, and deps.
Estimated context reduction: 18%
```

## See Also

- `bloat-detector` skill - Detection modules and patterns
- `bloat-auditor` agent - Scan orchestration
- `context-optimization` skill - MECW principles
- `/context-status` - Current context utilization
