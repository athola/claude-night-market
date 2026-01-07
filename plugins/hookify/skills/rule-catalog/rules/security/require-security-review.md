---
name: require-security-review
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: (auth|login|session|token|password|credential|secret|crypto|security)
  - field: new_text
    operator: regex_match
    pattern: (password|token|secret|key|hash|encrypt|decrypt|auth|session)
---

**BLOCKED: Security-sensitive code requires pensive review!**

You're modifying authentication/security code.

**Required before this change:**
```bash
Skill(pensive:security-review)
```

**Security review checklist:**
- [ ] No hardcoded secrets
- [ ] Proper input validation
- [ ] Secure session management
- [ ] Password hashing (bcrypt/argon2)
- [ ] Rate limiting on auth endpoints
- [ ] Error messages don't leak info
- [ ] Logging doesn't expose secrets
- [ ] HTTPS only for sensitive data

**After review, to proceed:**
```bash
# Disable temporarily
# .claude/hookify.require-security-review.local.md - enabled: false
# Make changes
# Re-enable rule
```

**Why this blocks (not warns):**
Security vulnerabilities can cause severe damage.
Review MUST happen before changes.
