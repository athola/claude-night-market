---
name: block-force-push
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: git\s+push\s+.*(-f|--force)
  - field: command
    operator: regex_match
    pattern: (main|master)
---

**Force push to main/master detected!**

Force pushing to the main branch can:
- Overwrite team members' work
- Break production deployments
- Cause irreversible data loss
- Violate team git policies

**Safer alternatives:**
```bash
# Create a new branch instead
git checkout -b fix/my-changes

# Or rebase locally first
git pull --rebase origin main

# Or use --force-with-lease (safer)
git push --force-with-lease origin main
```

**To override this rule:**
If you really need to force push (rare):
1. Get team approval
2. Temporarily disable: `.claude/hookify.block-force-push.local.md` - `enabled: false`
3. Force push
4. Re-enable the rule
