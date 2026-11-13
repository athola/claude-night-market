---
name: require-security-review
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: (auth|login|session|token|password|credential|secret|crypto|security)
  - field: new_text
    operator: regex_match
    pattern: (password|token|secret|key|hash|encrypt|decrypt|auth|session)
---

Security-sensitive code protects the people who trust
this system with their data. Changes here deserve
careful review.
(Care, Diligence)

**Security-sensitive code: run a pensive review before merging.**

You're modifying authentication/security code.

**Recommended for this change:**
```bash
Skill(pensive:harden)
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

**Why this warns (not blocks):**
Bundled rules load for every user. The patterns match
words like "key", "hash" and "session" anywhere in a
path or edit, so a block denied comments and docs.
Install a local copy with `action: block` to enforce it.
