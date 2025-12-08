# Function Extraction Guidelines

*Last Updated: 2025-12-06*

## Overview

This document provides standards and guidelines for function extraction and refactoring in the Claude Night Market plugin ecosystem. Following these guidelines ensures maintainable, testable, and readable code.

## Principles

### 1. Single Responsibility Principle (SRP)
A function should have only one reason to change.

### 2. Keep Functions Small
- Ideal: **10-20 lines** of code
- Acceptable: **20-30 lines** with clear logic
- Maximum: **50 lines** with strong justification
- **Never exceed 100 lines** without splitting

### 3. Limited Parameters
- Ideal: **0-3 parameters**
- Acceptable: **4-5 parameters** with clear types
- Consider object parameter if **6+ parameters**

### 4. Clear Naming
- Functions should be **verbs** that describe their action
- Use **consistent naming conventions** across the codebase
- Avoid abbreviations unless widely understood

---

## When to Extract Functions

### Immediate Extraction Required

1. **Function exceeds 30 lines**
   ```python
   # BAD - Too long
   def process_large_content(content):
       lines = content.split('\n')
       filtered_lines = []
       for line in lines:
           if line.strip():
               if not line.startswith('#'):
                   if len(line) < 100:
                       filtered_lines.append(line.strip())
       # ... 20 more lines
   ```

2. **Function has multiple responsibilities**
   ```python
   # BAD - Multiple responsibilities
   def analyze_and_optimize(content):
       # Analysis part
       complexity = calculate_complexity(content)
       quality = assess_quality(content)

       # Optimization part
       optimized = remove_redundancy(content)
       optimized = shorten_sentences(optimized)
       return optimized, complexity, quality
   ```

3. **Nested function depth exceeds 3 levels**
   ```python
   # BAD - Too nested
   def process_data(data):
       if data:
           for item in data:
               if item.valid:
                   for subitem in item.children:
                       if subitem.active:
                           # Deep nesting - extract this
                           process_subitem(subitem)
   ```

### Consider Extraction

1. **Function has 4+ parameters**
   ```python
   # CONSIDER - Many parameters
   def create_report(title, content, author, date, format, include_header, include_footer):
       pass

   # BETTER - Use configuration object
   @dataclass
   class ReportConfig:
       title: str
       content: str
       author: str
       date: datetime
       format: str = "pdf"
       include_header: bool = True
       include_footer: bool = True

   def create_report(config: ReportConfig):
       pass
   ```

2. **Complex conditional logic**
   ```python
   # CONSIDER - Complex conditions
   def calculate_rate(user, product, time, location, special_offer):
       if user.premium and product.category in ["electronics", "books"]:
           if time.hour < 12 and location.country == "US":
               if special_offer and not user.used_recently:
                   return 0.9
       # ... more conditions

   # BETTER - Extract condition checks
   def _is_eligible_for_discount(user, product, time, location, special_offer):
       return (user.premium and
               product.category in ["electronics", "books"] and
               time.hour < 12 and
               location.country == "US" and
               special_offer and
               not user.used_recently)
   ```

---

## Extraction Patterns

### 1. Extract Method Pattern

**Before:**
```python
def generate_report(data):
    # Validate data
    if not data:
        raise ValueError("Data cannot be empty")
    if not all(isinstance(item, dict) for item in data):
        raise TypeError("All items must be dictionaries")

    # Process data
    processed = []
    for item in data:
        processed_item = {
            'id': item.get('id'),
            'name': item.get('name', '').title(),
            'value': float(item.get('value', 0))
        }
        processed.append(processed_item)

    # Calculate totals
    total = sum(item['value'] for item in processed)
    average = total / len(processed) if processed else 0

    return {
        'items': processed,
        'summary': {
            'total': total,
            'average': average,
            'count': len(processed)
        }
    }
```

**After:**
```python
def generate_report(data):
    """Generate a report from data items."""
    _validate_data(data)
    processed_items = _process_data_items(data)
    summary = _calculate_summary(processed_items)

    return {
        'items': processed_items,
        'summary': summary
    }

def _validate_data(data):
    """Validate input data."""
    if not data:
        raise ValueError("Data cannot be empty")
    if not all(isinstance(item, dict) for item in data):
        raise TypeError("All items must be dictionaries")

def _process_data_items(data):
    """Process individual data items."""
    return [
        {
            'id': item.get('id'),
            'name': item.get('name', '').title(),
            'value': float(item.get('value', 0))
        }
        for item in data
    ]

def _calculate_summary(items):
    """Calculate summary statistics."""
    total = sum(item['value'] for item in items)
    return {
        'total': total,
        'average': total / len(items) if items else 0,
        'count': len(items)
    }
```

### 2. Strategy Pattern for Complex Logic

