# Solving the Core Dependencies Issue for Marketplace Distribution

## Problem Statement

The `plugins/core/` directory contains shared utilities (especially the error handling framework) that several plugins depend on. When plugins are installed individually from the Claude Code marketplace, they won't have access to this shared directory, causing import errors.

## Current Dependencies

### Heavy Dependencies
- **conservation**: Imports `ErrorSeverity`, `PluginError` from `core.errors`
- **abstract**: Has commented imports with TODO markers

### Pattern of Problematic Imports
```python
# Current problematic approach
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent.parent / "core" / "src"
sys.path.insert(0, str(core_path))
from core.errors import ErrorSeverity, PluginError
```

## Recommended Solution: Progressive Migration Strategy

### Phase 1: Immediate Fix (Runtime Dependency Resolution)

Implement a 3-tier fallback system that works in all environments:

```python
# Try to import from claude-plugin-core package (marketplace distribution)
try:
    from claude_plugin_core.errors import ErrorSeverity, PluginError
except ImportError:
    # Development fallback - try to import from local core
    import sys
    from pathlib import Path
    core_path = Path(__file__).parent.parent.parent / "core" / "src"
    if core_path.exists():
        sys.path.insert(0, str(core_path))
        from core.errors import ErrorSeverity, PluginError
    else:
        # Final fallback - minimal implementations for standalone operation
        from enum import Enum

        class ErrorSeverity(Enum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
            CRITICAL = 4

        class PluginError(Exception):
            # Minimal implementation
            pass
```

### Phase 2: Extract and Publish Core Package

1. **Create `claude-plugin-core` PyPI package**
   - Extract `plugins/core/src/core/` to standalone package
   - Add setup.py/pyproject.toml for publishing
   - Version independently from plugins

2. **Update Plugin Dependencies**
   - Add to each plugin's `pyproject.toml`:
     ```toml
     [project]
     dependencies = [
         "claude-plugin-core >= 1.0.0"
     ]
     ```

3. **Standardize Imports**
   ```python
   # Standard import across all plugins
   from claude_plugin_core.errors import ErrorSeverity, PluginError
   ```

### Phase 3: Clean Migration

1. **Remove bundled fallbacks** once marketplace adoption is complete
2. **Deprecate local core** directory
3. **Standardize on package-based approach**

## Implementation Checklist

### For Each Plugin Using Core Dependencies

1. **Identify Core Dependencies**
   ```bash
   grep -r "from core\|import.*core\|plugins/core" plugins/<plugin-name>/
   ```

2. **Update Import Pattern**
   - Replace direct core imports with 3-tier fallback
   - Test all three import scenarios

3. **Add Package Dependency**
   - Update `pyproject.toml` with `claude-plugin-core` dependency
   - Pin to compatible version

4. **Test Marketplace Distribution**
   - Test plugin installation without core directory present
   - Verify functionality with only package dependency

### Core Extraction Tasks

1. **Extract Core Modules**
   - `plugins/core/src/core/errors.py` → `claude_plugin_core/errors.py`
   - Add necessary package infrastructure

2. **Package Setup**
   - Create repository for `claude-plugin-core`
   - Add CI/CD for publishing to PyPI
   - Document migration path

3. **Version Management**
   - Establish versioning strategy
   - Create compatibility matrix
   - Document breaking changes

## Benefits of This Approach

### Immediate Benefits
- **Backward Compatibility**: Existing installations continue working
- **Marketplace Ready**: Plugins work when installed individually
- **Graceful Degradation**: Standalone operation with minimal functionality

### Long-term Benefits
- **Standard Dependencies**: Normal Python package management
- **Version Control**: Clear compatibility between core and plugins
- **Independent Evolution**: Core can evolve without plugin updates
- **Reduced Maintenance**: No more path manipulation

## Migration Example

### Before (Problematic)
```python
# plugins/conservation/src/conservation/errors.py
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent.parent / "core" / "src"
sys.path.insert(0, str(core_path))
from core.errors import ErrorSeverity, PluginError
```

### After (Solution)
```python
# plugins/conservation/src/conservation/errors.py
try:
    from claude_plugin_core.errors import ErrorSeverity, PluginError
except ImportError:
    import sys
    from pathlib import Path
    core_path = Path(__file__).parent.parent.parent / "core" / "src"
    if core_path.exists():
        sys.path.insert(0, str(core_path))
        from core.errors import ErrorSeverity, PluginError
    else:
        from enum import Enum

        class ErrorSeverity(Enum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3
            CRITICAL = 4

        class PluginError(Exception):
            def __init__(self, error_code, message, **kwargs):
                super().__init__(message)
                self.error_code = error_code
```

## Testing Strategy

### Test All Three Scenarios
1. **Package Only**: Install plugin without core directory
2. **Local Core**: Development environment with core present
3. **Fallback**: Standalone with minimal implementations

### Validation Tests
```python
def test_core_dependencies():
    """Test that error classes work in all environments."""
    # Test import works
    from conservation.errors import ConservationError

    # Test functionality
    error = ConservationError(
        message="Test error",
        severity=ErrorSeverity.HIGH
    )

    assert error.error_code == "CONSERVATION_ERROR"
    assert error.severity == ErrorSeverity.HIGH
```

## Timeline

### Week 1: Immediate Fixes
- [ ] Update conservation plugin with fallback imports
- [ ] Fix any other plugins with direct core dependencies
- [ ] Test current plugins in isolation

### Week 2-3: Core Package
- [ ] Extract core to standalone package
- [ ] Setup PyPI publishing pipeline
- [ ] Version 1.0.0 release

### Week 4: Migration
- [ ] Update all plugins to use package dependency
- [ ] Document migration for plugin authors
- [ ] Test marketplace distribution

### Week 5-6: Cleanup
- [ ] Remove bundled fallbacks (optional)
- [ ] Deprecate local core usage
- [ ] Update documentation

## Conclusion

This progressive migration strategy ensures that:
1. **Existing users see no disruption**
2. **Marketplace distribution works immediately**
3. **Long-term maintainability improves**
4. **Plugin development becomes easier**

The 3-tier fallback system provides a smooth transition path while maintaining backward compatibility and enabling standalone plugin operation.
