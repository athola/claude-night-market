---
name: warn-console-log
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.(ts|tsx|js|jsx)$
  - field: new_text
    operator: regex_match
    pattern: console\.(log|warn|error|debug)\(
---

🐛 **Debug logging detected in source file!**

You're adding console statements to code.

**Why this matters:**
- Debug logs shouldn't ship to production
- Can expose sensitive data in browser console
- Impacts performance in production builds
- Hard to track and remove later

**Better alternatives:**
```typescript
// Use a proper logging library
import { logger } from './logger';
logger.debug('Debug info', { data });

// Or use conditional logging
if (process.env.NODE_ENV === 'development') {
  console.log('Dev only');
}
```

**To proceed anyway:**
This is a warning only - the operation will complete.
