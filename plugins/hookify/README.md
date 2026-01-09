# Hookify Plugin

**Zero-config behavioral rules - 8 safety rules active immediately upon installation.**

## Overview

Hookify includes **bundled rules that work out of the box**. Just install the plugin and you're protected.

## Zero-Touch Experience

```bash
# Install the plugin
claude install hookify@claude-night-market

# 8 rules are now active:
# - Block force push to main/master
# - Warn about large binary files in git
# - Block dangerous dynamic code execution
# - Warn about print statements in Python
# - Require security review for auth code changes
# - Enforce scope-guard for new features
# - Block code without specs (disabled by default)
# - Warn about large file operations
```

## Bundled Rules

| Category | Rule | Action | Status |
|----------|------|--------|--------|
| **git** | `block-force-push` | block | enabled |
| **git** | `warn-large-commits` | warn | enabled |
| **python** | `block-dynamic-code` | block | enabled |
| **python** | `warn-print-statements` | warn | enabled |
| **security** | `require-security-review` | block | enabled |
| **workflow** | `enforce-scope-guard` | warn | enabled |
| **workflow** | `require-spec-before-code` | block | disabled |
| **performance** | `warn-large-file-ops` | warn | enabled |

## Customizing Rules

### Override a Bundled Rule

Create a file in `.claude/` with the same rule name to override:

```bash
# Disable block-force-push for this project
cat > .claude/hookify.block-force-push.local.md << 'EOF'
---
name: block-force-push
enabled: false
event: bash
pattern: git push --force
action: warn
---
Disabled for this project
EOF
```

### Create Custom Rules

```bash
/hookify Don't use console.log in TypeScript files
```

Or manually create `.claude/hookify.{name}.local.md`:

```yaml
---
name: warn-console-log
enabled: true
event: file
pattern: console\.log\(
action: warn
---

Remove console.log before committing.
```

## Rule Syntax

### Event Types

- `bash` - Bash tool commands
- `file` - Edit/Write/MultiEdit operations
- `stop` - Before stopping execution
- `prompt` - User prompt submission
- `all` - All events

### Actions

- `warn` - Show warning but allow operation (default)
- `block` - Prevent operation entirely

### Advanced Conditions

```yaml
---
name: protect-env
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.env$
  - field: new_text
    operator: contains
    pattern: API_KEY
---

API keys should not be in .env files.
```

### Operators

- `regex_match` - Regex pattern matching
- `contains` - Substring check
- `equals` - Exact match
- `not_contains` - Must NOT contain
- `starts_with` - Prefix check
- `ends_with` - Suffix check

## Commands

| Command | Description |
|---------|-------------|
| `/hookify [instruction]` | Create rule from natural language |
| `/hookify:list` | Show all active rules |
| `/hookify:configure` | Enable/disable rules |
| `/hookify:install` | Install additional rules |
| `/hookify:help` | Display help |

## Skills

| Skill | Purpose |
|-------|---------|
| `hookify:rule-catalog` | Browse bundled rules |
| `hookify:writing-rules` | Complete rule syntax guide |

## Architecture

```
Bundled Rules (8 rules)          User Rules (.claude/)
        ↓                                ↓
    [ConfigLoader] ──────────────────────┘
        ↓
    (User rules override bundled with same name)
        ↓
    [RuleEngine]
        ↓
    Evaluate on tool use
```

**Key design:**
- Bundled rules use `Path(__file__)` for portable location
- User rules in `.claude/` override bundled rules by name
- No manual installation required

## Installation

```bash
claude install hookify@claude-night-market
```

Or from source:

```bash
git clone https://github.com/athola/claude-night-market
cd claude-night-market
claude install ./plugins/hookify
```

## Documentation

- **Rule Catalog**: `Skill(hookify:rule-catalog)`
- **Rule Writing**: `Skill(hookify:writing-rules)`
- **Hook Scope**: `Skill(abstract:hook-scope-guide)`

## Credits

Inspired by the original [hookify plugin](https://github.com/anthropics/claude-code/tree/main/plugins/hookify) by Daisy Hollman at Anthropic.

Enhanced for claude-night-market with:
- Zero-config bundled rules
- Portable path resolution via `__file__`
- User override support
- Night-market plugin integration
