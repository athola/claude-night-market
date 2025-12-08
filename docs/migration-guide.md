# Technical Debt Migration Guide

*Last Updated: 2025-12-06*

## Overview

This guide helps plugin maintainers migrate their code to use the new shared constants and follow the function extraction guidelines.

## Quick Start

### 1. Update Your Plugin to Use Shared Constants

Replace scattered magic numbers with centralized constants:

```python
# BEFORE
def check_file_size(content):
    if len(content) > 15000:  # Magic number!
        return "File too large"
    if len(content) > 5000:   # Another magic number!
        return "File is large"

# AFTER
from plugins.shared.constants import MAX_SKILL_FILE_SIZE, LARGE_SIZE_LIMIT

def check_file_size(content):
    if len(content) > MAX_SKILL_FILE_SIZE:
        return "File too large"
    if len(content) > LARGE_SIZE_LIMIT:
        return "File is large"
```

### 2. Apply Function Extraction Guidelines

Use the patterns from the guidelines to refactor complex functions:

```python
# BEFORE - Complex function with multiple responsibilities
def analyze_and_optimize_skill(content, strategy):
    # Validation
    if not content:
        raise ValueError("Content cannot be empty")

    # Analysis
    tokens = estimate_tokens(content)
    complexity = calculate_complexity(content)

    # Optimization
    if strategy == "aggressive":
        # 20 lines of optimization logic
        pass
    elif strategy == "moderate":
        # 20 lines of optimization logic
        pass

    return optimized_content, tokens, complexity

# AFTER - Extracted and organized
def analyze_and_optimize_skill(content: str, strategy: str) -> OptimizationResult:
    """Analyze and optimize skill content."""
    _validate_content(content)

    analysis = _analyze_content(content)
    optimized = _optimize_content(content, strategy)

    return OptimizationResult(optimized, analysis)

def _validate_content(content: str) -> None:
    """Validate input content."""
    if not content:
        raise ValueError("Content cannot be empty")

def _analyze_content(content: str) -> ContentAnalysis:
    """Analyze content properties."""
    tokens = estimate_tokens(content)
    complexity = calculate_complexity(content)
    return ContentAnalysis(tokens, complexity)

def _optimize_content(content: str, strategy: str) -> str:
    """Optimize content using specified strategy."""
    optimizer = get_strategy_optimizer(strategy)
    return optimizer.optimize(content)
```

---

## Detailed Migration Steps

### Step 1: Audit Your Plugin

Find all magic numbers and complex functions:

```bash
# Find magic numbers (search for numeric literals in conditions)
grep -n -E "(if|when|while).*[0-9]+" your_plugin/**/*.py

# Find long functions
find your_plugin -name "*.py" -exec wc -l {} + | awk '$1 > 30 {print}'

# Find functions with many parameters
grep -n "def .*\(.*," your_plugin/**/*.py | grep -oE "\([^)]*\)" | grep -o "," | wc -l
```

### Step 2: Plan Your Migration

Create a migration plan for your plugin:

1. **Identify Constants**
   - List all magic numbers
   - Categorize by purpose (timeouts, sizes, thresholds)
   - Check if they exist in shared constants

2. **Identify Functions to Refactor**
   - Functions > 30 lines
   - Functions with > 4 parameters
   - Functions with multiple responsibilities

3. **Create Migration Tasks**
   - Update constants first (lowest risk)
   - Refactor simple functions next
   - Tackle complex functions last

### Step 3: Replace Magic Numbers

#### File Size Constants
```python
# Replace these patterns:
if len(content) > 15000:
if file_size > 100000:
if line_count > 200:

# With:
from plugins.shared.constants import (
    MAX_SKILL_FILE_SIZE,
    MAX_TOTAL_SKILL_SIZE,
    LARGE_FILE_LINES
)
```

#### Timeout Constants
```python
# Replace these patterns:
timeout=10
timeout=300
time.sleep(30)

# With:
from plugins.shared.constants import (
    DEFAULT_SERVICE_CHECK_TIMEOUT,
    DEFAULT_EXECUTION_TIMEOUT,
    MEDIUM_TIMEOUT
)
```

