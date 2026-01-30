---
name: refine-code
description: Analyze and improve living code quality across 6 dimensions
usage: /refine-code [PATH] [--level 1|2|3] [--focus all|duplication|algorithms|clean-code|architecture] [--report FILE] [--apply]
---

# Refine Code Command

<identification>
triggers: refine code, improve quality, clean code, reduce slop, code refinement, refactor quality

use_when:
- After AI-assisted development to check for slop
- Before releases as a quality gate
- When code works but needs improvement
- Systematic refactoring of living code
- Reducing duplication and algorithmic inefficiency

do_not_use_when:
- Removing dead/unused code (use /unbloat)
- Bug hunting (use /bug-review)
- Selecting architecture paradigm (use archetypes)
</identification>

Analyze living code for quality issues and generate a prioritized refactoring plan.

## Philosophy

- **Craft over speed**: Counter AI velocity with intentional quality
- **Living code focus**: Improve code that stays, not remove code that's dead
- **Evidence-based**: Every finding has file:line references and principle citations
- **Actionable**: Concrete before/after proposals, not vague suggestions

## Usage

```bash
# Quick quality scan (Tier 1, default)
/refine-code

# Scan specific path
/refine-code src/

# Targeted analysis (Tier 2)
/refine-code --level 2
/refine-code --level 2 --focus duplication
/refine-code --level 2 --focus algorithms

# Deep analysis (Tier 3)
/refine-code --level 3 --report quality-report.md

# Apply refinements interactively
/refine-code --apply
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `PATH` | Directory or file to analyze | `.` |
| `--level <1\|2\|3>` | Analysis depth: 1=quick, 2=targeted, 3=deep | `1` |
| `--focus <area>` | Focus: `all`, `duplication`, `algorithms`, `clean-code`, `architecture` | `all` |
| `--report <file>` | Save report to file | stdout |
| `--apply` | Interactive remediation mode (preview + approve) | `false` |
| `--min-severity <level>` | Minimum severity to report: `high`, `medium`, `low` | `low` |

## Analysis Dimensions

| Dimension | What It Catches |
|-----------|----------------|
| **Duplication** | Near-identical blocks, similar functions, copy-paste patterns |
| **Algorithms** | O(n^2) where O(n) suffices, sort-in-loop, list-as-set |
| **Clean Code** | Long methods, deep nesting, magic values, poor naming |
| **Architecture** | Coupling violations, layer breaches, low cohesion |
| **Anti-Slop** | Premature abstraction, enterprise cosplay, hollow wrappers |
| **Error Handling** | Bare excepts, swallowed errors, happy-path-only |

## Scan Tiers

### Tier 1: Quick (2-5 min)
- Complexity hotspots (long methods, god classes)
- Obvious duplication (exact blocks)
- Naming issues (generic names)
- Magic numbers
- Bare excepts

### Tier 2: Targeted (10-20 min)
- Full duplication scan with structural similarity
- Algorithm inefficiency patterns
- Architectural coupling checks
- Anti-slop pattern detection
- Error handling completeness

### Tier 3: Deep (30-60 min)
- All Tier 1 + Tier 2
- Cross-module dependency analysis
- Paradigm fitness evaluation (if archetypes available)
- Comprehensive refactoring plan with before/after code
- Quality score with benchmarks

## Example Session

```
$ /refine-code src/ --level 2

Phase 1: Context
  Language: Python | Framework: FastAPI | Size: 2,847 lines (34 files)

Phase 2: Scanning (6 dimensions)
  [################] 34 files analyzed (8.3s)

Phase 3: Findings

[1/14] DUPLICATION | HIGH | SMALL effort
  src/handlers/user.py:45-62 <-> src/handlers/order.py:23-40
  18 duplicate lines (entity permission validation)
  Strategy: Extract to shared validate_permissions()

[2/14] ALGORITHM | HIGH | SMALL effort
  src/matching.py:45-58
  Nested loop on same collection: O(n^2)
  Strategy: Build dict index, reduce to O(n)

[3/14] ERROR HANDLING | HIGH | SMALL effort
  src/api.py:120-180
  60-line handler with zero error handling
  Strategy: Add try/except with proper error responses

[4/14] ANTI-SLOP | MEDIUM | SMALL effort
  src/factories/user_factory.py
  UserFactory has 1 implementation, 3 references
  Strategy: Inline factory, use direct construction

...

=== Quality Score: 62/100 ===
  Duplication:    55/100 (3 findings)
  Algorithms:     70/100 (1 finding)
  Clean Code:     65/100 (5 findings)
  Architecture:   60/100 (2 findings)
  Anti-Slop:      60/100 (2 findings)
  Error Handling:  55/100 (1 finding)

TOP 5 QUICK WINS (high impact, small effort):
  1. Extract duplicate validation (3 files, -54 lines)
  2. Index-based matching (-13 lines, 100x faster)
  3. Add API error handling (+20 lines, prevents crashes)
  4. Inline UserFactory (-45 lines, less indirection)
  5. Replace magic 86400 with SECONDS_PER_DAY

Next steps:
  /refine-code --apply                  # Apply interactively
  /refine-code --level 3 --report r.md  # Full deep analysis
  /cleanup                              # Combined with /unbloat
```

## Interactive Apply Mode

When `--apply` is used:

1. Creates backup branch: `backup/refine-YYYYMMDD-HHMMSS`
2. Shows each finding with proposed change
3. Prompts: `[y]es / [n]o / [d]iff / [s]kip rest / [q]uit`
4. Runs tests after each change
5. Rolls back on test failure
6. Reports summary with rollback instructions

## Plugin Dependencies

| Plugin | Status | Fallback |
|--------|--------|----------|
| `pensive` | **Required** | Core skill and agent |
| `imbue` | Optional | Evidence inline (no TodoWrite proof-of-work) |
| `conserve` | Optional | Built-in checks (no detect_duplicates.py, no KISS/YAGNI examples) |
| `archetypes` | Optional | Coupling/cohesion only (no paradigm-specific alignment) |

## Relationship to Other Commands

| Command | Focus | Scope |
|---------|-------|-------|
| `/refine-code` | Living code quality | Improve what exists |
| `/bloat-scan` + `/unbloat` | Dead/unused code | Remove what's unnecessary |
| `/ai-hygiene-audit` | AI-specific symptoms | Detect AI slop patterns |
| `/full-review` | Bug/security/API review | Find defects |
| `/cleanup` | All of the above | Unified orchestration |

## See Also

- `code-refinement` skill — Analysis dimensions and detection patterns
- `code-refiner` agent — Orchestration implementation
- `/cleanup` command — Unified cleanup orchestrator (conserve, if available)
- `conserve:code-quality-principles` — KISS/YAGNI/SOLID reference (if available)
- `archetypes:architecture-paradigms` — Paradigm detection (if available)
