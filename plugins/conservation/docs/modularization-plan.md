# Conservation Plugin Modularization Plan

## Executive Summary

This plan addresses DRY violations and modularization opportunities identified through comprehensive skill evaluation. The conservation plugin should leverage abstract's token analysis infrastructure and extract reusable MECW patterns to leyline.

## Current State Analysis

### Plugin Validation Results
- **Status**: Valid plugin structure
- **Recommendation**: Add `claude` configuration object for enhanced metadata

### Skills Evaluation Summary

| Skill | Tokens | Status | Recommendation |
|-------|--------|--------|----------------|
| `context-optimization/SKILL.md` | 613 | ✅ Optimal | Hub pattern - exemplary |
| `mcp-code-execution/SKILL.md` | 1,528 | ✅ Good | Extract code to scripts |
| `optimizing-large-skills/SKILL.md` | 2,007 | ⚠️ Moderate | Consider modularization |
| `cpu-gpu-performance/SKILL.md` | 882 | ✅ Good | No changes needed |
| `token-conservation/SKILL.md` | 745 | ✅ Optimal | No changes needed |

### Hooks Evaluation
- **No hooks directory** - Conservation has no hooks, which is appropriate for a resource management plugin

### Module Quality Assessment

| Module Path | Lines | Quality |
|-------------|-------|---------|
| `context-optimization/modules/mecw-principles.md` | 102 | ✅ Excellent |
| `context-optimization/modules/mecw-assessment.md` | ~80 | ✅ Good |
| `context-optimization/modules/subagent-coordination.md` | ~90 | ✅ Good |
| `mcp-code-execution/modules/mcp-patterns.md` | 183 | ⚠️ Repetitive bash blocks |
| `mcp-code-execution/modules/mcp-subagents.md` | 253 | ⚠️ Heavy code |
| `mcp-code-execution/modules/mcp-validation.md` | ~100 | ✅ Good |

## DRY Violations Identified

### 1. Token Estimator Duplication (Priority: High)

**Location**: `skills/resource-management/token-estimator` (247 lines)

**Issue**: Duplicates functionality from `abstract/scripts/token_estimator.py`

**Analysis**:
- Conservation's token-estimator: Simple character-based heuristics
- Abstract's token_estimator: Uses `abstract.tokens.TokenAnalyzer` with sophisticated analysis

**Code Comparison**:
```python
# Conservation (simple)
CHARS_PER_TOKEN = 4
def count_tokens(text): return len(text) // CHARS_PER_TOKEN

# Abstract (sophisticated)
from abstract.tokens import TokenAnalyzer
analysis = TokenAnalyzer.analyze_content(content)
```

### 2. MECW Pattern Isolation (Priority: Medium)

**Location**: `context-optimization/modules/mecw-principles.md`

**Issue**: MECW patterns (50% rule, context pressure monitoring) are valuable but isolated to conservation. Other plugins could benefit.

**Opportunity**: Extract core MECW utilities to leyline for cross-plugin use.

### 3. Repetitive Code Blocks (Priority: Low)

**Location**: `mcp-code-execution/modules/mcp-patterns.md`

**Issue**: Same bash block repeated 8 times:
```bash
# Basic usage
python tools/extracted_tool.py --input data.json --output results.json
```

## Implementation Plan

### Phase 1: Remove Token Estimator Duplication (Priority: High)

**Task 1.1**: Update pyproject.toml to depend on abstract
```toml
[project.dependencies]
abstract = {path = "../abstract", develop = true}
```

**Task 1.2**: Refactor token-estimator to use abstract's TokenAnalyzer
```python
# New implementation
from abstract.tokens import TokenAnalyzer
from abstract.cli_framework import AbstractCLI

class ConservationTokenEstimator(AbstractCLI):
    def analyze_file(self, file_path):
        return TokenAnalyzer.analyze_content(file_path.read_text())
```

**Task 1.3**: Update Makefile targets to use abstract's token-estimator
```makefile
token-estimate:
    cd ../abstract && uv run python scripts/token_estimator.py $(ARGS)
```

**Expected Reduction**: ~200 lines removed

### Phase 2: Extract MECW Utilities to Leyline (Priority: Medium)

