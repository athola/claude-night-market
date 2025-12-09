# Plugin Dependency Pattern

This document describes the proper pattern for handling dependencies between Claude Code plugins without using shared code modules.

## Philosophy

Plugins should be **self-contained** and **independent**. Instead of sharing code through common modules, plugins should:

1. **Detect** the presence of other plugins
2. **Use** functionality when available
3. **Fallback** gracefully when dependencies are missing
4. **Document** these relationships clearly

## Core Pattern: Plugin Detection

### Step 1: Check for Plugin Installation

```python
def is_plugin_available(plugin_name: str) -> bool:
    """Check if a plugin is installed and available"""
    try:
        # Check if plugin directory exists
        plugin_path = Path.home() / ".claude" / "plugins" / plugin_name
        if not plugin_path.exists():
            return False

        # Check if plugin has valid structure
        required_files = ["plugin.json", "SKILL.md"]
        return all((plugin_path / f).exists() for f in required_files)
    except Exception:
        return False
```

### Step 2: Check for Specific Functionality

```python
def has_plugin_capability(plugin_name: str, capability: str) -> bool:
    """Check if a plugin provides a specific capability"""
    try:
        plugin_path = Path.home() / ".claude" / "plugins" / plugin_name

        # Check plugin manifest for capabilities
        if (plugin_path / "plugin.json").exists():
            import json
            with open(plugin_path / "plugin.json") as f:
                manifest = json.load(f)
                return capability in manifest.get("provides", [])

        return False
    except Exception:
        return False
```

## Implementation Patterns

### Pattern 1: Optional Feature Enhancement

```python
def enhance_with_sanctum_feature(data: dict) -> dict:
    """Enhance data using Sanctum plugin if available"""
    # Check if Sanctum is available
    if not is_plugin_available("sanctum"):
        # Fallback behavior
        data["sanctum_enhanced"] = False
        return data

    # Try to use Sanctum functionality
    try:
        # Import and use Sanctum's functionality
        from sanctum import git_operations

        if "commit_hash" in data:
            data["commit_details"] = git_operations.get_commit_details(data["commit_hash"])
            data["sanctum_enhanced"] = True
        else:
            data["sanctum_enhanced"] = False

    except ImportError as e:
        # Sanctum exists but functionality not available
        data["sanctum_enhanced"] = False
        data["sanctum_error"] = str(e)

    return data
```

### Pattern 2: Bidirectional Plugin Integration

```python
def analyze_with_abstract_and_sanctum(content: str) -> dict:
    """Analyze content using both Abstract and Sanctum if available"""
    results = {
        "abstract_analysis": None,
        "sanctum_context": None,
        "combined_insights": []
    }

    # Always try Abstract analysis (this plugin)
    results["abstract_analysis"] = analyze_content(content)

    # Enhance with Sanctum if available
    if is_plugin_available("sanctum"):
        try:
            from sanctum import workspace_analysis

            # Get workspace context from Sanctum
            ws_context = workspace_analysis.get_workspace_context()
            results["sanctum_context"] = ws_context

            # Combine insights
            if results["abstract_analysis"] and ws_context:
                results["combined_insights"] = merge_analysis_with_context(
                    results["abstract_analysis"],
                    ws_context
                )

        except ImportError:
            pass  # Sanctum not fully functional

    return results
```

### Pattern 3: Service Provider Pattern

```python
class ContextOptimizer:
    """Context optimization with plugin support"""

    def __init__(self):
        self.optimizers = {}
        self._load_optimizers()

    def _load_optimizers(self):
        """Load available context optimizers from plugins"""
        # Try to load Conservation plugin optimizer
        if is_plugin_available("conservation"):
            try:
                from conservation import context_optimizer as cons_opt
                self.optimizers["conservation"] = cons_opt
            except ImportError:
                pass

        # Add built-in optimizer
        self.optimizers["built-in"] = self._basic_optimize

    def optimize_context(self, content: str, strategy: str = "auto") -> str:
        """Optimize content using best available strategy"""
        if strategy == "auto":
            # Prefer Conservation if available
            if "conservation" in self.optimizers:
                return self.optimizers["conservation"].optimize(content)
            else:
                return self._basic_optimize(content)

        elif strategy in self.optimizers:
            return self.optimizers[strategy].optimize(content)

        # Fallback to built-in
        return self._basic_optimize(content)

    def _basic_optimize(self, content: str) -> str:
        """Basic built-in optimization"""
        # Simple truncation or summarization
        if len(content) > 10000:
            return content[:5000] + "...\n[Content truncated]"
        return content
```

