---
name: cleanup
description: Unified codebase cleanup orchestrating bloat removal, code refinement, and hygiene auditing
usage: /cleanup [--focus all|bloat|quality|hygiene] [--level 1|2|3] [--report FILE] [--quick]
---

# Cleanup Command

Unified orchestrator that combines bloat removal, code quality refinement, and AI hygiene auditing into a single workflow.

## When To Use

Use this command when you need to:
- Comprehensive codebase maintenance
- Before major releases
- After extended AI-assisted development
- Regular hygiene cadence (weekly/sprint)
- Onboarding new team members to codebase state

## When NOT To Use

- Quick fixes that don't need structured workflow
- Already know the specific issue - fix it directly

## Philosophy

- **One command, full picture**: See all quality dimensions at once
- **Progressive**: Quick overview first, deep dive where needed
- **Graceful degradation**: Works with whatever plugins are installed
- **Non-destructive by default**: Report only unless explicitly asked

## Usage

```bash
# Full cleanup scan (all dimensions, Tier 1)
/cleanup

# Quick pass (fastest possible)
/cleanup --quick

# Focus on specific area
/cleanup --focus bloat       # /bloat-scan + /unbloat
/cleanup --focus quality     # /refine-code
/cleanup --focus hygiene     # /ai-hygiene-audit

# Deep analysis
/cleanup --level 3 --report cleanup-report.md

# Apply fixes interactively
/cleanup --apply
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--focus <area>` | Focus: `all`, `bloat`, `quality`, `hygiene` | `all` |
| `--level <1\|2\|3>` | Depth passed to sub-commands | `1` |
| `--report <file>` | Save consolidated report | stdout |
| `--quick` | Tier 1 scan of all dimensions, minimal output | `false` |
| `--apply` | Interactive remediation after scan | `false` |

## Orchestration Workflow

```
/cleanup
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

### Phase Execution

Phases 1-3 run their **scan** steps in parallel (independent analyses).
Phase 4 consolidates all findings.
Phase 5 remediates sequentially with user approval.

## Plugin Availability

| Plugin | Provides | Required? | Fallback |
|--------|----------|-----------|----------|
| `conserve` | `/bloat-scan`, `/unbloat`, `/ai-hygiene-audit` | **Yes** (this command lives here) | N/A |
| `pensive` | `/refine-code` | Optional | Phase 2 skipped; report notes "install pensive for code quality analysis" |
| `imbue` | Evidence logging | Optional | Evidence inline in report |
| `archetypes` | Paradigm detection | Optional | Architecture checks use coupling/cohesion only |

### Graceful Degradation

```python
def detect_available_phases():
    phases = {
        'bloat': True,           # Always available (conserve command)
        'hygiene': True,         # Always available (conserve command)
        'quality': plugin_installed('pensive'),  # Optional
    }

    unavailable = [k for k, v in phases.items() if not v]
    if unavailable:
        print(f"Note: {', '.join(unavailable)} phase(s) unavailable.")
        print("Install missing plugins for full coverage:")
        if not phases['quality']:
            print("  claude plugins install pensive  # Code quality refinement")

    return phases
```

## Example Session

```
$ /cleanup

=== Codebase Cleanup ===
Plugins: conserve (bloat, hygiene), pensive (quality), imbue (evidence)

Phase 1: Bloat Scan (Tier 1)
  [################] 847 files (4.2s)
  Found: 8 bloat items (~18,400 tokens recoverable)

Phase 2: Code Refinement (Tier 1)
  [################] 34 source files (5.1s)
  Found: 14 quality findings (3 HIGH, 7 MEDIUM, 4 LOW)

Phase 3: AI Hygiene Audit
  [################] Git + code analysis (3.8s)
  Hygiene score: 62/100

=== Consolidated Report ===

QUALITY SCORECARD:
  Bloat Health:     72/100  (8 items to clean)
  Code Quality:     62/100  (14 refinement opportunities)
  AI Hygiene:       62/100  (moderate concern)
  Overall:          65/100

TOP 10 ACTIONS (by impact):
  1. [BLOAT/HIGH] Delete 3 deprecated files (-3,200 tokens)
  2. [QUALITY/HIGH] Extract duplicate validation (3 files)
  3. [QUALITY/HIGH] Fix O(n^2) in matching.py
  4. [HYGIENE/HIGH] Add error tests for API handlers
  5. [BLOAT/HIGH] Remove 2 unused dependencies
  6. [QUALITY/MEDIUM] Inline premature UserFactory
  7. [HYGIENE/MEDIUM] Reduce doc hedge word density
  8. [QUALITY/MEDIUM] Replace magic numbers (4 files)
  9. [BLOAT/MEDIUM] Consolidate similar util modules
  10. [QUALITY/LOW] Improve generic function names

NEXT STEPS:
  /cleanup --apply              # Fix interactively
  /cleanup --level 2 --report   # Deeper analysis
  /refine-code --focus algorithms  # Drill into algorithms
  /unbloat --auto-approve low   # Quick bloat removal
```

## Consolidated Report Format (--report)

```markdown
# Codebase Cleanup Report

**Date:** YYYY-MM-DD
**Scope:** [path]
**Level:** [1|2|3]
**Plugins:** [list of installed plugins used]

## Quality Scorecard

| Dimension | Score | Findings | Recoverable |
|-----------|-------|----------|-------------|
| Bloat | 72/100 | 8 | ~18,400 tokens |
| Code Quality | 62/100 | 14 | N/A |
| AI Hygiene | 62/100 | 6 | N/A |
| **Overall** | **65/100** | **28** | |

## Findings by Priority

### Immediate (HIGH severity)
[findings...]

### Short-term (MEDIUM severity)
[findings...]

### Long-term (LOW severity)
[findings...]

## Unavailable Analyses

[List any skipped phases due to missing plugins, with install instructions]
```

## Integration

```bash
# Regular maintenance cadence
/cleanup --quick                    # Weekly quick check
/cleanup --level 2                  # Sprint end review
/cleanup --level 3 --report Q1.md  # Quarterly deep audit

# Pre-release workflow
/cleanup --level 2
/cleanup --apply                    # Fix what's found
/full-review                        # Then do a full code review
/pr "Release prep: cleanup + quality improvements"

# After AI sprint
/cleanup --focus quality --focus hygiene
```

## See Also

- `/bloat-scan` — Detect dead/unused code (conserve)
- `/unbloat` — Remove dead code with safety (conserve)
- `/ai-hygiene-audit` — AI-specific quality issues (conserve)
- `/refine-code` — Living code quality improvement (pensive, if available)
- `/full-review` — Comprehensive code review (pensive, if available)