**Before:**
```python
def optimize_content(content, strategy_type):
    if strategy_type == "aggressive":
        # Remove all emphasis
        lines = content.split('\n')
        cleaned = []
        for line in lines:
            if not line.strip().startswith('**'):
                cleaned.append(line)
        return '\n'.join(cleaned)
    elif strategy_type == "moderate":
        # Shorten code blocks
        # ... 20 lines of logic
    elif strategy_type == "gentle":
        # Only remove images
        # ... 20 lines of logic
```

**After:**
```python
from abc import ABC, abstractmethod

class OptimizationStrategy(ABC):
    """Base class for content optimization strategies."""

    @abstractmethod
    def optimize(self, content: str) -> str:
        """Optimize content according to strategy."""
        pass

class AggressiveOptimizationStrategy(OptimizationStrategy):
    """Aggressive content optimization."""

    def optimize(self, content: str) -> str:
        lines = content.split('\n')
        cleaned = [
            line for line in lines
            if not line.strip().startswith('**')
        ]
        return '\n'.join(cleaned)

class ModerateOptimizationStrategy(OptimizationStrategy):
    """Moderate content optimization."""

    def optimize(self, content: str) -> str:
        # Implementation for moderate optimization
        pass

class GentleOptimizationStrategy(OptimizationStrategy):
    """Gentle content optimization."""

    def optimize(self, content: str) -> str:
        # Implementation for gentle optimization
        pass

# Strategy registry
OPTIMIZATION_STRATEGIES = {
    "aggressive": AggressiveOptimizationStrategy(),
    "moderate": ModerateOptimizationStrategy(),
    "gentle": GentleOptimizationStrategy()
}

def optimize_content(content: str, strategy_type: str) -> str:
    """Optimize content using specified strategy."""
    if strategy_type not in OPTIMIZATION_STRATEGIES:
        raise ValueError(f"Unknown strategy: {strategy_type}")

    strategy = OPTIMIZATION_STRATEGIES[strategy_type]
    return strategy.optimize(content)
```

### 3. Builder Pattern for Complex Construction

**Before:**
```python
def create_complex_object(name, type, config, options, metadata):
    obj = ComplexObject()
    obj.name = name
    obj.type = type

    # Complex configuration
    if config.get('enabled', True):
        obj.enabled = True
        obj.timeout = config.get('timeout', 30)
        obj.retries = config.get('retries', 3)

    # Options processing
    for key, value in options.items():
        if key.startswith('custom_'):
            obj.custom_fields[key[7:]] = value
        else:
            setattr(obj, key, value)

    # Metadata handling
    obj.created_at = metadata.get('created_at', datetime.now())
    obj.created_by = metadata.get('created_by', 'system')

    return obj
```

**After:**
```python
class ComplexObjectBuilder:
    """Builder for ComplexObject instances."""

    def __init__(self):
        self._object = ComplexObject()

    def with_name(self, name: str) -> 'ComplexObjectBuilder':
        self._object.name = name
        return self

    def with_type(self, obj_type: str) -> 'ComplexObjectBuilder':
        self._object.type = obj_type
        return self

    def with_config(self, config: Dict[str, Any]) -> 'ComplexObjectBuilder':
        self._object.enabled = config.get('enabled', True)
        self._object.timeout = config.get('timeout', 30)
        self._object.retries = config.get('retries', 3)
        return self

    def with_options(self, options: Dict[str, Any]) -> 'ComplexObjectBuilder':
        for key, value in options.items():
            if key.startswith('custom_'):
                self._object.custom_fields[key[7:]] = value
            else:
                setattr(self._object, key, value)
        return self

    def with_metadata(self, metadata: Dict[str, Any]) -> 'ComplexObjectBuilder':
        self._object.created_at = metadata.get('created_at', datetime.now())
        self._object.created_by = metadata.get('created_by', 'system')
        return self

    def build(self) -> ComplexObject:
        return self._object

# Usage
def create_complex_object(name, type, config, options, metadata):
    return (ComplexObjectBuilder()
            .with_name(name)
            .with_type(type)
            .with_config(config)
            .with_options(options)
            .with_metadata(metadata)
            .build())
```

---

## Testing Extracted Functions

### 1. Unit Test Each Extracted Function

```python
# Test for _validate_data
def test_validate_data_valid():
    data = [{'id': 1, 'name': 'test'}]
    # Should not raise
    _validate_data(data)

def test_validate_data_empty():
    with pytest.raises(ValueError, match="Data cannot be empty"):
        _validate_data([])

def test_validate_data_invalid_type():
    with pytest.raises(TypeError, match="All items must be dictionaries"):
        _validate_data([{'id': 1}, "invalid"])
```

### 2. Test Strategy Implementations

