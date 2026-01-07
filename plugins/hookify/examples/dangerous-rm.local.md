---
name: dangerous-rm
enabled: true
event: bash
pattern: rm\s+-rf|dd\s+if=/dev/|mkfs\.|format\s+
action: block
---

🛑 **Destructive operation detected!**

This command can cause irreversible data loss:
- `rm -rf` - Recursively force-delete files
- `dd if=/dev/` - Direct device writes
- `mkfs.*` - Format filesystems
- `format` - Format drives

**Before proceeding:**
1. ✅ Verify the target path is correct
2. ✅ Ensure you have recent backups
3. ✅ Consider safer alternatives

**To allow this operation:**
Temporarily disable this rule:
```bash
# Edit .claude/hookify.dangerous-rm.local.md
# Set: enabled: false
```
