---
name: rule-catalog
description: |
  Browse and install pre-built hookify rules from the official catalog.

  Triggers: install hookify rule, hookify catalog, browse rules, pre-built rules,
  available hookify rules, hookify templates

  Use when: looking for ready-made hookify rules, installing standard rules,
  browsing available rule categories

  DO NOT use when: writing custom rules - use hookify:writing-rules instead.

  This skill provides the catalog and guides installation.
version: 1.0.0
category: hook-development
tags: [hookify, rules, catalog, install, templates]
dependencies: []
estimated_tokens: 1500
complexity: beginner
provides:
  patterns: [rule-installation, rule-browsing]
  infrastructure: [rule-catalog]
usage_patterns:
  - browsing-rules
  - installing-rules
---

# Hookify Rule Catalog

Pre-built rules for common scenarios. Install directly or use as templates.

## Quick Install

```bash
# Install a specific rule
Skill(hookify:rule-catalog) then install git:block-force-push

# Or use the Python installer for bulk operations
python3 plugins/hookify/scripts/install_rule.py git:block-force-push
python3 plugins/hookify/scripts/install_rule.py --category git
python3 plugins/hookify/scripts/install_rule.py --all
```

## Available Rules

### git/ - Git Safety
| Rule | Action | Default | Description |
|------|--------|---------|-------------|
| `block-force-push` | block | enabled | Prevent force push to main/master |
| `warn-large-commits` | warn | enabled | Warn about large binary files |

### python/ - Python Quality
| Rule | Action | Default | Description |
|------|--------|---------|-------------|
| `block-dynamic-code` | block | enabled | Block dangerous dynamic code execution |
| `warn-print-statements` | warn | enabled | Encourage logging over print() |

### security/ - Security Gates
| Rule | Action | Default | Description |
|------|--------|---------|-------------|
| `require-security-review` | block | enabled | Require review for auth code |

### workflow/ - Workflow Enforcement
| Rule | Action | Default | Description |
|------|--------|---------|-------------|
| `enforce-scope-guard` | warn | enabled | Anti-overengineering (imbue) |
| `require-spec-before-code` | block | disabled | Spec-first development |

### performance/ - Resource Management
| Rule | Action | Default | Description |
|------|--------|---------|-------------|
| `warn-large-file-ops` | warn | enabled | Watch large file writes |

## Installation Instructions

### Method 1: Claude-Assisted (Recommended)

When you invoke this skill, tell Claude which rule(s) to install:

```
Install git:block-force-push
```

Claude will:
1. Read the rule from `skills/rule-catalog/rules/git/block-force-push.md`
2. Write it to `.claude/hookify.block-force-push.local.md`
3. Confirm installation

### Method 2: Python Script

For bulk operations or automation:

```bash
# Install single rule
python3 plugins/hookify/scripts/install_rule.py git:block-force-push

# Install all rules in category
python3 plugins/hookify/scripts/install_rule.py --category python

# Install all rules
python3 plugins/hookify/scripts/install_rule.py --all

# List available rules
python3 plugins/hookify/scripts/install_rule.py --list

# Install to custom directory
python3 plugins/hookify/scripts/install_rule.py git:block-force-push --target /path/to/.claude
```

### Method 3: Manual Copy

1. Find rule in `plugins/hookify/skills/rule-catalog/rules/<category>/<rule>.md`
2. Copy to `.claude/hookify.<rule-name>.local.md`
3. Edit `enabled: true/false` as needed

## Rule File Locations

Rules are stored relative to this skill:

```
skills/rule-catalog/
├── SKILL.md (this file)
└── rules/
    ├── git/
    │   ├── block-force-push.md
    │   └── warn-large-commits.md
    ├── python/
    │   ├── block-dynamic-code.md
    │   └── warn-print-statements.md
    ├── security/
    │   └── require-security-review.md
    ├── workflow/
    │   ├── enforce-scope-guard.md
    │   └── require-spec-before-code.md
    └── performance/
        └── warn-large-file-ops.md
```

## Customizing Rules

After installation, edit the rule in `.claude/`:

```yaml
# Change action from warn to block
action: block

# Disable temporarily
enabled: false

# Modify pattern
pattern: your-custom-pattern
```

## Creating Pull Requests for New Rules

To add rules to the catalog:

1. Create rule file in appropriate category
2. Follow naming convention: `kebab-case.md`
3. Include comprehensive message with alternatives
4. Test thoroughly before submitting
5. Update this SKILL.md catalog table

## Related

- `Skill(hookify:writing-rules)` - Create custom rules
- `/hookify:list` - Show installed rules
- `/hookify:configure` - Manage installed rules
