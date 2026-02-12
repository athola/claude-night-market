---
name: configure
description: Interactive interface to enable/disable rules
usage: /hookify:configure
examples:
  - /hookify:configure
---

# Hookify Configure Command

Interactive configuration for enabling and disabling rules.

## Usage

```bash
/hookify:configure
```

## Interactive Flow

1. Shows list of all rules
2. Prompts for which rule to configure
3. Asks to enable, disable, or delete
4. Updates rule file immediately

## Example Session

```
Hookify Rules
=============

1. ✅ dangerous-rm (bash, block)
2. ⚠️  warn-console-log (file, warn)
3. ❌ require-tests (stop, warn) [DISABLED]

Select rule number (1-3) or 'q' to quit: 3

Rule: require-tests
Status: Disabled
Event: stop
Action: warn

Actions:
  [e] Enable rule
  [d] Delete rule
  [q] Cancel

Choice: e

✅ Rule 'require-tests' enabled!
```

## Quick Enable/Disable

You can also edit files directly:

```bash
# Disable a rule
vi .claude/hookify.dangerous-rm.local.md
# Change: enabled: false

# Enable a rule
# Change: enabled: true
```

## See Also

- `/hookify:list` - View all rules
- `/hookify` - Create new rule