#### Quality Thresholds
```python
# Replace these patterns:
if quality_score > 70.0:
if quality_score > 80.0:
if quality_score > 90.0:

# With:
from plugins.shared.constants import (
    MINIMUM_QUALITY_THRESHOLD,
    HIGH_QUALITY_THRESHOLD,
    EXCELLENT_QUALITY_THRESHOLD
)
```

### Step 4: Refactor Complex Functions

Follow this iterative approach:

#### 4.1 Write Tests First
```python
# Test the current behavior
def test_function_to_refactor():
    result = your_complex_function(input_data)
    assert result.expected_field == expected_value
    # Add more assertions based on current behavior
```

#### 4.2 Extract Small Helper Functions
```python
# Start with small, obvious extractions
def _calculate_value(item):
    """Extract value calculation from complex function."""
    return item.base * item.multiplier + item.offset

def _validate_input(data):
    """Extract input validation."""
    if not data:
        raise ValueError("Data required")
    return True
```

#### 4.3 Extract Strategy Classes
For functions with conditional logic:

```python
# Before: Complex conditional function
def process_item(item, mode):
    if mode == "fast":
        # Fast processing logic
        pass
    elif mode == "thorough":
        # Thorough processing logic
        pass
    elif mode == "minimal":
        # Minimal processing logic
        pass

# After: Strategy pattern
class ItemProcessor(ABC):
    @abstractmethod
    def process(self, item):
        pass

class FastProcessor(ItemProcessor):
    def process(self, item):
        # Fast processing implementation
        pass

class ThoroughProcessor(ItemProcessor):
    def process(self, item):
        # Thorough processing implementation
        pass

# Registry
PROCESSORS = {
    "fast": FastProcessor(),
    "thorough": ThoroughProcessor(),
    "minimal": MinimalProcessor()
}

def process_item(item, mode):
    processor = PROCESSORS.get(mode)
    if not processor:
        raise ValueError(f"Unknown mode: {mode}")
    return processor.process(item)
```

### Step 5: Update Configuration

If your plugin has configuration files:

```yaml
# config.yaml - Use shared defaults
plugin_name: your_plugin

# Import shared defaults and override only what's needed
shared_constants:
  import: file_limits, timeouts, quality

# Plugin-specific settings
specific_settings:
  custom_threshold: 42
  feature_enabled: true
```

---

## Migration Checklist

### Pre-Migration
- [ ] Run existing tests to ensure baseline
- [ ] Create backup of current code
- [ ] Document current behavior
- [ ] Identify all dependencies

### Constants Migration
- [ ] List all magic numbers in your plugin
- [ ] Map to appropriate shared constants
- [ ] Update imports
- [ ] Replace magic numbers
- [ ] Run tests to verify no breaking changes

### Function Refactoring
- [ ] Identify functions > 30 lines
- [ ] Write tests for each function
- [ ] Extract small helper functions first
- [ ] Apply strategy pattern where appropriate
- [ ] Keep public APIs stable
- [ ] Update documentation

### Post-Migration
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Verify performance
- [ ] Update CHANGELOG
- [ ] Create migration notes for users

---

## Common Migration Patterns

### 1. Gradual Migration

Don't refactor everything at once. Use feature flags:

```python
# Gradually migrate to new implementation
def legacy_function(data):
    if USE_NEW_IMPLEMENTATION:
        return new_refactored_function(data)
    else:
        return old_implementation(data)

# Set this in config when ready
USE_NEW_IMPLEMENTATION = os.getenv("USE_NEW_IMPLEMENTATION", "false").lower() == "true"
```

### 2. Adapter Pattern

Keep old API while using new implementation:

```python
def old_api_function(param1, param2, param3):
    """Legacy API - delegates to new implementation."""
    config = LegacyConfig(param1, param2, param3)
    return new_refactored_function(config)

# New, cleaner API
def new_refactored_function(config: Config):
    """New, improved implementation."""
    pass
```

