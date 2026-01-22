# hookify

Create custom behavioral rules through markdown configuration files.

## Overview

Hookify provides a framework for defining behavioral rules that prevent unwanted actions through pattern matching. Rules are defined in markdown files and can be enabled, disabled, or customized per project.

## Installation

```bash
/plugin install hookify@claude-night-market
```

## Skills

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `writing-rules` | Guide for authoring behavioral rules | Creating new rules |
| `rule-catalog` | Pre-built behavioral rule templates | Installing common rules |

## Commands

| Command | Description |
|---------|-------------|
| `/hookify` | Create behavioral rules to prevent unwanted actions |
| `/hookify:install` | Install hookify rule from catalog |
| `/hookify:list` | List all hookify rules with status |
| `/hookify:configure` | Interactive rule enable/disable interface |
| `/hookify:help` | Display hookify help and documentation |

## Usage Examples

### Install a Rule

```bash
# Install from catalog
/hookify:install no-force-push

# List installed rules
/hookify:list --status
```

### Create Custom Rule

```bash
# Create a new rule interactively
/hookify

# Configure existing rule
/hookify:configure no-force-push --disable
```

### Rule Structure

Rules are markdown files with frontmatter:

```markdown
---
name: no-force-push
trigger: PreToolUse
matcher: Bash
pattern: "git push.*--force"
action: block
message: "Force push blocked. Use --force-with-lease instead."
---

# No Force Push Rule

Prevents accidental force pushes that could overwrite remote history.
```

## Integration

Hookify integrates with:
- **abstract**: Rule validation and testing
- **imbue**: Scope guard integration
- **sanctum**: Git workflow protection
