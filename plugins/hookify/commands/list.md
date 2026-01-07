---
name: list
description: List all hookify rules with their status
usage: |
  /hookify:list [--enabled|--disabled|--all]
examples:
  - /hookify:list
  - /hookify:list --enabled
  - /hookify:list --disabled
---

# Hookify List Command

Displays all hookify rules in the project.

## Usage

```bash
# List all rules
/hookify:list

# Only enabled rules
/hookify:list --enabled

# Only disabled rules
/hookify:list --disabled
```

## Output Format

```
Hookify Rules
=============

✅ dangerous-rm (bash, block)
   Location: .claude/hookify.dangerous-rm.local.md
   Pattern: rm\s+-rf|dd\s+if=

⚠️  warn-console-log (file, warn)
   Location: .claude/hookify.warn-console-log.local.md
   Pattern: console\.log\(

❌ require-tests (stop, warn) [DISABLED]
   Location: .claude/hookify.require-tests.local.md
   Conditions: 1 condition(s)

Total: 3 rules (2 enabled, 1 disabled)
```

## Legend

- ✅ = Enabled, blocking
- ⚠️ = Enabled, warning only
- ❌ = Disabled

## See Also

- `/hookify:configure` - Enable/disable rules
- `/hookify` - Create new rule
