---
name: bloat-detector
description: |
  Detect codebase bloat through progressive analysis: dead code, duplication, complexity, and documentation bloat.

  Triggers: bloat detection, dead code, code cleanup, duplication, redundancy, codebase health, technical debt, unused code

  Use when: preparing for refactoring, context usage is high, quarterly maintenance, pre-release cleanup

  DO NOT use when: actively developing new features, time-sensitive bug fixes.
  DO NOT use when: codebase is < 1000 lines (insufficient scale for bloat).

  Progressive 3-tier detection: quick scan → targeted analysis → deep audit.
category: conservation
tags: [bloat, cleanup, static-analysis, technical-debt, optimization]
dependencies: []
tools: [Bash, Grep, Glob, Read]
modules:
  - quick-scan
  - git-history-analysis
  - code-bloat-patterns
  - documentation-bloat
  - static-analysis-integration
progressive_loading: true
usage_patterns:
  - bloat-detection
  - codebase-cleanup
  - technical-debt-reduction
complexity: intermediate
estimated_tokens: 800
---

# Bloat Detector

## Overview

Systematically detect and eliminate codebase bloat through progressive analysis tiers. Reduces context consumption, improves navigability, and identifies technical debt hotspots.

**Bloat Categories:**
- **Code**: Dead code, God classes, Lava flow, duplication
- **Documentation**: Redundancy, excessive nesting, verbosity
- **Dependencies**: Unused imports, dependency bloat
- **Git History**: Stale files, low-churn code, orphaned branches

## Quick Start

### Tier 1: Quick Scan (5 minutes, no tools required)

```bash
# Heuristic-based detection
/bloat-scan
```

**Detects:**
- Files > 500 lines (God class candidates)
- Stale files (unchanged 6+ months)
- TODO/FIXME comments > 3 months old
- Commented code blocks
- Basic duplication patterns

**Output:** Prioritized quick wins with token savings estimates

### Tier 2: Targeted Analysis (15 minutes, optional tools)

```bash
# Focus on specific bloat types
/bloat-scan --level 2 --focus code
/bloat-scan --level 2 --focus docs
/bloat-scan --level 2 --focus deps
```

**Detects:**
- Static analysis (Vulture, deadcode, Knip if available)
- Git churn × complexity hotspots
- Documentation similarity (duplicate content)
- Import graph analysis

**Output:** Detailed findings with confidence levels, remediation steps

### Tier 3: Deep Audit (1 hour, full tooling)

```bash
# Deep analysis across all dimensions
/bloat-scan --level 3 --report audit-report.md
```

**Detects:**
- Full static analysis suite
- Cross-file redundancy
- Dependency graph visualization
- Readability metrics (Flesch-Kincaid)
- Bundle size analysis (JS/TS)

**Output:** Full audit report, refactoring roadmap, automated fixes

## When to Use

**Recommended Triggers:**
- ✅ Context usage > 30% regularly
- ✅ Quarterly maintenance cycles
- ✅ Pre-release cleanup
- ✅ Onboarding feedback: "hard to navigate"
- ✅ Before major refactoring

**Avoid Using:**
- ❌ During active feature development
- ❌ Time-sensitive bug fixes
- ❌ Codebases < 1000 lines
- ❌ When tools are unavailable (Tier 2/3)

## Detection Confidence Levels

| Level | Confidence | Action |
|-------|-----------|--------|
| **HIGH** (90-100%) | Multiple signals confirm | Safe to remove |
| **MEDIUM** (70-89%) | Single tool + heuristic | Review before action |
| **LOW** (50-69%) | Heuristic only | Manual investigation needed |
| **INVESTIGATE** | Edge case | Domain knowledge required |

## Prioritization Formula

```python
Priority Score = (
    (Token_Savings × 0.4) +
    (Maintenance_Impact × 0.3) +
    (Confidence_Level × 0.2) +
    (Fix_Ease × 0.1)
)
```

Output ranked by descending priority score.

## Module Architecture

### Tier 1: Quick Scan (Always Available)
- **quick-scan.md**: Heuristic-based detection, no external tools
- **git-history-analysis.md**: Staleness, churn metrics, reference counting

### Tier 2: Targeted Analysis (Optional Tools)
- **code-bloat-patterns.md**: God classes, Lava flow, anti-patterns
- **documentation-bloat.md**: Redundancy, readability, similarity
- **static-analysis-integration.md**: Tool integration (Vulture, Knip, etc.)

