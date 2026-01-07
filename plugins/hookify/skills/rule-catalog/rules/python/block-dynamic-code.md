---
name: block-dynamic-code
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: (^|\s)(exec|eval)\s*\(
---

**SECURITY: Dynamic code execution detected!**

Using functions that execute arbitrary strings as code is a **critical security risk**.

**Dangers:**
- Arbitrary code execution
- Injection attacks
- Difficult to audit
- Bypasses security controls

**Safer alternatives:**

For expression evaluation:
```python
# Use ast.literal_eval for safe evaluation
import ast
result = ast.literal_eval(user_input)  # Only evaluates literals

# Use operator module for math
import operator
ops = {'+': operator.add, '-': operator.sub}
result = ops[op](a, b)
```

For dynamic behavior:
```python
# Use importlib for dynamic imports
import importlib
module = importlib.import_module(module_name)

# Use getattr for dynamic attribute access
fn = getattr(obj, method_name)
result = fn(*args)

# Use configuration files
import json
config = json.load(config_file)
```

**If you absolutely must use dynamic execution:**
1. Document the security review
2. Sanitize all inputs
3. Use restricted execution environments
4. Get security team approval
5. Temporarily disable this rule
