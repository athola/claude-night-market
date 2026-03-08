# Tiered Plugin Review Workflow

## Context

The night-market monorepo has 17 plugins with existing quality
skills (`skills-eval`, `hooks-eval`, `rules-eval`,
`test-review`, `unified-review`, `bloat-detector`,
`quality-gate`) but no unified orchestration that ties them
together with branch-awareness and dependency-aware scoping.

The `/plugin-review` command exists (abstract) with 7-dimension
scoring, and `/update-plugins` (sanctum) has a 4-phase audit.
Neither is tier-aware or dependency-aware.

## Design

### Command Interface

```bash
# Default: branch tier on affected + related plugins
/plugin-review

# Explicit tier
/plugin-review --tier branch
/plugin-review --tier pr
/plugin-review --tier release

# Specific plugin(s)
/plugin-review sanctum memory-palace --tier pr

# Show what would be reviewed without executing
/plugin-review --plan
```

Existing flags (`--focus`, `--format`, `--quality-gate`,
`--fail-on`) are preserved.

### Integration with /update-plugins

`/update-plugins` triggers `/plugin-review` as Phase 2:

```
/update-plugins
  Phase 1: Registration audit (existing)
  Phase 2: /plugin-review --tier branch (NEW)
  Phase 3: Meta-evaluation (existing)
  Phase 4: Knowledge queue (existing)
```

`/plugin-review` remains independently invocable.

### Tier Definitions

#### Branch (default)

Scope: affected plugins (from git diff) + related plugins
(from dependency map).

| Check | Affected | Related |
|-------|----------|---------|
| Registration audit | Full | Full |
| `make test` | Full | Full |
| `make lint` | Full | Skip |
| `make typecheck` | Full | Skip |
| Diff analysis (risk) | Full | Side-effect |

Target duration: under 2 minutes. Sequential execution.

#### PR

Scope: same plugin detection, deeper checks.

| Check | Affected | Related |
|-------|----------|---------|
| Everything in Branch | Full | Full |
| `abstract:skills-eval` | Full | Skip |
| `abstract:hooks-eval` | Changed hooks | Skip |
| `pensive:test-review` | Full | Skip |
| `conserve:bloat-scan` Tier 1 | Full | Skip |
| `abstract:rules-eval` | If rules changed | Skip |

Target duration: ~5 minutes. 2-3 parallel agents.

#### Release

Scope: all 17 plugins, full depth.

| Check | All Plugins |
|-------|-------------|
| Everything in PR | Full |
| `pensive:architecture-review` | Full |
| `pensive:unified-review` | Full |
| `conserve:bloat-scan` Tier 2-3 | Full |
| Token efficiency analysis | Full |
| Meta-evaluation (Phase 3) | Full |
| Cross-plugin dependency validation | Full |

Target duration: ~15 minutes. 5-6 parallel agents.
Requires plan mode (4+ agents rule).

### Plugin Scope Detection

1. **Affected plugins**: `git diff main --name-only` filtered
   to `plugins/*/` to extract plugin names.
2. **Related plugins**: look up changed plugins in
   `docs/plugin-dependencies.json` reverse index to find
   dependents that may experience side effects.
3. **Explicit override**: `--tier release` always scopes to
   all 17 plugins regardless of diff.

### Plugin Dependency Map

Static file at `docs/plugin-dependencies.json`:

```json
{
  "version": "1.0.0",
  "generated": "2026-03-08",
  "dependencies": {
    "abstract": {
      "dependents": ["*"],
      "type": "build",
      "reason": "Shared Make includes"
    },
    "leyline": {
      "dependents": ["conjure"],
      "type": "runtime",
      "reason": "QuotaTracker base class (optional)"
    }
  },
  "reverse_index": {
    "attune": ["abstract"],
    "conjure": ["abstract", "leyline"],
    "conserve": ["abstract"],
    "egregore": ["abstract"],
    "hookify": ["abstract"],
    "imbue": ["abstract"],
    "leyline": ["abstract"],
    "memory-palace": ["abstract"],
    "minister": ["abstract"],
    "parseltongue": ["abstract"],
    "pensive": ["abstract"],
    "sanctum": ["abstract"],
    "scribe": ["abstract"],
    "scry": ["abstract"],
    "spec-kit": ["abstract"],
    "archetypes": ["abstract"]
  }
}
```

Regenerated via `scripts/generate_dependency_map.py` which
scans Makefile includes, pyproject.toml deps, and Python
imports.

### Orchestration Flow

```
1. DETECT SCOPE
   - Parse --tier flag (default: branch)
   - If specific plugins given, use those
   - Else git diff to find affected plugins
   - Load plugin-dependencies.json for related plugins

2. PLAN
   - Build check matrix (tier x plugin x affected/related)
   - Estimate duration
   - If release tier, require plan mode (4+ agents)

3. EXECUTE
   - Branch: sequential, inline
   - PR: 2-3 parallel agents by plugin cluster
   - Release: 5-6 parallel agents per plan mode

4. REPORT
   - Per-plugin result table (pass/warn/fail)
   - Aggregate score
   - Top remediation actions
   - Verdict: PASS / PASS-WITH-WARNINGS / FAIL
```

### Verdict Mapping

| Verdict | Meaning | Action |
|---------|---------|--------|
| PASS | All checks green | Proceed |
| PASS-WITH-WARNINGS | Non-blocking issues | List warnings |
| FAIL | Blocking issues found | Fix before merge |

### Output Format

Branch tier produces a compact table:

```
Plugin Review (branch tier)
Affected: sanctum, memory-palace
Related:  abstract (build dep)

Plugin          test  lint  type  reg   verdict
sanctum         PASS  PASS  PASS  PASS  PASS
memory-palace   PASS  PASS  PASS  PASS  PASS
abstract        PASS  --    --    PASS  PASS

Verdict: PASS (3/3 plugins healthy)
```

PR and release tiers add scorecard sections with letter
grades and remediation priorities.

## Implementation Scope

| Asset | Plugin | Action |
|-------|--------|--------|
| `skills/plugin-review/SKILL.md` | abstract | Rewrite |
| `skills/plugin-review/modules/tier-branch.md` | abstract | New |
| `skills/plugin-review/modules/tier-pr.md` | abstract | New |
| `skills/plugin-review/modules/tier-release.md` | abstract | New |
| `skills/plugin-review/modules/dependency-detection.md` | abstract | New |
| `commands/plugin-review.md` | abstract | Update |
| `commands/update-plugins.md` | sanctum | Update |
| `scripts/generate_dependency_map.py` | root | New |
| `docs/plugin-dependencies.json` | root | New |

5 new files, 4 modified. No new plugins or commands.
