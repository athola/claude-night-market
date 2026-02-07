---
name: block-destructive-git
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: git\s+(reset\s+--hard|checkout\s+--\s+\.|checkout\s+HEAD\s+--|clean\s+-[fd]+|stash\s+drop|branch\s+-D)
---

🛑 **Destructive Git Operation Blocked!**

This command destroys uncommitted work. Even with sandbox auto-allow mode, destructive git operations warrant an explicit safety gate.

## What You're About to Lose

Run these commands to see what would be destroyed:

```bash
# For reset --hard / checkout -- .
git diff HEAD              # All uncommitted changes
git status                 # Summary view

# For clean -fd
git clean -nfd             # Dry-run: shows files that would be deleted

# For stash drop
git stash show -p          # Contents of stash
```

## Safer Workflow

1. **Stash instead of discard**: `git stash`
2. **Backup branch**: `git checkout -b backup/my-work`
3. **Selective reset**: `git checkout -- specific/file.txt`

## To Proceed Anyway

If you've verified the changes should be discarded:
1. Edit this file: `.claude/hookify.block-destructive-git.local.md`
2. Set `enabled: false`
3. Run your command
4. Re-enable immediately
