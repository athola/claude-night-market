---
name: block-destructive-git
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: git\s+(reset\s+--hard|checkout\s+--\s+\.|checkout\s+HEAD\s+--|checkout\s+\S+\s+--\s|restore\s+--source|clean\s+-[fd]+|stash\s+drop|branch\s+-D)
---

**Destructive Git Operation Blocked**

This command overwrites or destroys work. Destructive git operations require explicit user approval.

## Blocked Patterns

| Pattern | Risk |
|---------|------|
| `git reset --hard` | Discards all uncommitted changes |
| `git checkout -- .` | Discards all working tree changes |
| `git checkout <branch> -- <path>` | Overwrites files from another branch (can undo intentional deletions) |
| `git restore --source` | Overwrites files from another ref |
| `git clean -fd` | Deletes untracked files permanently |
| `git stash drop` | Destroys stashed changes |
| `git branch -D` | Force-deletes branch without merge check |

## Before Proceeding

```bash
# See what would be affected
git diff HEAD              # Uncommitted changes
git status                 # Summary view
git clean -nfd             # Dry-run for clean
git stash show -p          # Stash contents
```

## To Proceed

Get explicit user approval, then:
1. Edit `.claude/hookify.block-destructive-git.local.md`
2. Set `enabled: false`
3. Run the command
4. Re-enable immediately