### Tier 3: Deep Audit (Full Tooling)
All above + deep cross-file analysis, dependency graphs, automated fixes

## Integration Points

- **Context Optimization**: Provides bloat metrics to MECW assessment
- **Performance Monitoring**: Correlates bloat with performance issues
- **Git Workflows** (sanctum): Integrates with PR review, cleanup branches
- **Memory Palace**: Stores bloat patterns as knowledge for future detection

## Example Output

```yaml
=== Bloat Detection Report ===

Scan Level: 1 (Quick Scan)
Duration: 2m 34s
Files Scanned: 847

HIGH PRIORITY (Immediate Action):
  ❌ plugins/old-plugin/legacy.py
     - 1,247 lines (God class)
     - Unchanged 18 months
     - No imports found (dead code)
     - Confidence: 95%
     - Token Savings: ~4,500 tokens
     - Action: DELETE or archive

  ❌ docs/archive/old-guide.md
     - 87% similar to docs/current-guide.md
     - Duplicate content detected
     - Confidence: 92%
     - Token Savings: ~2,100 tokens
     - Action: MERGE or remove

MEDIUM PRIORITY (Review Soon):
  ⚠️  src/core/manager.py
     - 634 lines, 15 methods
     - God class candidate
     - Confidence: 75%
     - Impact: High (core module)
     - Action: REFACTOR into smaller classes

  ⚠️  5 files with duplicate error handling
     - Pattern detected across modules
     - Confidence: 70%
     - Token Savings: ~1,200 tokens
     - Action: EXTRACT to shared utility

STATS:
  - Estimated bloat: 3,847 lines (14% of codebase)
  - Potential token savings: ~18,000 tokens
  - Context reduction: ~12%
  - High-confidence findings: 3
  - Medium-confidence findings: 6

NEXT STEPS:
  1. Review HIGH priority items (3 findings)
  2. Run Tier 2 scan for detailed analysis: /bloat-scan --level 2
  3. Create cleanup branch: git checkout -b cleanup/bloat-reduction
  4. Track progress with issue: /create-issue "Bloat reduction Q1 2025"
```

## Safety & Guardrails

**NEVER auto-delete without approval:**
- All deletions require explicit user confirmation
- Provide preview diffs before changes
- Support `--dry-run` flag for all operations
- Create backup branches before bulk changes

**Automatic Cache Directory Exclusion:**

All scan operations automatically exclude files and directories using a three-tier approach:

1. **Default Excludes** (always applied):
   ```text
   # Python
   .venv/, venv/, __pycache__/, .pytest_cache/, .mypy_cache/, .ruff_cache/, .tox/

   # JavaScript/Node
   node_modules/

   # Build artifacts
   dist/, build/, *.egg-info/

   # Version control
   .git/

   # Dependencies
   vendor/

   # IDE
   .vscode/, .idea/
   ```

2. **`.gitignore` Integration** (if present):
   - Automatically inherits patterns from your `.gitignore`
   - Respects project-specific exclusions
   - Prevents scanning generated files, build artifacts, etc.

3. **`.bloat-ignore`** (optional, bloat-specific overrides):
   - Additional patterns specific to bloat detection
   - Can override or extend `.gitignore` patterns
   - Useful for excluding test fixtures, templates, etc.

**Exclusion Priority**: Default → `.gitignore` → `.bloat-ignore`

**False Positive Mitigation:**
- Multi-signal validation (git + static + heuristic)
- Automatic exclusion of cache/dependency directories
- `.gitignore` pattern inheritance
- Optional `.bloat-ignore` file support
- Test file exemptions
- Generated code detection

## Detailed Resources

- **Quick Scan**: See `modules/quick-scan.md` for heuristic patterns
- **Git Analysis**: See `modules/git-history-analysis.md` for churn metrics
- **Code Patterns**: See `modules/code-bloat-patterns.md` for anti-patterns
- **Doc Bloat**: See `modules/documentation-bloat.md` for similarity detection
- **Static Analysis**: See `modules/static-analysis-integration.md` for tool setup

## Related Skills

- `context-optimization`: MECW principles, token reduction
- `performance-monitoring`: Resource usage correlation
- `resource-management`: Broader optimization strategies

## Related Agents

- `bloat-auditor`: Executes scans, generates reports, recommends actions
