# Conjure Plugin Modularization Plan

## Executive Summary

This plan addresses DRY violations and modularization opportunities identified through detailed skill evaluation. The conjure plugin should use leyline infrastructure instead of maintaining duplicate implementations.

## Current State Analysis

### Plugin Validation Results
- **Status**: Valid plugin structure
- **Recommendation**: Add `claude` configuration object for enhanced metadata

### Skills Evaluation Summary

| Skill | Tokens | Status | Recommendation |
|-------|--------|--------|----------------|
| `delegation-core/SKILL.md` | 3,085 | High | MODULARIZE (exceeds 3000 threshold) |
| `gemini-delegation/SKILL.md` | 782 | Optimal | No changes needed |
| `qwen-delegation/SKILL.md` | 948 | Good | No changes needed |

### Hooks Evaluation Summary

| Hook | Lines | Security | Performance |
|------|-------|----------|-------------|
| `bridge.on_tool_start` | 437 | Good path validation | Duplicate token estimation |
| `bridge.after_tool_use` | 124 | Clean | Lightweight |

### Critical DRY Violations

1. **Token Estimation Logic** - Duplicated in 4 files:
   - `conjure/scripts/quota_tracker.py` (lines 36-43, 284-298)
   - `conjure/scripts/delegation_executor.py` (lines 54-59, 218-256)
   - `conjure/hooks/gemini/bridge.on_tool_start` (via import)
   - `leyline/scripts/quota_tracker.py` (reference implementation)

2. **Quota Tracking** - Service-specific duplication:
   - `GeminiQuotaTracker` in conjure
   - `QuotaTracker` in leyline (service-agnostic)

3. **Usage Logging** - Similar implementations:
   - `GeminiUsageLogger` in conjure
   - `UsageLogger` in leyline (service-agnostic)

4. **Module Content Overlap** - Conjure modules duplicate leyline:
   - `conjure:delegation-core/modules/quota-management.md` (42 lines)
   - `leyline:quota-management/SKILL.md` (114 lines) + modules

## Implementation Plan

### Phase 1: Consolidate Token Estimation (Priority: High)

**Task 1.1**: Create shared token estimation utility in leyline
```
Location: plugins/leyline/src/leyline/tokens.py
Action: Consolidate FILE_TOKEN_RATIOS and estimation logic
```

**Task 1.2**: Update conjure scripts to import from leyline
```python
# Before
FILE_TOKEN_RATIOS = {...}  # Duplicated

# After
from leyline.tokens import estimate_tokens, FILE_TOKEN_RATIOS
```

**Task 1.3**: Update conjure hooks to use shared utilities

### Phase 2: Migrate Quota/Usage Infrastructure (Priority: High)

**Task 2.1**: Refactor GeminiQuotaTracker to extend leyline.QuotaTracker
```python
# New implementation
from leyline.quota_tracker import QuotaTracker, QuotaConfig

GEMINI_QUOTA_CONFIG = QuotaConfig(
    requests_per_minute=60,
    requests_per_day=1000,
    tokens_per_day=1000000
)

class GeminiQuotaTracker(QuotaTracker):
    def __init__(self):
        super().__init__(service="gemini", config=GEMINI_QUOTA_CONFIG)
```

**Task 2.2**: Refactor GeminiUsageLogger similarly

**Task 2.3**: Delete redundant code from conjure scripts

### Phase 3: Module Reference Cleanup (Priority: Medium)

**Task 3.1**: Update delegation-core modules to reference leyline
```yaml
# delegation-core/SKILL.md frontmatter
dependencies:
  - leyline:quota-management
  - leyline:usage-logging
  - leyline:service-registry
  - leyline:error-patterns
  - leyline:authentication-patterns

# Remove local modules/, use leyline references instead
references:
  - leyline/skills/quota-management/modules/threshold-strategies.md
  - leyline/skills/usage-logging/modules/session-patterns.md
```

**Task 3.2**: Delete conjure duplicate modules:
- `delegation-core/modules/quota-management.md` → Use leyline
- `delegation-core/modules/usage-logging.md` → Use leyline
- `delegation-core/modules/error-handling.md` → Use leyline
- `delegation-core/modules/authentication-patterns.md` → Use leyline

**Task 3.3**: Retain service-specific modules:
- Keep `gemini-delegation/modules/gemini-specifics.md`
- Keep `qwen-delegation/modules/qwen-specifics.md`
- Keep `delegation-core/shared-shell-execution.md` (conjure-specific)

### Phase 4: Reduce delegation-core Token Count (Priority: Medium)

**Current**: 3,085 tokens (exceeds 3000 threshold)
**Target**: <2,500 tokens

**Task 4.1**: Extract cost estimation section to module
```
New: delegation-core/modules/cost-estimation.md
Move: Lines 96-165 (Cost Estimation Guidelines)
Savings: ~400 tokens
```

**Task 4.2**: Extract troubleshooting to module
```
New: delegation-core/modules/troubleshooting.md
Move: Lines 291-327 (Troubleshooting)
Savings: ~200 tokens
```

**Task 4.3**: Compress leyline integration section
```
Current: 30 lines describing leyline usage
Target: 10 lines with link to leyline docs
Savings: ~150 tokens
```

### Phase 5: Hook Optimization (Priority: Low)

**Task 5.1**: Remove duplicate imports in hooks
```python
# Current: Local quota_tracker import with secondary logic
# New: Import from leyline with secondary logic
L155: # Use bundled version as secondary
```

**Task 5.2**: Share path validation utilities
```
Move: validate_path(), calculate_context_size() to leyline
```

## Migration Steps (Subagent Execution)

Execute using parallel subagents:

### Agent 1: Token Estimation Consolidation
```
Scope: leyline/src/leyline/tokens.py, conjure/scripts/*.py
Tasks: 1.1, 1.2, 1.3
Est. Changes: 4 files modified, 1 file created
```

### Agent 2: Quota/Usage Migration
```
Scope: conjure/scripts/quota_tracker.py, conjure/scripts/usage_logger.py
Tasks: 2.1, 2.2, 2.3
Est. Changes: 2 files heavily modified
```

### Agent 3: Module Reference Cleanup
```
Scope: conjure/skills/delegation-core/
Tasks: 3.1, 3.2, 3.3
Est. Changes: 1 file modified, 4 files deleted
```

### Agent 4: SKILL.md Token Reduction
```
Scope: conjure/skills/delegation-core/SKILL.md
Tasks: 4.1, 4.2, 4.3
Est. Changes: 1 file modified, 2 files created
```

## Expected Outcomes

### Token Reduction
- `delegation-core/SKILL.md`: 3,085 → ~2,400 tokens (-22%)
- Total conjure skills: 4,815 → ~4,100 tokens

### Code Reduction
- Duplicate Python code: ~600 lines removed
- Duplicate module content: ~170 lines removed

### Improved Maintenance
- Single source of truth for token estimation
- Unified quota/usage tracking across plugins
- Clear dependency hierarchy: conjure → leyline

## Verification Checklist

After implementation:
- [ ] `uv run python scripts/validate-plugin.py ../conjure/` passes
- [ ] `uv run python scripts/token_estimator.py --file ../conjure/skills/delegation-core/SKILL.md` shows <3000 tokens
- [ ] Hooks still function correctly (manual test)
- [ ] All leyline imports resolve correctly
- [ ] No duplicate FILE_TOKEN_RATIOS definitions remain
