---
name: require-spec-before-code
enabled: false
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: ^src/.*\.(py|ts|rs|go)$
  - field: file_path
    operator: not_contains
    pattern: test
---

**BLOCKED: No spec file for this feature**

Spec-kit enforces specification-driven development:

**The workflow:**
```
1. Write spec    - /spec-kit:write <feature>
2. Review spec   - /spec-kit:review specs/<feature>.md
3. THEN implement - (this action)
4. Verify        - /spec-kit:verify specs/<feature>.md
```

**To proceed, either:**

1. **Create the spec first:**
```bash
/spec-kit:write <feature-name>
```

2. **Or link to existing spec:**
```bash
# Add to your file header:
# Spec: specs/<feature>.md
```

3. **Or disable for this project** (not recommended):
```bash
# Edit: .claude/hookify.require-spec-before-code.local.md
# Set: enabled: false
```

**Why spec-first matters:**
- Clear requirements before coding
- Better test coverage from spec
- Documentation generated from spec
- Team alignment on expectations
