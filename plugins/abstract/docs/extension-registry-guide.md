# Extension Registry Guide

## Overview

The Extension Registry is a standalone component that allows Claude Code plugins to:

- Register domain-specific extensions (skills, commands, agents, hooks, etc.)
- Discover and reuse extensions from other plugins
- Handle versioning and compatibility
- Resolve conflicts between extensions

## Quick Start

### 1. Import the Registry

```python
from extension_registry import RegistryManager, ExtensionType

# Create a registry manager for your plugin
registry = RegistryManager(
    plugin_name="my-plugin",
    registry_path=Path("./registry"),  # Optional, defaults to shared location
    auto_create=True  # Create registry directory if it doesn't exist
)
```

### 2. Register Extensions

```python
# Register a skill extension
success, messages = registry.register_plugin_extension(
    name="data-processor",
    version="1.0.0",
    extension_type=ExtensionType.SKILL,
    title="Data Processing Skill",
    description="Process various data formats",
    entry_point="./skills/data_processor.py",
    keywords=["data", "processing", "etl"],
    dependencies=["format-parser@^2.0.0", "validator@>=1.5.0"]
)
```

### 3. Discover Extensions

```python
# Find all skill extensions
skills = registry.discover_extensions(extension_type=ExtensionType.SKILL)

# Find extensions by keywords
data_extensions = registry.discover_extensions(keywords=["data", "parsing"])

# Find specific extension with version constraint
parser = registry.find_extension_for_dependency("format-parser", "^2.0.0")
```

## Extension Types

The registry supports these extension types:

- `SKILL` - Skills that can be invoked by Claude
- `COMMAND` - Slash commands
- `AGENT` - Specialized agents
- `HOOK` - Claude Code hooks
- `PATTERN` - Reusable patterns
- `UTILITY` - Utility functions
- `WORKFLOW` - Complete workflows

## Dependencies

### Declaring Dependencies

```python
registry.register_plugin_extension(
    name="my-extension",
    version="1.0.0",
    extension_type=ExtensionType.SKILL,
    title="My Extension",
    description="An extension with dependencies",
    dependencies=[
        "required-dependency@^1.0.0",
        "optional-dependency@~2.0.0"  # Mark as optional in metadata
    ]
)
```

### Version Constraints

Supports semantic versioning constraints:

- `==1.0.0` - Exact version
- `>=1.0.0` - Minimum version
- `^1.0.0` - Compatible with same major version
- `~1.0.0` - Compatible with same minor version
- `1.*` - Wildcard for patch versions

## Conflict Resolution

When registering extensions that conflict, the registry can:

1. **Latest Wins** - Keep the most recently registered extension
2. **Oldest Wins** - Keep the first registered extension
3. **Higher Version** - Keep the extension with higher semantic version
4. **Rename New** - Rename the new extension to avoid conflict
5. **Reject New** - Reject the conflicting extension
6. **Merge** - Attempt to merge compatible extensions

### Example Conflict Handling

```python
# The registry automatically handles conflicts based on strategy
registry = RegistryManager(
    plugin_name="my-plugin",
    registry_path=Path("./registry"),
    conflict_strategy=ConflictStrategy.LATEST_WINS
)
```

## Storage Format

Extensions are stored as YAML files:

```yaml
name: "data-processor"
version: "1.0.0"
plugin_name: "my-plugin"
extension_type: "skill"
title: "Data Processing Skill"
description: "Process various data formats"
keywords: ["data", "processing", "etl"]
compatibility_level: "full"
dependencies:
  - name: "format-parser"
    version_constraint: "^2.0.0"
    optional: false
  - name: "validator"
    version_constraint: ">=1.5.0"
    optional: false
entry_point: "./skills/data_processor.py"
registered_at: "2024-01-01T12:00:00Z"
metadata: {}
```

## Advanced Usage

### Manifest Export/Import

```python
# Export all extensions from a plugin
manifest = registry.export_extension_manifest()

# Import extensions into another plugin
result = registry.import_extension_manifest(manifest, overwrite=False)
```

### Validation

```python
# Validate plugin extensions
validation = registry.validate_plugin_extensions()
if not validation['valid']:
    for issue in validation['issues']:
        print(f"Issue: {issue}")
```

### Registry Information

```python
# Get registry statistics
info = registry.get_registry_info()
print(f"Total extensions: {info['total_extensions']}")
print(f"By type: {info['by_type']}")

# Check dependencies
dep_report = registry.check_plugin_dependencies()
```

## Integration in Plugins

### Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── src/
│   └── extension-registry/  # Copy registry code here
├── skills/
├── commands/
└── hooks/
```

### Plugin Initialization

```python
# In your plugin's __init__.py or main module
from pathlib import Path
import sys

# Add local extension registry to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extension_registry import RegistryManager

# Initialize registry for this plugin
registry = RegistryManager(
    plugin_name="my-plugin",
    auto_create=True
)

# Register plugin's extensions
def register_extensions():
    registry.register_plugin_extension(
        name="my-skill",
        version="1.0.0",
        extension_type=ExtensionType.SKILL,
        title="My Plugin Skill",
        description="A skill from my plugin",
        entry_point="./skills/my_skill.py"
    )

# Call during plugin initialization
register_extensions()
```

## Best Practices

1. **Semantic Versioning**: Use proper semantic versioning for your extensions
2. **Clear Dependencies**: Declare all dependencies explicitly
3. **Descriptive Metadata**: Provide clear titles, descriptions, and keywords
4. **Compatibility Levels**: Choose appropriate compatibility levels
5. **Conflict Resolution**: Consider how your extensions should handle conflicts
6. **Regular Validation**: Validate extensions and dependencies regularly

## Troubleshooting

### Common Issues

1. **Registry Path Issues**: Ensure the registry path is writable
2. **Permission Errors**: Check file permissions for registry directory
3. **Version Conflicts**: Use explicit version constraints
4. **Circular Dependencies**: Avoid circular dependencies between extensions

### Debug Information

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check registry validation
valid, issues = registry.registry.validate_registry()
if not valid:
    print("Registry issues:", issues)
```