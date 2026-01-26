---
name: from-hook
description: Convert Python SDK hooks to hookify rules
---

# /hookify:from-hook

Convert Python SDK hooks to declarative hookify rules.

## Usage

```bash
/hookify:from-hook <hook_file.py>           # Convert single hook
/hookify:from-hook --scan <hooks_dir>       # Scan directory
/hookify:from-hook <hook.py> -o rules.md    # Output to file
```

## What It Does

1. Parses Python hook AST
2. Extracts regex patterns, string checks, startswith/endswith
3. Generates equivalent hookify rule YAML
4. Reports unconvertible hooks (network, file I/O, complex logic)

## Example

Input hook:
```python
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
action: block
---
Dangerous command blocked.
```

## Limitations

Cannot convert hooks with:
- Network calls (API requests)
- File I/O operations
- Complex conditional logic
- External dependencies

## See Also

- `hookify:browse` - Browse available rules
- `hookify:install` - Install rules