## Documentation Guidelines

### 1. Document Plugin Dependencies

In your plugin's `README.md`:

```markdown
## Plugin Dependencies

### Optional Dependencies

- **Sanctum Plugin** (optional): Enhances analysis with git context
  - Provides: commit details, branch information, workspace analysis
  - Fallback: Analysis continues without git context

- **Conservation Plugin** (optional): Optimizes context usage
  - Provides: intelligent content truncation, token optimization
  - Fallback: Uses built-in simple truncation
```

### 2. Document Capabilities

In your `plugin.json`:

```json
{
  "name": "abstract",
  "version": "1.0.0",
  "provides": [
    "content-analysis",
    "skill-complexity-analysis",
    "modularization-recommendations"
  ],
  "requires": [],
  "optional": [
    {
      "plugin": "sanctum",
      "purpose": "git context enhancement",
      "fallback": "analysis without git data"
    },
    {
      "plugin": "conservation",
      "purpose": "context optimization",
      "fallback": "built-in optimization"
    }
  ]
}
```

### 3. Document Integration Points

In your skill documentation:

```markdown
## Integration with Other Plugins

### Sanctum Integration
When the Sanctum plugin is available, this skill will:
1. Automatically detect git repository context
2. Enrich analysis with commit and branch information
3. Provide git-aware recommendations

Without Sanctum:
- Analysis proceeds normally
- Git-related insights are omitted

### Conservation Integration
When the Conservation plugin is available:
- Content is optimized for token efficiency
- Long contexts are intelligently summarized
- Priority is given to recent or important content

Without Conservation:
- Simple truncation is used for long content
- All content is treated equally
```

## Best Practices

### 1. Always Provide Fallbacks
Never make a plugin dependency required. Always have a fallback behavior.

```python
# Good
def process_data(data):
    if has_plugin_capability("superpowers", "enhanced-processing"):
        return superpower_enhanced_process(data)
    else:
        return basic_process(data)

# Bad
def process_data(data):
    from superpowers import enhanced_process  # Will fail if not installed
    return enhanced_process(data)
```

### 2. Graceful Degradation
When dependencies are missing, degrade gracefully rather than failing.

```python
# Good
try:
    enhanced = enhanced_feature(data)
    result = {
        "success": True,
        "data": enhanced,
        "enhanced": True
    }
except ImportError:
    result = {
        "success": True,
        "data": basic_feature(data),
        "enhanced": False,
        "message": "Enhanced features not available"
    }

# Bad
try:
    return enhanced_feature(data)
except ImportError:
    raise Exception("Required plugin not installed")
```

### 3. Clear Communication
Always communicate when features are enhanced or degraded.

```python
def analyze_skill(skill_path: Path) -> dict:
    result = {"skill": skill_path.name}

    # Basic analysis (always available)
    result["analysis"] = basic_skill_analysis(skill_path)

    # Abstract-specific enhancements
    if "abstract" in skill_path.parts:
        result["abstract_analysis"] = abstract_enhancements(skill_path)
        result["enhanced_by"] = "abstract"

    # Sanctum integration if available
    if is_plugin_available("sanctum"):
        try:
            git_context = get_git_context_for_file(skill_path)
            result["git_context"] = git_context
            result["enhanced_by"] = result.get("enhanced_by", "") + " + sanctum"
        except Exception:
            result["sanctum_error"] = "Git context unavailable"

    return result
```

### 4. Version Compatibility
Check for specific versions when required:

```python
def check_plugin_version(plugin_name: str, min_version: str) -> bool:
    """Check if plugin meets minimum version requirement"""
    try:
        plugin_path = Path.home() / ".claude" / "plugins" / plugin_name
        with open(plugin_path / "plugin.json") as f:
            manifest = json.load(f)
            return version.parse(manifest["version"]) >= version.parse(min_version)
    except Exception:
        return False
```

## Testing Plugin Dependencies

```python
def test_plugin_integrations():
    """Test all plugin integrations with mocks"""

    # Test without dependencies
    with mock_plugin_unavailable("sanctum"):
        result = enhance_with_sanctum_feature({"data": "test"})
        assert not result["sanctum_enhanced"]

    # Test with dependencies
    with mock_plugin_available("sanctum"):
        result = enhance_with_sanctum_feature({"data": "test", "commit_hash": "abc123"})
        assert result["sanctum_enhanced"]
        assert "commit_details" in result
```

This pattern ensures plugins remain independent while still providing enhanced functionality when used together in the same environment.