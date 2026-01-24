# Plugin Dependency Pattern

This guide defines the standard pattern for managing dependencies between Claude Code plugins without using shared code modules.

## Philosophy

Plugins must remain self-contained and independent. Instead of sharing code through common modules, plugins implement their own logic for detecting and interacting with other plugins. This approach prevents version coupling and ensures that a single plugin's failure does not disable the entire ecosystem.

1.  **Detection**: Verify the existence of other plugins at runtime.
2.  **Capability Check**: Query plugin manifests for specific supported features.
3.  **Graceful Degradation**: Implement default behaviors when dependencies are missing.
4.  **Documentation**: Explicitly state optional relationships in READMEs and manifests.

## Core Pattern: Plugin Detection

### Step 1: Check for Plugin Installation

Plugins check the user's local configuration directory to determine if a dependency is present.

```python
def is_plugin_available(plugin_name: str) -> bool:
    """Check if a plugin is installed and available."""
    try:
        plugin_path = Path.home() / ".claude" / "plugins" / plugin_name
        if not plugin_path.exists():
            return False

        # Required markers for a valid plugin
        required_files = ["plugin.json", "SKILL.md"]
        return all((plugin_path / f).exists() for f in required_files)
    except Exception:
        return False
```

### Step 2: Check for Specific Functionality

Functional checks prevent errors when a plugin exists but is an incompatible version.

```python
def has_plugin_capability(plugin_name: str, capability: str) -> bool:
    """Check if a plugin provides a specific capability."""
    try:
        plugin_path = Path.home() / ".claude" / "plugins" / plugin_name

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

This pattern adds non-critical data or analysis when a secondary plugin is present. If `sanctum` is missing, the function returns the original data without git-specific enrichment.

```python
def enhance_with_sanctum_feature(data: dict) -> dict:
    """Enhance data using Sanctum plugin if available."""
    if not is_plugin_available("sanctum"):
        data["sanctum_enhanced"] = False
        return data

    try:
        from sanctum import git_operations
        if "commit_hash" in data:
            data["commit_details"] = git_operations.get_commit_details(data["commit_hash"])
            data["sanctum_enhanced"] = True
        else:
            data["sanctum_enhanced"] = False
    except ImportError as e:
        data["sanctum_enhanced"] = False
        data["sanctum_error"] = str(e)

    return data
```

### Pattern 2: Bidirectional Plugin Integration

When two plugins can benefit from each other's data, use a merging strategy. Each plugin remains responsible for its own primary analysis while optionally accepting data from the other.

```python
def analyze_with_abstract_and_sanctum(content: str) -> dict:
    """Analyze content using both Abstract and Sanctum if available."""
    results = {
        "abstract_analysis": analyze_content(content),
        "sanctum_context": None,
        "combined_insights": []
    }

    if is_plugin_available("sanctum"):
        try:
            from sanctum import workspace_analysis
            ws_context = workspace_analysis.get_workspace_context()
            results["sanctum_context"] = ws_context

            if results["abstract_analysis"] and ws_context:
                results["combined_insights"] = merge_analysis_with_context(
                    results["abstract_analysis"],
                    ws_context
                )
        except ImportError:
            pass

    return results
```

### Pattern 3: Service Provider Pattern

This pattern allows a central class to delegate tasks to specialized plugins. It defines a default built-in strategy that takes over if no preferred plugin is available.

```python
class ContextOptimizer:
    """Context optimization with plugin support."""

    def __init__(self):
        self.optimizers = {}
        self._load_optimizers()

    def _load_optimizers(self):
        """Load available context optimizers from plugins."""
        if is_plugin_available("conserve"):
            try:
                from conservation import context_optimizer as cons_opt
                self.optimizers["conserve"] = cons_opt
            except ImportError:
                pass
        self.optimizers["default"] = self._basic_optimize

    def optimize_context(self, content: str, strategy: str = "auto") -> str:
        """Optimize content using best available strategy."""
        if strategy == "auto":
            if "conserve" in self.optimizers:
                return self.optimizers["conserve"].optimize(content)
            return self._basic_optimize(content)

        return self.optimizers.get(strategy, self._basic_optimize)(content)

    def _basic_optimize(self, content: str) -> str:
        """Default built-in optimization using simple truncation."""
        if len(content) > 10000:
            return content[:5000] + "...\n[Content truncated]"
        return content
```

## Documentation Guidelines

### 1. Document Plugin Dependencies

In your plugin's `README.md`, distinguish between required and optional plugins.

```markdown
## Dependencies

### Optional

- **Sanctum Plugin**: Enables git repository context.
  - Features: commit details, branch analysis.
  - Secondary behavior: Analysis proceeds without git metadata.

- **Conservation Plugin**: Provides token optimization.
  - Features: Intelligent content summarization.
  - Default behavior: Uses standard character-based truncation.
```

### 2. Document Capabilities

In your `plugin.json`, use the `optional` array to declare integration points.

```json
{
  "name": "abstract",
  "version": "1.0.0",
  "provides": ["content-analysis", "skill-audit"],
  "optional": [
    {
      "plugin": "sanctum",
      "purpose": "git context enhancement",
      "default": "analysis without git data"
    }
  ]
}
```

## Best Practices

1.  **Always Provide Default Behaviors**: Never assume a plugin is installed. Every integration point must have a non-plugin default logic path.
2.  **Graceful Degradation**: Catch `ImportError` or `FileNotFoundError` when attempting to access other plugins. Return partial results with a clear status message instead of raising an unhandled exception.
3.  **Clear Communication**: Use return dictionaries or logs to indicate whether a result is "basic" or "enhanced." This helps developers debug why a specific feature might be missing.
4.  **Version Compatibility**: Use semantic version parsing if your plugin requires a specific feature set from a dependency.

## Testing Plugin Dependencies

Verify your integration logic by mocking the presence and absence of secondary plugins.

```python
def test_plugin_integrations():
    """Verify plugin behavior with and without dependencies."""
    # Test default behavior
    with mock_plugin_unavailable("sanctum"):
        result = enhance_with_sanctum_feature({"data": "test"})
        assert not result["sanctum_enhanced"]

    # Test enhanced behavior
    with mock_plugin_available("sanctum"):
        result = enhance_with_sanctum_feature({"data": "test", "commit_hash": "abc123"})
        assert result["sanctum_enhanced"]
        assert "commit_details" in result
```
