# Hook Authoring Scripts

Utilities for validating and testing Claude Code and SDK hooks.

## hook_validator.py

Validates hook files for syntax, structure, and compliance with hook specifications.

### Features

- **JSON Hook Validation**: Validates `hooks.json` files for Claude Code
  - JSON syntax validation
  - Required field checking
  - Known event type verification
  - Hook action validation

- **Python SDK Hook Validation**: Validates Python files containing `AgentHooks` subclasses
  - Python syntax validation
  - `AgentHooks` inheritance checking
  - Callback method signature verification
  - Async definition validation

### Usage

```bash
# Make executable (first time only)
chmod +x hook_validator.py

# Validate JSON hook file
./hook_validator.py hooks/hooks.json

# Validate Python SDK hook file
./hook_validator.py my_hooks.py

# Specify type explicitly
./hook_validator.py hooks.json --type json
./hook_validator.py my_hooks.py --type python

# Verbose output (show info messages)
./hook_validator.py hooks.json --verbose
```

### Exit Codes

- `0`: Success, no issues found
- `1`: Warnings found (valid but with recommendations)
- `2`: Errors found (invalid)

### Example Output

**Valid JSON hook:**
```
OK Valid

Info:
  [INFO]  Loaded JSON from hooks/hooks.json
  [INFO]  Validated 2 event type(s)
```

**Invalid Python hook:**
```
FAIL Invalid

Errors:
  FAIL MyHooks.on_pre_tool_use: should be async (async def)
  FAIL MyHooks.on_post_tool_use: incorrect arguments. Expected ['self', 'tool_name', 'tool_input', 'tool_output'], got ['self', 'tool', 'output']
```

### JSON Hook Validation

Checks for:
- Valid JSON syntax
- Known event types (`PreToolUse`, `PostToolUse`, etc.)
- Required fields (`hooks` array)
- Hook action structure (`type`, `command`)
- Matcher validity (`toolName`, `inputPattern`)

### Python SDK Hook Validation

Checks for:
- Valid Python syntax
- `AgentHooks` base class inheritance
- Async callback methods (`async def`)
- Correct callback signatures:
  - `on_pre_tool_use(self, tool_name, tool_input) -> dict | None`
  - `on_post_tool_use(self, tool_name, tool_input, tool_output) -> str | None`
  - `on_user_prompt_submit(self, message) -> str | None`
  - `on_stop(self, reason, result) -> None`
  - `on_subagent_stop(self, subagent_id, result) -> None`
  - `on_pre_compact(self, context_size) -> dict | None`

## Integration with CI/CD

### Pre-commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
echo "Validating hooks..."

# Find all hook files
json_hooks=$(find . -name "hooks.json" -not -path "*/node_modules/*" -not -path "*/.git/*")
python_hooks=$(find . -name "*_hooks.py" -not -path "*/tests/*" -not -path "*/.git/*")

# Validate JSON hooks
for hook in $json_hooks; do
    if ! ./scripts/hook_validator.py "$hook"; then
        echo "Hook validation failed: $hook"
        exit 1
    fi
done

# Validate Python hooks
for hook in $python_hooks; do
    if ! ./scripts/hook_validator.py "$hook"; then
        echo "Hook validation failed: $hook"
        exit 1
    fi
done

echo "OK All hooks validated"
```

### GitHub Actions

Add to `.github/workflows/validate-hooks.yml`:

```yaml
name: Validate Hooks

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Validate JSON hooks
        run: |
          find . -name "hooks.json" -not -path "*/node_modules/*" | while read hook; do
            python scripts/hook_validator.py "$hook" --verbose
          done

      - name: Validate Python hooks
        run: |
          find . -name "*_hooks.py" -not -path "*/tests/*" | while read hook; do
            python scripts/hook_validator.py "$hook" --verbose
          done
```

## Testing

Test the validator itself:

```bash
# Test with valid JSON hook
echo '{
  "PreToolUse": [{
    "matcher": {"toolName": "Bash"},
    "hooks": [{"type": "command", "command": "echo test"}]
  }]
}' > test_hooks.json

./hook_validator.py test_hooks.json
# Should exit with 0

# Test with invalid JSON hook
echo '{"invalid": "structure"}' > test_invalid.json

./hook_validator.py test_invalid.json
# Should exit with 1 or 2

# Clean up
rm test_hooks.json test_invalid.json
```

## Dependencies

- Python 3.11+
- Standard library only (no external dependencies)

## Related Files

- **SKILL.md**: Main hook authoring guide
- **modules/hook-types.md**: Hook event specifications
- **modules/sdk-callbacks.md**: Python SDK patterns
- **modules/security-patterns.md**: Security validation guidelines
- **modules/testing-hooks.md**: detailed testing strategies
