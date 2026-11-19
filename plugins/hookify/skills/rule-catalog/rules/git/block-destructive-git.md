---
name: block-destructive-git
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: git\s+(reset\s+--hard|checkout\s+--\s+\.|checkout\s+\.(?=\s|$)|restore\s+\.(?=\s|$)|checkout\s+HEAD\s+--|checkout\s+\S+\s+--\s|restore\s+--source|clean\s+(?:-\w+\s+)*-(?![a-zA-Z]*n)[a-zA-Z]*f|stash\s+drop|branch\s+-D|reflog\s+expire|gc\s+--prune)
---

Uncommitted work represents someone's thinking.
Destroying it erases context that cannot be rebuilt.
(Care)

🛑 **Destructive Git Operation Blocked!**

This command can cause **irreversible data loss** - uncommitted changes, local branches, or reflog history may be permanently deleted.

## Detected Patterns

| Command | Risk | What It Destroys |
|---------|------|------------------|
| `git reset --hard` | 🔴 Critical | All uncommitted changes (staged and unstaged) |
| `git checkout -- .` | 🔴 Critical | All unstaged changes in working directory |
| `git checkout .` | 🔴 Critical | All unstaged changes in working directory |
| `git restore .` | 🔴 Critical | All unstaged changes in working directory |
| `git checkout HEAD -- <file>` | 🟡 High | Specific file's uncommitted changes |
| `git checkout <branch> -- <path>` | 🔴 Critical | Overwrites files from another branch (undoes intentional changes) |
| `git restore --source` | 🟡 High | Overwrites files from another ref |
| `git clean -fd` | 🔴 Critical | All untracked files and directories |
| `git clean -xdf` | 🔴 Critical | Untracked and ignored files, local config included |
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
# Option 1: Stash, which leaves the tree clean with no reset needed
git stash push -u                # Save tracked and untracked changes
# Later: git stash pop           # Recover if needed

# Option 2: Commit the changes to a backup branch
git switch -c backup/my-changes
git add -A && git commit -m "wip: backup before reset"  # Untracked too
git switch -                     # Original branch, clean tree

# Option 3: Discard one file only, named explicitly
git restore --staged --worktree -- path/to/file
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
