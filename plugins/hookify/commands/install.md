---
name: install
description: Install a hookify rule from the catalog
usage: |
  /hookify:install <category>:<rule-name>
  /hookify:install --category <name>
  /hookify:install --all
  /hookify:install --list
examples:
  - /hookify:install git:block-force-push
  - /hookify:install python:warn-print-statements
  - /hookify:install --category security
  - /hookify:install --list
---

# Hookify Install Command

Install hookify rules from the rule catalog.

## Quick Start

```bash
# Use the Python installer (recommended)
python3 plugins/hookify/scripts/install_rule.py git:block-force-push

# Or invoke the skill for Claude-assisted installation
Skill(hookify:rule-catalog)
```

## Python Installer Usage

The installer uses `__file__` to locate rules, so it works regardless of where the plugin is installed.

### Install Single Rule

```bash
python3 plugins/hookify/scripts/install_rule.py git:block-force-push
```

### Install All Rules in Category

```bash
python3 plugins/hookify/scripts/install_rule.py --category git
```

### Install All Rules

```bash
python3 plugins/hookify/scripts/install_rule.py --all
```

### List Available Rules

```bash
python3 plugins/hookify/scripts/install_rule.py --list
```

## Available Rules

### git/ - Git Safety
| Rule | Action | Default |
|------|--------|---------|
| `block-force-push` | block | enabled |
| `warn-large-commits` | warn | enabled |

### python/ - Python Quality
| Rule | Action | Default |
|------|--------|---------|
| `block-dynamic-code` | block | enabled |
| `warn-print-statements` | warn | enabled |

### security/ - Security Gates
| Rule | Action | Default |
|------|--------|---------|
| `require-security-review` | block | enabled |

### workflow/ - Workflow Enforcement
| Rule | Action | Default |
|------|--------|---------|
| `enforce-scope-guard` | warn | enabled |
| `require-spec-before-code` | block | disabled |

### performance/ - Resource Management
| Rule | Action | Default |
|------|--------|---------|
| `warn-large-file-ops` | warn | enabled |

## Installation Options

```bash
# Install with default status
python3 plugins/hookify/scripts/install_rule.py git:block-force-push

# Force overwrite existing
python3 plugins/hookify/scripts/install_rule.py git:block-force-push --force

# Install to custom directory
python3 plugins/hookify/scripts/install_rule.py git:block-force-push --target /path/to/.claude
```

## Uninstall

```bash
rm .claude/hookify.<rule-name>.local.md
```

## Rule Location

Rules are stored in the skill catalog:
```
plugins/hookify/skills/rule-catalog/rules/
├── git/
├── python/
├── security/
├── workflow/
└── performance/
```

## See Also

- `Skill(hookify:rule-catalog)` - Browse and install rules
- `/hookify:list` - Show installed rules
- `/hookify:configure` - Manage installed rules
- `Skill(hookify:writing-rules)` - Create custom rules