### 3. Parallel Implementation

Run both old and new implementations in parallel to verify:

```python
def process_with_validation(data):
    """Run both implementations and compare."""
    old_result = old_implementation(data)
    new_result = new_implementation(data)

    if not results_equivalent(old_result, new_result):
        log_discrepancy(old_result, new_result)
        # Return old result for safety
        return old_result

    return new_result
```

---

## Testing Your Migration

### 1. Property-Based Testing

Use hypothesis to test refactored functions:

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_refactor(data):
    """Test that refactored sort produces same result."""
    old_result = old_sort_function(data.copy())
    new_result = new_sort_function(data.copy())
    assert old_result == new_result
```

### 2. Integration Tests

Ensure the whole workflow still works:

```python
def test_complete_workflow():
    """Test that refactoring didn't break the workflow."""
    input_data = create_test_data()

    # Run through entire process
    result = your_plugin_workflow(input_data)

    # Verify key properties
    assert result is not None
    assert result.quality_score >= 70
    assert len(result.processed_data) > 0
```

### 3. Performance Tests

Ensure refactoring didn't hurt performance:

```python
import time

def test_performance():
    """Verify refactoring didn't degrade performance."""
    data = create_large_dataset()

    start = time.time()
    old_result = old_implementation(data)
    old_time = time.time() - start

    start = time.time()
    new_result = new_implementation(data)
    new_time = time.time() - start

    # New implementation shouldn't be more than 10% slower
    assert new_time < old_time * 1.1
```

---

## Rollback Plan

### If Migration Fails

1. **Immediate Rollback**
   ```bash
   git revert <migration-commit>
   ```

2. **Partial Rollback**
   - Keep constants migration
   - Revert function refactoring
   - Fix issues and retry

3. **Feature Flag Rollback**
   ```python
   # Disable new implementation
   os.environ["USE_NEW_IMPLEMENTATION"] = "false"
   ```

### Documenting Issues

If you encounter problems:

1. Document the specific issue
2. Note the affected functionality
3. Create a bug report with:
   - Migration step that failed
   - Error messages
   - Minimal reproduction case
   - Expected vs actual behavior

---

## Getting Help

### Resources
- [Function Extraction Guidelines](FUNCTION_EXTRACTION_GUIDELINES.md)
- [Technical Debt Backlog](../TECHNICAL_DEBT_BACKLOG.md)
- [Shared Constants Documentation](../plugins/shared/README.md)

### Support
- Create an issue for migration problems
- Join the #migration Slack channel
- Review example migrations in other plugins

### Contributing
- Share your migration experience
- Suggest improvements to guidelines
- Add new shared constants as needed

---

## Success Stories

### Memory Palace Plugin Migration

**Challenges:**
- 15 magic numbers scattered across files
- Functions averaging 45 lines
- Complex conditional logic

**Solution:**
- Replaced all magic numbers with shared constants
- Refactored 8 functions using extraction patterns
- Introduced strategy pattern for content processing

**Results:**
- 40% reduction in code complexity
- Improved test coverage from 60% to 85%
- Easier to add new content types

### Parseltongue Plugin Migration

**Challenges:**
- Complex analysis functions with 8+ parameters
- Duplicated logic across multiple analyzers
- Hard to test individual components

**Solution:**
- Extracted configuration objects for parameters
- Created shared analysis utilities
- Applied builder pattern for complex objects

**Results:**
- Functions reduced to average 15 lines
- Parameter count reduced to 3-4 per function
- 100% test coverage for core logic

---

## Conclusion

Migrating to shared constants and following function extraction guidelines significantly improves code quality. While it requires effort upfront, the long-term benefits in maintainability, testability, and developer productivity make it worthwhile.

Remember to:
- **Migrate incrementally** - don't try to do everything at once
- **Test thoroughly** - ensure behavior doesn't change
- **Document changes** - help others understand the migration
- **Ask for help** - leverage the community's experience

Good luck with your migration!