```python
def test_aggressive_optimization():
    content = "**Bold text**\nNormal text\n**More bold**"
    strategy = AggressiveOptimizationStrategy()
    result = strategy.optimize(content)
    assert "Normal text" in result
    assert "**" not in result
```

### 3. Integration Tests

```python
def test_generate_report_integration():
    data = [
        {'id': 1, 'name': 'test item', 'value': 100},
        {'id': 2, 'name': 'another item', 'value': 200}
    ]
    report = generate_report(data)

    assert report['summary']['total'] == 300
    assert report['summary']['average'] == 150
    assert len(report['items']) == 2
```

---

## Code Review Checklist

When reviewing code for function extraction:

### Function Size
- [ ] Function is under 30 lines
- [ ] If over 30 lines, there's a clear justification
- [ ] No function exceeds 100 lines

### Responsibilities
- [ ] Function has a single, clear purpose
- [ ] Function name describes its purpose accurately
- [ ] Function doesn't mix abstraction levels

### Parameters
- [ ] Function has 0-5 parameters
- [ ] Parameters are well-typed
- [ ] Related parameters are grouped into objects

### Complexity
- [ ] Cyclomatic complexity is under 10
- [ ] Nesting depth is under 4 levels
- [ ] No deeply nested ternary operators

### Testability
- [ ] Function can be tested independently
- [ ] Function has no hidden dependencies
- [ ] Side effects are clearly documented

### Documentation
- [ ] Function has a clear docstring
- [ ] Parameters are documented
- [ ] Return value is documented
- [ ] Exceptions are documented

---

## Refactoring Workflow

### 1. Identify Refactoring Candidates
```bash
# Find long functions
find . -name "*.py" -exec wc -l {} \; | sort -n | tail -20

# Find complex functions (manual code review)
# Look for functions with:
# - Multiple return statements
# - Deep nesting
# - Many parameters
# - Mixed responsibilities
```

### 2. Create Tests First
```python
# Write failing tests for the current behavior
def test_existing_behavior():
    # Test the function as it exists now
    pass
```

### 3. Extract Incrementally
1. Extract small, private helper functions
2. Run tests after each extraction
3. Gradually extract larger functions
4. Keep the public API stable

### 4. Optimize Imports and Dependencies
- Remove unused imports
- Group related imports
- Consider circular dependency issues

### 5. Update Documentation
- Update function docstrings
- Update API documentation
- Add examples for complex functions

---

## Tools and Automation

### 1. Complexity Analysis
```bash
# Using radon (complexity analyzer)
pip install radon
radon cc your_file.py -a

# Using flake8 with complexity plugin
pip install flake8-mccabe
flake8 --max-complexity 10 your_file.py
```

### 2. Automated Refactoring Tools
```bash
# Using rope (refactoring library)
pip install rope
rope refactor.py -e

# Using black for formatting (maintains consistency)
pip install black
black your_file.py
```

### 3. Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
      - id: flake8
        args: [--max-complexity=10, --max-line-length=100]

  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3
```

---

## Examples from the Codebase

### Before: GrowthController.generate_control_strategies()

The original function was 60+ lines and handled multiple responsibilities.

### After Refactoring:
```python
def generate_control_strategies(self, growth_rate: float) -> StrategyPlan:
    """Generate comprehensive control strategies for growth management."""
    strategies = self._select_control_strategies(growth_rate)
    monitoring = self._define_monitoring_needs(strategies)
    implementation = self._plan_implementation(strategies, monitoring)

    return StrategyPlan(strategies, monitoring, implementation)

def _select_control_strategies(self, growth_rate: float) -> List[Strategy]:
    """Select appropriate control strategies based on growth rate."""
    # Extracted strategy selection logic

def _define_monitoring_needs(self, strategies: List[Strategy]) -> MonitoringPlan:
    """Define monitoring requirements for selected strategies."""
    # Extracted monitoring logic

def _plan_implementation(self, strategies: List[Strategy],
                        monitoring: MonitoringPlan) -> ImplementationPlan:
    """Plan implementation steps for strategies and monitoring."""
    # Extracted implementation planning
```

This refactoring:
- Reduced main function to 5 lines
- Created three focused helper functions
- Made each function independently testable
- Improved readability and maintainability

---

## Conclusion

Following these function extraction guidelines will:

1. **Improve Maintainability**: Smaller, focused functions are easier to understand and modify
2. **Enhance Testability**: Each function can be tested in isolation
3. **Increase Reusability**: Extracted functions can be reused in different contexts
4. **Reduce Bugs**: Simpler functions have fewer edge cases and are easier to verify
5. **Improve Code Review**: Smaller functions are easier to review and understand

Remember: **The goal is not just to make functions smaller, but to make the code more readable, maintainable, and testable.**
