# Conservation Plugin Modularization Plan

## Status: Partially Complete

**Last Updated**: 2025-01-25
**Plan Created**: 2025-01-03

This document tracks the modularization work for the conservation plugin. Some items have been completed, others remain as future work.

## Completed Work

### ✅ Token Estimator Consolidation
- **Status**: DONE
- Token estimation now redirects to abstract plugin
- See `scripts/token-estimator.md` for usage instructions
- Conservation no longer maintains duplicate token counting code

### ✅ Skill Directory Reorganization
- **Status**: DONE
- Skills moved to flat structure under `skills/`
- Old nested paths (`resource-management/`, `performance-monitoring/`) removed
- Current structure:
  - `skills/token-conservation/`
  - `skills/cpu-gpu-performance/`
  - `skills/context-optimization/`
  - `skills/mcp-code-execution/`
  - `skills/bloat-detector/`
  - `skills/clear-context/`
  - And others...

### ✅ Plugin Metadata Updated
- **Status**: DONE
- `claude` configuration object added to plugin.json
- Skill paths updated to reflect new structure

## Remaining Work

### 🔲 MECW Pattern Extraction (Priority: Medium)

**Opportunity**: Extract core MECW utilities to leyline for cross-plugin use.

**Location**: `context-optimization/modules/mecw-principles.md`

**Rationale**: MECW patterns (50% rule, context pressure monitoring) are valuable but isolated to conservation. Other plugins could benefit from shared MECW utilities.

**Proposed Implementation**:
```python
# leyline/src/leyline/mecw.py
MECW_THRESHOLDS = {
    "LOW": 0.30,
    "MODERATE": 0.50,
    "HIGH": 0.70,
    "CRITICAL": 0.95
}

def calculate_context_pressure(current_tokens: int, max_tokens: int) -> str:
    """Determine context pressure level."""
    ratio = current_tokens / max_tokens
    for level, threshold in MECW_THRESHOLDS.items():
        if ratio < threshold:
            return level
    return "CRITICAL"
```

### 🔲 MCP Patterns Cleanup (Priority: Low)

**Location**: `mcp-code-execution/modules/mcp-patterns.md`

**Issue**: Repetitive bash blocks could be consolidated

**Target**: Reduce from ~183 lines to ~100 lines

## Current Skills Assessment

| Skill | Status | Notes |
|-------|--------|-------|
| `context-optimization` | ✅ Good | Hub pattern, well-modularized |
| `token-conservation` | ✅ Good | Optimal size |
| `cpu-gpu-performance` | ✅ Good | No changes needed |
| `mcp-code-execution` | ⚠️ Review | Could reduce code duplication |
| `bloat-detector` | ✅ Good | Well-modularized with 7 modules |
| `clear-context` | ✅ Good | Session state management |
| `optimizing-large-skills` | ⚠️ Review | Consider further modularization |

## Verification

Run these checks after any modularization work:
```bash
# Validate plugin structure
uv run python ../abstract/scripts/validate-plugin.py .

# Run tests
make test

# Check for stale references
grep -r "resource-management" . --include="*.md" --include="*.py" --include="*.json"
grep -r "performance-monitoring" . --include="*.md" --include="*.py" --include="*.json"
```

## Related Documents

- `README.md` - Plugin overview and usage
- `skills/bloat-detector/SKILL.md` - Bloat detection methodology
- `skills/context-optimization/SKILL.md` - MECW principles hub
