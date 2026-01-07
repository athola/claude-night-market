---
name: warn-print-statements
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: ^\s*print\(
---

**Print statement detected in Python!**

You're adding `print()` calls to Python code.

**Why this matters:**
- Print statements bypass proper logging
- Can't be filtered or configured
- Pollute stdout in production
- Hard to track and remove

**Better alternatives:**
```python
# Use logging module
import logging
logger = logging.getLogger(__name__)

# Instead of print
logger.debug("Debug info: %s", data)
logger.info("Status update: %s", status)
logger.warning("Warning: %s", warning)

# Configure logging levels
logging.basicConfig(level=logging.INFO)
```

**Quick logging setup:**
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**For debugging only:**
If this is temporary debugging code, remember to remove before committing.
