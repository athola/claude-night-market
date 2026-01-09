# Remaining Issues from /fix-issue 93-95, 25-33

## Completed (7/12)

✅ **#25**: Architecture-paradigms → index/router (28.5% reduction)
✅ **#26**: Modularize optimizing-large-skills (38% reduction)
✅ **#30**: Complete JSON escaping in imbue hooks
✅ **#31**: Add logging to PyYAML warnings
✅ **#93**: Merge README-HOOKS.md into docs/guides
✅ **#94**: Consolidate conjure CHANGELOG
✅ **#95**: Rename /pr to /prepare-pr with expanded workflow

## Remaining (5/12)

### Priority 2: MECW Optimization

**#27 - Split Large Command Files (45 min estimated)**
- **Files**: bulletproof-skill.md (19.6KB), validate-hook.md (18.2KB), pr-review.md (35KB)
- **Strategy**: Each command → core dispatcher (<5KB) + modules directory
  ```
  commands/bulletproof-skill.md        # Core dispatcher
  commands/bulletproof-skill/
    modules/checklist.md
    modules/examples.md
  ```
- **Expected Impact**: ~40KB reduction across 3 files

**#28 - Consolidate Abstract Module Bloat (35 min estimated)**
- **Current State**:
  - hook-authoring/modules: 128K
  - skill-authoring/modules: 120K
  - skills-eval/modules: 144K
- **Strategy**: Archive larger examples to docs/examples/, replace with links
- **Expected Impact**: ~50-80KB reduction

**#29 - Optimize Oversized Agent Files (30 min estimated)**
- **Files**:
  - `testing-with-subagents.md` (569 lines) → Extract to standalone skill
  - `mcp-subagents.md` (252 lines) → Split into mcp-patterns.md, mcp-examples.md, mcp-troubleshooting.md
- **Expected Impact**: ~300-400 lines reduction

### Batch 4: Test Coverage Improvements

**#32 - Add Delegation Error Path Tests (25 min estimated)**
- **File**: `plugins/conjure/scripts/delegation_executor.py`
- **Missing Tests**:
  1. `smart_delegate()` when no services available (RuntimeError)
  2. Timeout handling verification
  3. Malformed JSON config graceful failure
- **Location**: `plugins/conjure/tests/test_delegation_executor.py`

**#33 - Add Wrapper Base Tests (20 min estimated)**
- **File**: `plugins/abstract/src/abstract/wrapper_base.py`
- **Missing Tests**:
  1. `validate_translation()` function tests
  2. `detect_breaking_changes()` with empty file list
- **Location**: `plugins/abstract/tests/test_wrapper_base.py`

## Recommendations

### For Immediate Completion
1. **#32 and #33** (Test coverage) - Quickest wins, ~45 minutes total
2. **#29** (Agent optimization) - Clear targets, ~30 minutes

### For Follow-up PR
3. **#27** (Large commands) - Requires careful analysis, deserves own PR
4. **#28** (Module consolidation) - Benefits from dedicated review

## Implementation Notes

### Issue #27 Pattern
```markdown
---
name: bulletproof-skill
description: Anti-rationalization workflow for skill hardening
modules:
  - checklist.md
  - examples.md
---

# Bulletproof Skill

[Core workflow and quick reference - <5KB]

## Workflow

[Essential steps only]

## Modules

- [Detailed Checklist](bulletproof-skill/modules/checklist.md)
- [Examples & Anti-Patterns](bulletproof-skill/modules/examples.md)
```

### Issue #28 Pattern
Move examples like:
- `skill-authoring/modules/testing-with-subagents.md` → `docs/examples/subagent-testing-guide.md`
- Replace module content with: `See [Subagent Testing Guide](../../../docs/examples/subagent-testing-guide.md)`

### Issue #29 Pattern
**testing-with-subagents.md (569 lines)**
```
plugins/abstract/skills/subagent-testing/
  SKILL.md                    # Core skill (~150 lines)
  modules/
    patterns.md               # Testing patterns (~200 lines)
    examples.md               # Real examples (~150 lines)
```

**mcp-subagents.md (252 lines)**
```
plugins/conserve/skills/mcp-code-execution/modules/
  mcp-patterns.md            # Core patterns (~80 lines)
  mcp-examples.md            # Usage examples (~100 lines)
  mcp-troubleshooting.md     # Debug guidance (~60 lines)
```

### Issue #32 Tests
```python
def test_smart_delegate_no_services_raises():
    """smart_delegate raises RuntimeError when no delegation services configured."""
    executor = DelegationExecutor(config={})
    with pytest.raises(RuntimeError, match="No delegation services"):
        executor.smart_delegate("test prompt")

def test_delegation_timeout_handling():
    """Delegation properly handles and reports timeout errors."""
    executor = DelegationExecutor(config={"timeout": 1})
    with pytest.raises(TimeoutError):
        executor.smart_delegate("long running task")

def test_malformed_config_graceful_failure():
    """Malformed JSON config produces actionable error."""
    with pytest.raises(ValueError, match="Invalid configuration"):
        DelegationExecutor(config="not a dict")
```

### Issue #33 Tests
```python
def test_validate_translation_valid():
    """validate_translation accepts valid translation structure."""
    translation = {"key": "value", "metadata": {}}
    result = validate_translation(translation)
    assert result is True

def test_validate_translation_invalid_structure():
    """validate_translation rejects invalid structure."""
    with pytest.raises(ValueError):
        validate_translation({"missing": "required_fields"})

def test_detect_breaking_changes_empty_list():
    """detect_breaking_changes handles empty file list gracefully."""
    result = detect_breaking_changes([])
    assert result == []  # or appropriate empty/no-change result
```

## Total Progress

- **Completed**: 7/12 issues (58%)
- **Token Savings**: ~4KB from MECW optimization
- **Remaining Effort**: ~2.5 hours estimated
- **Recommended Approach**: Complete tests (#32, #33) first, then MECW optimization in follow-up PR
