---
name: require-tests
enabled: false
event: stop
action: warn
conditions:
  - field: transcript
    operator: not_contains
    pattern: npm test|pytest|cargo test|go test|mvn test
---

⚠️ **Tests not detected in session!**

Before completing, verify your changes work correctly.

**Run tests:**
```bash
# JavaScript/TypeScript
npm test

# Python
pytest

# Rust
cargo test

# Go
go test ./...

# Java
mvn test
```

**Why test:**
- Catch regressions early
- Verify new features work
- Ensure edge cases handled
- Document expected behavior

**Note:** This is disabled by default. Enable in:
`.claude/hookify.require-tests.local.md` → `enabled: true`
