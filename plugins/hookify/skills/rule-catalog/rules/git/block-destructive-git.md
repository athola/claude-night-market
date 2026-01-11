---
name: block-destructive-git
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: git\s+(reset\s+--hard|checkout\s+--\s+\.|checkout\s+HEAD\s+--|clean\s+-[fd]+|stash\s+drop|branch\s+-D|reflog\s+expire|gc\s+--prune)
---

🛑 **Destructive Git Operation Blocked!**

This command can cause **irreversible data loss** - uncommitted changes, local branches, or reflog history may be permanently deleted.

## Detected Patterns

| Command | Risk | What It Destroys |
|---------|------|------------------|
| `git reset --hard` | 🔴 Critical | All uncommitted changes (staged + unstaged) |
| `git checkout -- .` | 🔴 Critical | All unstaged changes in working directory |
| `git checkout HEAD -- <file>` | 🟡 High | Specific file's uncommitted changes |
| `git clean -fd` | 🔴 Critical | All untracked files and directories |
| `git stash drop` | 🟡 High | Stashed changes permanently |
| `git branch -D` | 🟡 High | Force-deletes branch (even unmerged) |
| `git reflog expire` | 🔴 Critical | Recovery points for lost commits |
| `git gc --prune` | 🟡 High | Unreachable objects (can break recovery) |

## Recovery-First Approach

Before discarding changes, **always check what you're about to lose:**

```bash
# See what would be affected by reset --hard
git diff HEAD                    # Unstaged changes
git diff --cached                # Staged changes
git status                       # Overall state

# See what clean would delete
git clean -nfd                   # Dry-run: shows what WOULD be deleted

# See stash contents before dropping
git stash show -p stash@{0}      # Full diff of stash
```

## Safer Alternatives

### Instead of `git reset --hard`
```bash
# Option 1: Save changes to a temporary branch first
git stash                        # Stash current changes
git reset --hard HEAD            # Now safe to reset
# Later: git stash pop           # Recover if needed

# Option 2: Create a backup branch
git checkout -b backup/my-changes
git checkout -                   # Return to original branch
git reset --hard HEAD

# Option 3: Reset specific files only
git checkout HEAD -- path/to/file
```

### Instead of `git checkout -- .`
```bash
# Option 1: Review what you're discarding
git diff                         # See all changes first
git stash                        # Save instead of discard

# Option 2: Discard specific files only
git checkout -- path/to/specific/file
```

### Instead of `git clean -fd`
```bash
# Option 1: See what would be deleted first
git clean -nfd                   # Dry run

# Option 2: Interactive clean (asks per file)
git clean -id

# Option 3: Move to trash instead of delete
mkdir -p .git/trash
git ls-files --others --exclude-standard | xargs -I{} mv {} .git/trash/
```

### Instead of `git stash drop`
```bash
# List all stashes first
git stash list

# Apply the stash to a branch for safekeeping
git stash branch backup-stash stash@{0}
```

## If You Truly Need This Operation

If you've reviewed the changes and confirm they should be discarded:

1. **Verify first**: Run the diagnostic commands above
2. **Temporarily disable** this rule:
   ```bash
   # Edit .claude/hookify.block-destructive-git.local.md
   # Set: enabled: false
   ```
3. **Run your command**
4. **Re-enable** the rule immediately after

## Related Rules

- `block-force-push` - Prevents force pushing to remote
- `warn-large-commits` - Warns about binary files in commits
