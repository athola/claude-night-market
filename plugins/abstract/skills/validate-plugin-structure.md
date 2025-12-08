---
name: validate-plugin-structure
description: Comprehensive checklist and reference guide for manually validating Claude Code plugin structure step-by-step. Use when you need the detailed validation checklist with implementation code samples, want to understand plugin.json schema requirements, or are building validation tooling. For quick automated validation, use /validate-plugin command instead.
triggers:
  - plugin validation checklist
  - plugin.json schema reference
  - plugin structure requirements
  - manual plugin audit
  - build validation tooling
---

# Plugin Structure Validation

This skill validates a Claude Code plugin's structure against the official documentation and best practices.

## When to Use This Skill

Use this skill when:
- Creating a new plugin to ensure proper structure
- Reviewing an existing plugin for compliance
- Preparing a plugin for distribution
- Debugging plugin loading issues
- Contributing plugins to a marketplace

## Validation Checklist

### 1. Required Structure Validation

**Critical Requirements:**
- [ ] `.claude-plugin/plugin.json` exists at correct location
- [ ] `plugin.json` contains required `name` field
- [ ] Plugin name follows kebab-case convention (lowercase, hyphens only)
- [ ] Component directories are at plugin root, not nested in `.claude-plugin/`

### 2. Directory Structure Validation

Check for standard directories (create if needed for extensibility):
- [ ] `skills/` directory (if plugin provides skills)
- [ ] `commands/` directory (if plugin provides slash commands)
- [ ] `agents/` directory (if plugin provides custom agents)
- [ ] `hooks/` directory (if plugin provides hooks)

**Note:** These directories are optional but should exist if referenced in `plugin.json`.

### 3. Plugin.json Schema Validation

**Required Fields:**
- [ ] `name` - kebab-case identifier (REQUIRED)

**Recommended Fields:**
- [ ] `version` - semantic versioning (e.g., "1.0.0")
- [ ] `description` - clear, concise description
- [ ] `author` - author name or object with name/email
- [ ] `license` - license identifier (e.g., "MIT")
- [ ] `keywords` - array of relevant keywords

**Optional Enhanced Fields:**
- [ ] `main` - entry point (e.g., "skills")
- [ ] `provides` - capabilities/patterns this plugin provides
- [ ] `dependencies` - plugin dependencies with versions
- [ ] `repository` - source code repository URL
- [ ] `homepage` - documentation or homepage URL
- [ ] `claude` - Claude-specific configuration object

### 4. Skills Validation

For each skill referenced in `plugin.json`:
- [ ] Skill file exists at specified path
- [ ] Skill file follows naming convention (either `skill-name.md` or `skill-name/SKILL.md`)
- [ ] Skill contains YAML frontmatter with `name` and `description`
- [ ] Skill uses progressive disclosure (sections that expand information)

### 5. Commands Validation

For each command:
- [ ] Command file is markdown format (`.md`)
- [ ] Command file contains YAML frontmatter with appropriate metadata
- [ ] Command paths use relative references with `./` prefix

### 6. Agents Validation

For each agent:
- [ ] Agent file is markdown format (`.md`)
- [ ] Agent file contains proper agent definition
- [ ] Agent paths use relative references with `./` prefix

### 7. Path Resolution Validation

- [ ] All paths in `plugin.json` are relative (start with `./`)
- [ ] Paths use `${CLAUDE_PLUGIN_ROOT}` for dynamic references where needed
- [ ] No absolute paths are used

### 8. Dependencies Validation

If plugin has dependencies:
- [ ] Dependencies use proper versioning (e.g., `">=2.0.0"`)
- [ ] Dependency plugins exist or are installable
- [ ] No circular dependencies

## Validation Implementation

### Step 1: Locate Plugin Root

```bash
# Get the plugin directory path
PLUGIN_DIR="$1"
if [ -z "$PLUGIN_DIR" ]; then
  echo "Usage: validate-plugin-structure <plugin-directory>"
  exit 1
fi

cd "$PLUGIN_DIR" || exit 1
```

### Step 2: Validate Critical Structure

```bash
# Check for .claude-plugin/plugin.json
if [ ! -f ".claude-plugin/plugin.json" ]; then
  echo "[CRITICAL] .claude-plugin/plugin.json not found"
  exit 1
fi

echo "[OK] .claude-plugin/plugin.json exists"
```

### Step 3: Validate plugin.json Content

