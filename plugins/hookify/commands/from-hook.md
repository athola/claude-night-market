---
name: from-hook
description: Convert Python SDK hooks to declarative rules
---

# /hookify:from-hook

Convert Python SDK hooks to declarative hookify rules.

## Usage

```bash
/hookify:from-hook <hook_file.py>           # Convert single hook
/hookify:from-hook --scan <hooks_dir>       # Scan directory
/hookify:from-hook <hook.py> -o rules.md    # Output to file
```

## Run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/hook_to_hookify.py" $ARGUMENTS
```

The script prints each hook it did not convert, with the reason, to
stderr as a `Not converted:` line. It exits 1 when no hook converted.
Report the generated rules and every `Not converted:` line.

## What It Does

1. Parses Python hook AST
2. Extracts regex patterns, string checks, startswith/endswith
3. Generates equivalent hookify rule YAML
4. Reports unconvertible hooks (network, file I/O, complex logic)

## Example

Input hook. The converter reads the hook type from the filename
(`pre_tool_*.py`) or from a `PreToolUse`-style comment, as here:

```python
# PreToolUse
import re
def hook(context):
    if re.search(r"rm -rf /", context["command"]):
        return {"action": "block", "message": "Dangerous!"}
```

Output rule:
```yaml
---
name: block-rm-rf
event: bash
pattern: 'rm -rf /'
action: warn
---
```

Every generated rule is `action: warn`. Review it, then change it to
`block` by hand where the original hook blocked.

## Limitations

Cannot convert hooks with:
- Network calls (API requests)
- File I/O operations
- Complex conditional logic
- External dependencies

## See Also

- `hookify:rule-catalog` - Browse available rules
- `hookify:install` - Install rules
