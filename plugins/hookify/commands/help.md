---
name: help
description: Display help and documentation
usage: /hookify:help
examples:
  - /hookify:help
---

# Hookify Help

## Overview

Hookify enables creation of custom behavioral rules through markdown configuration files. Prevent unwanted behaviors with pattern matching - no complex JSON or coding required.

## Quick Start

1. **Create a rule:**
   ```bash
   /hookify Don't use console.log in files
   ```

2. **View your rules:**
   ```bash
   /hookify:list
   ```

3. **Manage rules:**
   ```bash
   /hookify:configure
   ```

## Commands

- `/hookify [instruction]` - Create rule or analyze conversation
- `/hookify:list` - Show all rules
- `/hookify:configure` - Enable/disable rules interactively
- `/hookify:help` - This help message

## Rule Files

Rules are stored in `.claude/hookify.{name}.local.md`

### Example Rule

```yaml
---
name: dangerous-rm
enabled: true
event: bash
pattern: rm\s+-rf
action: block
---

🛑 **Dangerous rm command!**
This could delete files.
```

## Event Types

- **bash** - Bash commands
- **file** - File edits
- **stop** - Before stopping
- **prompt** - User input
- **all** - All events

## Actions

- **warn** - Show warning, allow operation (default)
- **block** - Prevent operation

## Learn More

For detailed rule syntax and examples:

```bash
Skill(hookify:writing-rules)
```

For hook scope decisions:

```bash
Skill(abstract:hook-scope-guide)
```

## Support

Issues and questions:
https://github.com/athola/claude-night-market/issues
