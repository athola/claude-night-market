---
description: Stage changes, generate conventional commit message, commit, and push to current branch. One-shot git add-commit-push.
model_hint: fast
---

# Add, Commit, Push

Stage all changes, generate a conventional commit message, commit,
and push to the current branch. One-shot workflow for when changes
are ready to go.

## Steps

1. **Gather context** (run in parallel):
   - `git status -sb`
   - `git diff --stat` (unstaged and staged)
   - `git diff` (full diff for commit message)
   - `git log --oneline -5`
   - `git branch --show-current`
   - `git rev-parse --abbrev-ref @{upstream} 2>/dev/null` (check if tracking remote)

2. **If no changes exist** (nothing staged or unstaged), tell the
   user and stop.

3. **Stage all changes**:
   - `git add` each changed and untracked file by name
   - Do NOT use `git add -A` or `git add .`
   - Do NOT stage `.env`, credentials, or secrets files
   - Do NOT stage `.claude/state/` directory

4. **Draft a conventional commit message** following the same rules
   as `/commit-msg`:
   - Type: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`,
     `style`, `perf`, `ci`
   - Scope: from the changed directory or module
   - Summary: imperative mood, 50 chars max
   - Body: what and why, wrapped at 72 chars
   - No AI attribution, no emojis, no slop

5. **Commit** with the drafted message. Record HEAD first, so step 6
   has something to compare against. Use a HEREDOC:
   ```bash
   before=$(git rev-parse HEAD)
   git commit -m "$(cat <<'EOF'
   <message>
   EOF
   )"
   ```

6. **Verify HEAD advanced** before treating the commit as landed:
   ```bash
   test "$(git rev-parse HEAD)" != "$before" && echo "committed" || echo "ABORTED"
   git status --short
   ```
   An auto-fixing hook (Ruff - Fix, ruff format, prettier,
   trailing-whitespace) rewrites a staged file and aborts the commit.
   Its output tail reads "Passed / Restored changes from patch",
   which is indistinguishable at a glance from a successful run, so
   tailing hook output is not evidence that the commit landed. HEAD
   is. See discussion #614.

7. **If HEAD did not advance**, read the failure rather than retrying
   blind. A `MM` row in `git status --short` means the hook rewrote a
   file you had staged: re-stage the hook-fixed copy (`git add` the
   `MM` paths) and commit again. Any other cause, fix the reported
   issue. Do NOT use `--no-verify`.

8. **Push** to the current branch:
   - If tracking a remote branch: `git push`
   - If no upstream set: `git push -u origin <branch>`

9. **Report** the commit hash, branch, and remote URL.
