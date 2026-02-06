---
name: hookify
description: Create behavioral rules to prevent unwanted actions
usage: /hookify [instruction]
examples:
  - /hookify Don't use console.log in TypeScript files
  - /hookify Block rm -rf commands
---

# Hookify Command

Creates custom behavioral rules to prevent unwanted actions.

## When To Use

Use this command when you need to:
- Creating rules from explicit instructions
- Analyzing conversation for unwanted behaviors to block

## When NOT To Use

- Complex multi-step workflows - use agents instead
- One-time operations that don't need persistent rules

## Usage

### Create Rule from Instruction

```bash
/hookify Don't use console.log in TypeScript files
```

This will:
1. Parse your instruction
2. Determine appropriate event type (bash, file, etc.)
3. Generate regex pattern
4. Create rule file in `.claude/`
5. Enable rule immediately

### Analyze Conversation

```bash
/hookify
```

Without arguments, hookify will:
1. Analyze recent conversation history
2. Identify unwanted behaviors or mistakes
3. Suggest rules to prevent recurrence
4. Ask if you want to create them

## Rule Creation Flow

1. **Event Detection**: Determines which tool the rule applies to
2. **Pattern Generation**: Creates regex pattern from your description
3. **Action Selection**: Chooses warn or block based on severity
4. **Message Creation**: Generates helpful message for Claude
5. **File Creation**: Saves to `.claude/hookify.{name}.local.md`

## Examples

### Block Dangerous Commands

```bash
/hookify Block rm -rf and other destructive operations
```

Creates:
```yaml
---
name: block-destructive-ops
enabled: true
event: bash
pattern: rm\s+-rf|dd\s+if=|mkfs
action: block
---

🛑 **Destructive operation detected!**
This command can cause data loss.
```

### Warn About Debug Code

```bash
/hookify Warn when I add console.log to files
```

Creates:
```yaml
---
name: warn-console-log
enabled: true
event: file
pattern: console\.log\(
action: warn
---

🐛 **Debug code detected!**
Remove console.log before committing.
```

### Require Tests

```bash
/hookify Remind me to run tests before stopping
```

Creates:
```yaml
---
name: require-tests
enabled: true
event: stop
action: warn
conditions:
  - field: transcript
    operator: not_contains
    pattern: npm test|pytest
---

⚠️ **Tests not detected!**
Run tests before completing.
```

## See Also

- `/hookify:list` - View all rules
- `/hookify:configure` - Enable/disable rules
- `/hookify:help` - Show help
- `Skill(hookify:writing-rules)` - Learn rule syntax
