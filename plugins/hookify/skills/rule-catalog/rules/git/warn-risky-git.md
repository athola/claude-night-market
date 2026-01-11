---
name: warn-risky-git
enabled: true
event: bash
action: warn
conditions:
  - field: command
    operator: regex_match
    pattern: git\s+(reset\s+--(soft|mixed)|reset\s+HEAD\s+|checkout\s+\S+\s+--|rebase\s+-i|rebase\s+--onto|cherry-pick\s+--abort|merge\s+--abort|am\s+--abort)
---

⚠️ **Risky Git Operation Detected**

This command modifies history or discards work. Please verify before proceeding.

## What This Command Does

| Command | Effect | Recovery |
|---------|--------|----------|
| `git reset` (soft/mixed) | Moves HEAD, may unstage | `git reflog` + `git reset` |
| `git checkout <branch> -- <file>` | Replaces file from branch | None for uncommitted |
| `git rebase -i` | Rewrites commit history | `git reflog` |
| `git rebase --onto` | Transplants commits | `git reflog` |
| `git cherry-pick --abort` | Discards in-progress pick | None |
| `git merge --abort` | Discards in-progress merge | None |
| `git am --abort` | Discards in-progress patch | None |

## Before Proceeding

```bash
# Always check current state
git status
git log --oneline -5

# Check what reflog can recover
git reflog -10
```

## Recovery Reference

If something goes wrong:
```bash
# Find the commit you want to return to
git reflog

# Reset to that state
git reset --hard HEAD@{N}
```

**Proceeding with caution...**
