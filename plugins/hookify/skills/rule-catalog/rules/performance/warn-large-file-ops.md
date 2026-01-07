---
name: warn-large-file-ops
enabled: true
event: file
action: warn
conditions:
  - field: new_text
    operator: regex_match
    pattern: .{10000,}
---

**Large file operation detected!**

You're writing a large amount of data (>10KB) in a single operation.

**Performance impact:**
- High token usage in context
- Slower Claude responses
- Memory pressure
- Network bandwidth

**Better approaches:**

For large data:
```python
# Instead of one large write
with open('huge_file.json', 'w') as f:
    f.write(massive_json_string)  # Large context

# Use streaming or chunking
import json
with open('huge_file.json', 'w') as f:
    for chunk in data_chunks:
        json.dump(chunk, f)  # Smaller operations
```

For generated code:
```python
# Generate to file directly
with open('generated.py', 'w') as f:
    for section in code_sections:
        f.write(section + '\n')
```

**Resource monitoring:**
```bash
# Check file sizes
/conserve:analyze-resources

# Monitor token usage
/conserve:token-usage
```