**Task 2.1**: Create `leyline/src/leyline/mecw.py`
```python
"""MECW (Maximum Effective Context Window) utilities."""

MECW_THRESHOLDS = {
    "LOW": 0.30,
    "MODERATE": 0.50,
    "HIGH": 0.70,
    "CRITICAL": 0.95
}

def calculate_context_pressure(current_tokens: int, max_tokens: int) -> str:
    """Determine context pressure level."""
    ratio = current_tokens / max_tokens
    if ratio < MECW_THRESHOLDS["LOW"]:
        return "LOW"
    elif ratio < MECW_THRESHOLDS["MODERATE"]:
        return "MODERATE"
    elif ratio < MECW_THRESHOLDS["HIGH"]:
        return "HIGH"
    return "CRITICAL"

def check_mecw_compliance(current_tokens: int, max_tokens: int = 200000) -> dict:
    """Check if context usage complies with MECW 50% rule."""
    threshold = max_tokens * 0.5
    compliant = current_tokens <= threshold
    return {
        "compliant": compliant,
        "current": current_tokens,
        "threshold": threshold,
        "overage": max(0, current_tokens - threshold),
        "action": "immediate_optimization_required" if not compliant else None
    }
```

**Task 2.2**: Update conservation modules to reference leyline
```yaml
# In mecw-principles.md frontmatter
dependencies:
  - leyline:mecw-utilities
```

**Task 2.3**: Update mcp-subagents.md code blocks to import from leyline

### Phase 3: Clean Up mcp-patterns.md (Priority: Low)

**Task 3.1**: Extract repeated bash blocks to a single reference
```markdown
## Tool Reference
All transformation patterns use the standard tool interface:
```bash
python tools/extracted_tool.py --input data.json --output results.json [--verbose]
```

See `tools/extracted_tool.py --help` for full options.
```

**Task 3.2**: Reduce module from 183 lines to ~100 lines

### Phase 4: Add Cross-Plugin Integration (Priority: Low)

**Task 4.1**: Document conservation → leyline dependency
```yaml
# In plugin.json
"dependencies": {
  "leyline": ">=1.0.0",
  "abstract": ">=1.0.0"
}
```

**Task 4.2**: Update README with integration documentation

## Migration Steps (Subagent Execution)

Execute using parallel subagents:

### Agent 1: Token Estimator Migration
```
Scope: conservation/skills/resource-management/token-estimator
       conservation/pyproject.toml
       conservation/Makefile
Tasks: 1.1, 1.2, 1.3
Est. Changes: 1 file deleted, 2 files modified
```

### Agent 2: MECW Extraction to Leyline
```
Scope: leyline/src/leyline/mecw.py (new)
       leyline/src/leyline/__init__.py
       conservation/skills/context-optimization/modules/*
Tasks: 2.1, 2.2, 2.3
Est. Changes: 2 files created, 3 files modified
```

### Agent 3: mcp-patterns Cleanup
```
Scope: conservation/skills/mcp-code-execution/modules/mcp-patterns.md
Tasks: 3.1, 3.2
Est. Changes: 1 file modified (significant reduction)
```

## Expected Outcomes

### Code Reduction
- Token estimator: 247 lines → 0 (use abstract)
- mcp-patterns.md: 183 lines → ~100 lines
- Total: ~330 lines removed

### New Shared Infrastructure
- `leyline/src/leyline/mecw.py`: ~50 lines (reusable by all plugins)

### Improved Architecture
- Single source of truth for token estimation (abstract)
- MECW utilities available to all plugins (leyline)
- Cleaner, more focused conservation skills

## Verification Checklist

After implementation:
- [ ] `uv run python ../abstract/scripts/validate-plugin.py .` passes
- [ ] `make test` passes (conservation tests)
- [ ] Token estimator CLI still works via abstract
- [ ] MECW imports resolve correctly from leyline
- [ ] No duplicate token estimation code remains
- [ ] mcp-patterns.md is under 120 lines

## Dependencies

This plan assumes:
1. leyline package has been set up (from conjure modularization)
2. abstract package exports `TokenAnalyzer` from `abstract.tokens`
3. Cross-plugin imports are supported via uv workspaces or relative paths