```python
import json
import re
from pathlib import Path

def validate_plugin_json(plugin_path: Path) -> dict[str, list[str]]:
    """Validate plugin.json structure and return issues."""
    issues = {
        "critical": [],
        "warnings": [],
        "recommendations": []
    }

    json_path = plugin_path / ".claude-plugin" / "plugin.json"

    if not json_path.exists():
        issues["critical"].append("plugin.json not found at .claude-plugin/plugin.json")
        return issues

    with open(json_path) as f:
        config = json.load(f)

    # Validate required fields
    if "name" not in config:
        issues["critical"].append("Missing required field: name")
    elif not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', config["name"]):
        issues["critical"].append(f"Invalid plugin name: {config['name']} (must be kebab-case)")

    # Check recommended fields
    recommended = ["version", "description", "author", "license"]
    for field in recommended:
        if field not in config:
            issues["recommendations"].append(f"Missing recommended field: {field}")

    # Validate paths
    for key in ["skills", "commands", "agents"]:
        if key in config and isinstance(config[key], list):
            for path in config[key]:
                if not path.startswith("./"):
                    issues["warnings"].append(f"{key} path should start with './': {path}")

                # Check if referenced file exists
                check_path = plugin_path / path.lstrip("./")
                if not check_path.exists() and not (plugin_path / f"{path.lstrip('./')}.md").exists():
                    issues["critical"].append(f"Referenced {key} path not found: {path}")

    # Validate dependencies format
    if "dependencies" in config:
        if isinstance(config["dependencies"], list):
            issues["recommendations"].append("Dependencies should be object with versions, not array")
        elif isinstance(config["dependencies"], dict):
            for dep, version in config["dependencies"].items():
                if not isinstance(version, str) or not re.match(r'^[><=\^~]*\d+\.\d+\.\d+', version):
                    issues["warnings"].append(f"Dependency {dep} should use semantic versioning")

    return issues
```

### Step 4: Validate Directory Structure

```python
def validate_directory_structure(plugin_path: Path) -> dict[str, list[str]]:
    """Validate plugin directory structure."""
    issues = {
        "warnings": [],
        "recommendations": []
    }

    # Check for standard directories
    standard_dirs = ["skills", "commands", "agents", "hooks"]

    with open(plugin_path / ".claude-plugin" / "plugin.json") as f:
        config = json.load(f)

    # If plugin references components, directories should exist
    if "skills" in config and config["skills"]:
        if not (plugin_path / "skills").exists():
            issues["warnings"].append("Plugin references skills but skills/ directory missing")

    if "commands" in config and config["commands"]:
        if not (plugin_path / "commands").exists():
            issues["warnings"].append("Plugin references commands but commands/ directory missing")

    if "agents" in config and config.get("agents"):
        if not (plugin_path / "agents").exists():
            issues["warnings"].append("Plugin references agents but agents/ directory missing")

    return issues
```

### Step 5: Generate Validation Report

```python
def generate_report(plugin_path: Path) -> None:
    """Generate comprehensive validation report."""
    print(f"Validating plugin: {plugin_path.name}")
    print("=" * 60)

    # Validate plugin.json
    json_issues = validate_plugin_json(plugin_path)

    # Validate directory structure
    dir_issues = validate_directory_structure(plugin_path)

    # Merge issues
    all_critical = json_issues["critical"]
    all_warnings = json_issues["warnings"] + dir_issues["warnings"]
    all_recommendations = json_issues["recommendations"] + dir_issues["recommendations"]

    # Display results
    if all_critical:
        print("\n[!] CRITICAL ISSUES:")
        for issue in all_critical:
            print(f"  • {issue}")

    if all_warnings:
        print("\n[*] WARNINGS:")
        for issue in all_warnings:
            print(f"  • {issue}")

    if all_recommendations:
        print("\n[+] RECOMMENDATIONS:")
        for issue in all_recommendations:
            print(f"  • {issue}")

    if not (all_critical or all_warnings or all_recommendations):
        print("\n[SUCCESS] Plugin structure is valid!")

    print("=" * 60)

    # Return exit code
    return 1 if all_critical else 0
```

## Usage

### Command Line Validation

```bash
# Validate a plugin
cd /path/to/plugin
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate-plugin.py .

# Or use the skill directly
/validate-plugin /path/to/plugin
```

### Programmatic Validation

```python
from pathlib import Path
from validate_plugin import validate_plugin_json, generate_report

plugin_path = Path("~/claude-night-market/plugins/archetypes").expanduser()
exit_code = generate_report(plugin_path)
```

## Common Issues and Fixes

### Issue: plugin.json at root instead of .claude-plugin/

**Fix:**
```bash
mkdir -p .claude-plugin
mv plugin.json .claude-plugin/plugin.json
```

### Issue: Invalid plugin name (spaces or uppercase)

**Fix:** Update `name` field in plugin.json to use kebab-case:
```json
{
  "name": "my-plugin-name"  // lowercase, hyphens only
}
```

### Issue: Absolute paths in plugin.json

**Fix:** Convert to relative paths:
```json
{
  "skills": [
    "./skills/my-skill"  // not "/home/user/skills/my-skill"
  ]
}
```

### Issue: Missing standard directories

**Fix:**
```bash
mkdir -p skills commands agents hooks
```

## Best Practices

1. **Always validate before distribution** - Run validation as part of your CI/CD
2. **Use semantic versioning** - Follow semver for version numbers
3. **Document dependencies** - Clearly specify version requirements
4. **Keep structure standard** - Only customize paths when necessary
5. **Use progressive disclosure** - Break complex skills into sections
6. **Test with Claude Code** - Actually install and test the plugin

## Integration with CI/CD

Add to your `.github/workflows/validate.yml`:

```yaml
name: Validate Plugin Structure

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate plugin structure
        run: |
          python scripts/validate-plugin.py .
```

## Conclusion

Regular validation ensures your plugin:
- Loads correctly in Claude Code
- Follows official conventions
- Works across different environments
- Integrates well with other plugins
- Provides good developer experience

Run this validation whenever you create or modify a plugin!
